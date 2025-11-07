"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
import asyncio
import websockets
import json

from Scheduler import *
from Tool.manager import *
from Memory.memory_handler import *
from Scheduler.Ku import *
from Awareness.awareness_handler import *
from base.config import *
from datetime import datetime, timedelta



class ChatServer:
    def __init__(self,  reply: MessageBank,tools:ToolManager, feeling:KuFeeling, memory:KuMemory):

        self.current_client = None  # 只保存当前连接的客户端

        self.reply = reply
        self.tools = tools
        self.feeling = feeling
        self.memory = memory


        # 消息发送器任务
        self.message_sender_task = None
        self.is_running = False
        self.reminder_task = None

        self.last_user_activity = None
        self.reminder_sent = False

    async def handle_client(self, websocket):
        """处理客户端连接"""
        # 如果有客户端已经连接，拒绝新连接
        if self.current_client is not None:
            print("已有客户端连接，拒绝新连接")
            await websocket.close()
            return

        # 设置当前客户端
        self.current_client = websocket
        client_ip = websocket.remote_address[0] if websocket.remote_address else "Unknown"
        print(f"客户端连接: {client_ip}")

        agent = XiaoKu(tool=self.tools, reply=self.reply, feeling=self.feeling)


        # 发送欢迎消息
        welcome_msg = {
            'type': 'system',
            'message': '你好，我是小酷。我是你的小助手，',
            'timestamp': datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_msg))

        agent.init_agent()  # 初始化Agent

        print("小酷已经初始化完成")

        self.last_user_activity = datetime.now()
        self.reminder_sent = False

        # 启动消息发送器
        self.is_running = True
        self.message_sender_task = asyncio.create_task(self.send_pending_messages(websocket))
        self.reminder_task = asyncio.create_task(self.monitor_user_activity(websocket))

        # 处理客户端消息
        async for message in websocket:
            print(f"收到来自 {client_ip} 的消息: {message}")

            self.last_user_activity = datetime.now()
            self.reminder_sent = False  # 重置提醒标记

            # 处理用户消息并获取响应
            await agent.chat(message=message)


        # finally:
        #     # 停止消息发送器
        #     self.is_running = False
        #     if self.message_sender_task:
        #         self.message_sender_task.cancel()
        #         try:
        #             await self.message_sender_task
        #         except asyncio.CancelledError:
        #             pass
        #         self.message_sender_task = None
        #
        #     # 清除当前客户端
        #     if self.current_client == websocket:
        #         self.current_client = None
        #     print(f"客户端 {client_ip} 已移除")

    async def monitor_user_activity(self, websocket):
        """监控用户活动状态，发送提醒消息"""
        print("启动用户活动监控")

        while self.is_running and self.current_client == websocket:
            try:
                # 检查用户是否超过1分钟没有活动
                if (self.last_user_activity and
                        datetime.now() - self.last_user_activity > timedelta(seconds=30) and
                        not self.reminder_sent):

                    # 发送提醒消息
                    summaries = await self.feeling.summary_from_message_bank(self.memory)
                    print(summaries)


                    # 标记已发送提醒
                    self.reminder_sent = True

                    # 记录提醒发送时间
                    reminder_time = datetime.now()

                    # 等待用户响应，如果再过1分钟仍无响应则不再处理
                    while (self.is_running and
                           self.current_client == websocket and
                           datetime.now() - reminder_time < timedelta(minutes=1) and
                           not self.last_user_activity > reminder_time):
                        await asyncio.sleep(5)  # 每5秒检查一次

                    # 如果用户仍然没有响应，重置状态等待下一次可能的连接
                    if (self.last_user_activity <= reminder_time and
                            self.current_client == websocket):
                        print("用户长时间未响应，停止发送提醒")

                # 短暂休眠，避免过度占用CPU
                await asyncio.sleep(5)  # 每5秒检查一次用户活动

            except websockets.exceptions.ConnectionClosed:
                print("客户端已断开，停止活动监控")
                break
            except Exception as e:
                print(f"活动监控错误: {e}")
                await asyncio.sleep(5)

    async def send_pending_messages(self, websocket):
        """发送待处理消息"""
        print("启动消息发送器")

        while self.is_running and self.current_client == websocket:


            try:
                    # 发送所有消息
                while len(self.reply.message_list_dict["not_send"]) != 0:

                    message = self.reply.send()

                    content = message.content

                    info = {
                        "type": "echo",
                        "message": content,
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(info))
                    # 清空消息列表，避免重复发送
                    await asyncio.sleep(random.uniform(1, 3))
                    print(f"已发送消息: {message.content}")

                # 短暂休眠，避免过度占用CPU
                await asyncio.sleep(0.1)

            except websockets.exceptions.ConnectionClosed:
                print("客户端已断开，停止消息发送")
                break
            except Exception as e:
                print(f"消息发送器错误: {e}")
                await asyncio.sleep(1)

    async def start_server(self):
        """启动WebSocket服务器"""
        print(f"启动WebSocket聊天服务器在 {host}:{port}")
        print("按 Ctrl+C 停止服务器")

        try:
            # 使用新的API，不需要path参数
            async with websockets.serve(self.handle_client, host, port):
                await asyncio.Future()  # 永久运行
        except KeyboardInterrupt:
            print("\n服务器正在关闭...")
            self.is_running = False



async def main():

    reply = MessageBank()
    tools = ToolManager()
    memory = KuMemory()
    feeling = KuFeeling(messages=reply)


    server = ChatServer(reply,tools, feeling, memory)
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())