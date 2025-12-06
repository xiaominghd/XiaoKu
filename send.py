import asyncio
import websockets
import json
import sys


class ChatClient:
    def __init__(self, server_url='ws://localhost:8765'):
        self.server_url = server_url
        self.websocket = None

    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            print(f"已连接到服务器 {self.server_url}")
            print("输入消息发送到服务器 (输入 'quit' 退出)")

            # 启动消息接收任务
            receive_task = asyncio.create_task(self.receive_messages())

            # 处理用户输入
            await self.handle_user_input()

            # 等待接收任务完成
            await receive_task

        except Exception as e:
            print(f"连接错误: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()

    async def handle_user_input(self):
        """处理用户输入"""
        try:
            while True:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, input, "你: "
                )

                if message.lower() in ['quit', 'exit', '退出']:
                    print("断开连接...")
                    break

                if message.strip():
                    await self.websocket.send(message)

        except KeyboardInterrupt:
            print("\n断开连接...")

    async def receive_messages(self):
        """接收服务器消息"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                if data["type"] == "echo":
                    print("收到心跳消息")
                    continue
                print(f"\n[小酷] {data['message']}")
                # 重新显示输入提示
                print("你: ", end='', flush=True)

        except websockets.exceptions.ConnectionClosed:
            print("\n连接已断开")
        except Exception as e:
            print(f"\n接收消息错误: {e}")


async def main():
    # 允许用户指定服务器地址
    server_url = 'ws://localhost:8765'
    if len(sys.argv) > 1:
        server_url = sys.argv[1]

    client = ChatClient(server_url)
    await client.connect()


if __name__ == "__main__":
    asyncio.run(main())