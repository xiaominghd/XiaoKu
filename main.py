import asyncio
import json
import time
from datetime import datetime
import websockets
from collections import deque
import logging
from Agents.awareness import *
from Ku import *
from base.api import *
from BackGroundTask.conversation_guidance_manager import *


class ChatServer:
    def __init__(self, reply: MessageBank, events: EventBank, memory: MemoryBank):
        self.current_client = None
        self.reply = reply
        self.events = events
        self.memory = memory
        self.agent = XiaoKu(reply=self.reply, events=self.events, memory=self.memory)
        self.last_remind_time = time.time()

        # 消息缓冲队列
        self.message_buffer = deque(maxlen=50)  # 用户消息缓存队列
        self.buffer_timer_task = None
        self.buffer_timer_duration = 3  # 缓冲等待时间（秒）

        # 消息发送器任务
        self.message_sender_task = None
        self.is_running = False

        self.task_lock = asyncio.Lock()

    async def handle_client(self, websocket):
        """处理客户端连接"""
        # 如果有客户端已经连接，拒绝新连接
        if self.current_client is not None:
            logger.error("当前已有客户端进行连接，无法创建新连接。")
            await websocket.close()
            return

        # 设置当前客户端
        self.current_client = websocket
        client_ip = websocket.remote_address[0] if websocket.remote_address else "Unknown"
        logger.info(f"客户端连接: {client_ip}")

        # 发送欢迎消息
        welcome_msg = {
            'type': 'system',
            'message': '你好，我是小酷。请耐心等待小酷初始化ing哦，',
            'timestamp': datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_msg))

        self.is_running = True
        self.message_sender_task = asyncio.create_task(self.send_pending_messages(websocket))
        asyncio.create_task(self.background_task_monitor(websocket))
        # 初始化事件
        event_bank = await AwareAgentWork().get_info()
        self.agent.events = event_bank

        logger.info("初始化小酷完成")
        self.agent.reply.not_send.append(
            SingleContext(
                create_time=datetime.now(),
                role="assistant",
                content="初始化小酷完成"
            )
        )

        try:
            # 处理客户端消息
            async for message in websocket:
                logger.info(f"收到来自 {client_ip} 的消息: {message}")
                self.last_remind_time = time.time()

                # 将消息添加到缓冲区
                await self.add_message_to_buffer(message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端 {client_ip} 连接已关闭")
        except Exception as e:
            logger.error(f"处理客户端消息时发生错误: {e}")
        finally:
            # 确保清理工作一定会执行
            await self.cleanup_client()

    async def add_message_to_buffer(self, message: str):
        """将消息添加到缓冲区"""
        # 将消息添加到缓冲区
        self.message_buffer.append(message)
        logger.debug(f"消息已添加到缓冲区，当前缓冲区大小: {len(self.message_buffer)}")

        # 如果有正在处理的计时器任务，取消它（因为我们有新的消息）
        if self.buffer_timer_task and not self.buffer_timer_task.done():
            self.buffer_timer_task.cancel()

        # 启动新的缓冲计时器
        self.buffer_timer_task = asyncio.create_task(self.process_buffer_with_delay())

    async def process_buffer_with_delay(self):
        """延迟处理缓冲区中的消息"""
        try:
            # 等待一段时间，看看用户是否继续输入
            await asyncio.sleep(self.buffer_timer_duration)

            # 开始处理缓冲区
            await self.process_message_buffer()

        except asyncio.CancelledError:
            logger.debug("缓冲计时器被取消（用户继续输入）")
        except Exception as e:
            logger.error(f"处理缓冲区消息时出错: {e}")

    async def process_message_buffer(self):
        """处理缓冲区中的所有消息"""
        if len(self.message_buffer) == 0:
            return

        try:
            # 获取缓冲区中的所有消息
            messages_to_process = list(self.message_buffer)
            self.message_buffer.clear()

            logger.info(f"开始处理缓冲区的 {len(messages_to_process)} 条消息")

            # 如果有多条消息，合并处理
            if len(messages_to_process) == 1:
                # 单条消息直接处理
                await self.agent.chat(messages_to_process[0])
            else:
                # 多条消息合并处理
                combined_message = "\n".join(messages_to_process)
                await self.agent.chat(combined_message)
                logger.info(f"已合并处理 {len(messages_to_process)} 条消息")

        except Exception as e:
            logger.error(f"处理消息缓冲区时发生错误: {e}")

    async def cleanup_client(self):
        """清理客户端连接"""
        try:
            # 处理缓冲区中剩余的消息
            if len(self.message_buffer) > 0:
                logger.info("处理剩余缓冲区消息")
                await self.process_message_buffer()

            logger.info("开始进行数据入库")
            self.agent.clear()
        except Exception as e:
            logger.error(f"执行agent.clear()时发生错误: {e}")
        finally:
            # 停止后台任务
            self.is_running = False

            # 取消任务
            if self.message_sender_task and not self.message_sender_task.done():
                self.message_sender_task.cancel()

            if self.buffer_timer_task and not self.buffer_timer_task.done():
                self.buffer_timer_task.cancel()

            # 清理缓冲区
            self.message_buffer.clear()

            # 清理当前客户端
            self.current_client = None
            logger.info("客户端清理完成")

    async def send_pending_messages(self, websocket):
        """发送待处理消息"""
        logger.info("启动消息发送器")

        while self.is_running and self.current_client == websocket:
            try:
                # 发送所有消息
                while len(self.reply.not_send) != 0:
                    message = self.reply.send()
                    await asyncio.sleep(0.1 * len(message.content))

                    # 直接发送完整消息
                    info = {
                        "type": message.role,
                        "message": message.content,
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(info))
                    # 消息之间的间隔

                    logger.info(f"已发送消息: {message.content[:50]}...")

                # 短暂休眠，避免过度占用CPU
                await asyncio.sleep(0.1)

            except websockets.exceptions.ConnectionClosed:
                logger.error("客户端已断开，停止消息发送")
                break
            except Exception as e:
                logger.error(f"消息发送器错误: {e}")
                await asyncio.sleep(1)

    async def background_task_monitor(self, websocket):
        """后台事件监视器"""
        logger.info("启动后台事件监视器")

        while self.is_running and self.current_client == websocket:

            async with self.task_lock:

                await get_conversation_guidance(self.agent)
                logger.info("开始执行对话指引任务")

            await asyncio.sleep(20)
        #
        #
        #
        # while self.is_running and self.current_client == websocket:
        #     try:
        #         current_time = time.time()
        #
        #         # 检查是否需要发送提醒
        #         if current_time - self.last_remind_time > 30 and self.agent.events.current_event is not None:
        #             logger.info("发送提醒消息")
        #             await self.agent.chat(message="")
        #             self.last_remind_time = current_time
        #
        #     except Exception as e:
        #         logger.error(f"后台任务执行失败：{e}")
        #
        #     # 等待下一次检查
        #     await asyncio.sleep(5)

    async def start_server(self):
        """启动WebSocket服务器"""
        host = "0.0.0.0"  # 应该从配置读取
        port = 8765  # 应该从配置读取

        logger.info(f"启动WebSocket聊天服务器在 {host}:{port}")
        logger.info("按 Ctrl+C 停止服务器")

        try:
            async with websockets.serve(
                    self.handle_client,
                    host,
                    port,
                    ping_interval=20,
                    ping_timeout=60,
                    close_timeout=10
            ):
                await asyncio.Future()  # 永久运行
        except KeyboardInterrupt:
            print("\n服务器正在关闭...")
            self.is_running = False
            # 如果还有连接的客户端，也执行清理
            if self.current_client:
                await self.cleanup_client()
        except Exception as e:
            logger.error(f"服务器发生错误: {e}")
        finally:
            logger.info("服务器已关闭")

async def main():

    reply = MessageBank()
    memory = MemoryBank()
    events = EventBank()

    server = ChatServer(reply, events, memory)
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())