"""
@author: Gonghf
@date: 2025/11/6
@description: 使用扣子进行网站搜索的agent
"""
from typing import Optional
import asyncio
from base.api import *
from cozepy import Message


class NewsSearchAgent:

    def __init__(self):

        self.name = "news_search"
        self.describe = r"输入1-2个关键词，使用新闻浏览工具进行搜索，并返回2-3段内容的总结作为模型的结果"
        self.input = r"需要搜索的内容"
        self.status = "未开始"
        self.result = None

    def execute(self, content: str):
        """实际的异步执行任务"""
        logger.info(f"开始执行 使用新闻搜索工具搜索内容：{content}")
        self.status = f"开始执行 使用新闻搜索工具搜索内容：{content}"

        bot_id = news_search_agent_id
        user_id = '123456789'

        return coze.chat.stream(
                bot_id=bot_id,
                user_id=user_id,
                additional_messages=[
                    Message.build_user_question_text(content),
                ],
        )

if __name__=="__main__":
    NewsSearchAgent().execute(content="搜一下今天关于美国AI的新闻")

