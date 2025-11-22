"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
import websockets
from Scheduler.Ku import *
from Scheduler.KuBackgroundTask import *
import random



class ChatServer:
    def __init__(self,  reply: MessageBank,tools:ToolManager, feeling:KuFeeling, memory:KuMemory, events:EventBank):

        self.current_client = None  # 只保存当前连接的客户端

        self.reply = reply
        self.tools = tools
        self.feeling = feeling
        self.memory = memory
        self.events = events

        self.agent = XiaoKu(tool=self.tools, reply=self.reply, feeling=self.feeling, memory=self.memory, events=self.events)
        self.background_task = BackgroundTaskHandler(self.agent)

        self.last_remind_time = time.time()
        self.e_conversation_list = []


        # 消息发送器任务
        self.message_sender_task = None
        self.is_running = False

        self._task_lock = asyncio.Lock()


    async def handle_client(self, websocket):
        """处理客户端连接"""
        # 如果有客户端已经连接，拒绝新连接
        if self.current_client is not None:
            logger.error(msg="当前已有客户端进行连接，无法创建新连接。")
            await websocket.close()
            return

        # 设置当前客户端
        self.current_client = websocket
        client_ip = websocket.remote_address[0] if websocket.remote_address else "Unknown"
        logger.info(msg = f"客户端连接: {client_ip}")

        # 发送欢迎消息
        welcome_msg = {
            'type': 'system',
            'message': '你好，我是小酷。请耐心等待小酷初始化ing哦，',
            'timestamp': datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_msg))
        # 启动消息发送器
        self.is_running = True
        asyncio.create_task(self.background_task_monitor(websocket))
        self.message_sender_task = asyncio.create_task(self.send_pending_messages(websocket))

        AA = AwareAgent()
        asyncio.create_task(AA.execute(content=self.agent.system_prompt.user_profile))
        while True:

            if AA.status.startswith("执行完成"):

                self.reply.append(Msg(role="assistant", content="小酷已经初始化结束啦，现在可以聊天了", is_send=False))
                break
            else:
                info = {
                    "type":"echo",
                    "content":"ping",
                    "time":datetime.now().timestamp()
                }

                self.current_client.send(json.dumps(info))

            await asyncio.sleep(10)

        self.agent.system_prompt.current = AA.result

        await self.events.init_from_nl(AA.result)  # 初始化当前事件列表

        self.agent.init_agent()
        # 初始化Agent
        logger.info(msg = f"初始化小酷完成，小酷的世界知识为：{self.agent.system_prompt.current} \n 用户画像为：{self.agent.system_prompt.user_profile}")

        # 处理客户端消息
        async for message in websocket:
            logger.info(msg = f"收到来自 {client_ip} 的消息: {message}")
            self.last_remind_time = time.time()

            await self.agent.chat(message)

    async def background_task_monitor(self, websocket):
        """后台事件监视器"""
        logger.info(msg="启动后台事件监视器")


        while self.is_running and self.current_client == websocket:
            try:

                current_time = time.time()  # 获取当前时间戳

                if current_time - self.last_remind_time < 120:  # 60内是否有用户的消息

                    async with self._task_lock:
                        logger.debug("执行后台任务")
                        await self.background_task.handler()
                else:
                    logger.debug("未达到执行间隔，跳过本次执行")

            except Exception as e:
                logger.error(msg=f"后台任务执行失败：{e}")
                # 可以选择添加重试逻辑或错误恢复

            # 等待下一次检查
            await asyncio.sleep(60)


    async def send_pending_messages(self, websocket):
        """发送待处理消息"""
        logger.info("启动消息发送器")

        while self.is_running and self.current_client == websocket:
            try:
                    # 发送所有消息
                while len(self.reply.message_list_dict["not_send"]) != 0:

                    message = self.reply.send()
                    self.e_conversation_list.append(message)

                    content = message.content

                    info = {
                        "type": message.role,
                        "message": content,
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(info))
                    # 清空消息列表，避免重复发送
                    await asyncio.sleep(random.uniform(1, 3))
                    logger.info(f"已发送消息: {message.content}")

                # 短暂休眠，避免过度占用CPU
                await asyncio.sleep(0.1)

            except websockets.exceptions.ConnectionClosed:
                logger.error("客户端已断开，停止消息发送")
                break
            except Exception as e:
                logger.error(f"消息发送器错误: {e}")
                await asyncio.sleep(1)

    async def start_server(self):
        """启动WebSocket服务器"""
        logger.info(f"启动WebSocket聊天服务器在 {host}:{port}")
        logger.info("按 Ctrl+C 停止服务器")

        try:
            # 使用新的API，不需要path参数
            async with websockets.serve(self.handle_client, host, port,ping_interval=20,  ping_timeout=60, close_timeout=10):
                await asyncio.Future()  # 永久运行
        except KeyboardInterrupt:
            print("\n服务器正在关闭...")
            self.is_running = False



async def main():

    reply = MessageBank()
    tools = ToolManager()
    memory = KuMemory()
    feeling = KuFeeling(reply=reply)
    events = EventBank()

    server = ChatServer(reply,tools, feeling, memory, events)
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())