"""
@author: Gonghf
@date: 2025/11/6
@description: 使用扣子进行网站搜索的agent
"""
from typing import Optional
import asyncio
from base.api import *

class NewsSearchAgent:

    def __init__(self):

        self.name = "news_search"
        self.describe = r"输入需要搜索的内容，使用新闻浏览工具进行搜索，并返回搜索结果总结"
        self.input = r"需要搜索的内容"
        self.status = "未开始"
        self.result = None
        self._task: Optional[asyncio.Task] = None

    async def execute(self, content: str):
        """异步执行方法 - 立即返回，不阻塞"""
        # 如果已有任务在执行，先取消它
        if self._task and not self._task.done():
            self._task.cancel()

        # 创建新的异步任务
        self._task = asyncio.create_task(self._execute_async(content))
        return self._task

    async def _execute_async(self, content: str):
        """实际的异步执行任务"""
        try:
            print(f"开始执行 使用新闻搜索工具搜索内容：{content}")
            self.status = f"开始执行 使用新闻搜索工具搜索内容：{content}"

            bot_id = news_search_agent_id
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
            self.status = f"执行完成 使用新闻搜索工具搜索结果为：{self.result}"
            print(f"执行完成 使用新闻搜索工具搜索结果为：{self.result}")

        except Exception as e:
            self.status = f"执行错误 调用新闻搜索工具出错：{e}"
            self.result = f"哎呀小酷在调用新闻搜搜工具时候出错了呢，主人可以帮忙核实一下这个错误吗：{e}"

