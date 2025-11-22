import asyncio
from typing import Optional
from cozepy import Coze, TokenAuth, Message,COZE_CN_BASE_URL
from base.api import *
# 初始化 Coze 客户端

class AwareAgent:
    def __init__(self):
        self.name = "aware_agent"
        self.describe = r"这是一个获取当前世界信息的智能体"
        self.status = "未开始"
        self.result = None
        self._task: Optional[asyncio.Task] = None

    async def execute(self, content: str):
        """异步执行方法 - 返回一个任务"""
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = asyncio.create_task(self._execute_async(content))
        return self._task

    async def _execute_async(self, content: str):
        """实际的异步执行任务"""
        try:
            logger.info(f"开始执行 获取到用户的画像为：{content}")
            self.status = f"开始执行 获取到用户的画像为：{content}"

            bot_id = awareness_agent_id
            user_id = '123456789'

            # 使用异步方式调用API
            chat_poll = await asyncio.to_thread(
                coze.chat.create_and_poll,
                bot_id=bot_id,
                user_id=user_id,
                additional_messages=[
                    Message.build_user_question_text(content)
                ]
            )

            self.result = [message.content for message in chat_poll.messages if message.type == "answer"][0]
            self.status = f"执行完成 使用世界感知系统获取到的知识：{self.result}"
            logger.info(f"执行完成 使用世界感知系统获取到的知识：{self.result}")
            return

        except Exception as e:
            self.status = f"执行错误 使用世界感知系统获取到的知识工具出错：{e}"
            logger.error(f"执行错误 使用世界感知系统获取到的知识工具出错：{e}")
            self.result = None
            return

if __name__=="__main__":
    asyncio.run(main())









































































































