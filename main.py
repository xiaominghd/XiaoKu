"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
import websockets
from Scheduler.Ku import *
from Scheduler.KuBackgroundTask import *



class ChatServer:
    def __init__(self,  reply: MessageBank,tools:ToolManager, feeling:KuFeeling, memory:KuMemory):

        self.current_client = None  # 只保存当前连接的客户端

        self.reply = reply
        self.tools = tools
        self.feeling = feeling
        self.memory = memory

        self.agent = XiaoKu(tool=self.tools, reply=self.reply, feeling=self.feeling, memory=self.memory)
        self.background_task = BackgroundTaskHandler(self.agent)

        self.last_remind_time = datetime.now()


        # 消息发送器任务
        self.message_sender_task = None
        self.is_running = False

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

        # 发送欢迎消息
        welcome_msg = {
            'type': 'system',
            'message': '你好，我是小酷。我是你的小助手，',
            'timestamp': datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_msg))

        plan_task = asyncio.create_task(self.background_task.get_plan_system())
        # 初始化Agent
        print("初始化已经完成")

        # 启动消息发送器
        self.is_running = True
        asyncio.create_task(self.background_task_monitor(websocket))
        self.message_sender_task = asyncio.create_task(self.send_pending_messages(websocket))

        # 处理客户端消息
        async for message in websocket:
            print(f"收到来自 {client_ip} 的消息: {message}")
            self.last_remind_time = datetime.now()
            # 处理用户消息并获取响应
            await self.agent.chat(message=message)

    async def background_task_monitor(self, websocket):

        print("启动后台事件监视器")
        while self.is_running and self.current_client == websocket:

            try:

                await self.background_task.handler(self.last_remind_time)

            except Exception as e:
                print(f"启动后台监视器失败：{e}")

            await asyncio.sleep(delay=10)


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
            async with websockets.serve(self.handle_client, host, port,ping_interval=20,  ping_timeout=60, close_timeout=10):
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