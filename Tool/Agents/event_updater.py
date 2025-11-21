"""
@author: Gonghf
@date: 2025/11/20
@description: 
"""
from typing import Optional
import asyncio

import cozepy

from base.api import *


class EventUpdaterAgent:

    def __init__(self):

        self.name = "event_updater"
        self.describe = r"对指定事件背景信息进行整合"
        self.input = r"用户和小酷的历史对话"
        self.status = "未开始"
        self.result = None
        self._task: Optional[asyncio.Task] = None


    async def execute(self, content: str):
        """实际的异步执行任务"""
        try:
            logger.info(f"开始执行 事件背景更新工具输入当前的状态信息为：{content}")
            self.status = f"开始执行 输入的当前状态信息：{content}"

            bot_id = event_updater_agent_id
            user_id = '123456789'

            chat_poll = await asyncio.to_thread(
                coze.chat.create_and_poll,
                bot_id=bot_id,
                user_id=user_id,
                additional_messages=[Message.build_user_question_text(content)]
            )

            self.result = [message.content for message in chat_poll.messages if message.type=='answer'][0]

            self.status = f"执行完成 事件背景更新工具执行的结果为：{self.result}"

        except Exception as e:
            self.status = f"执行错误 事件背景更新出错：{e}"
            self.result = f"未进行事件背景更新"
            logger.error(f"执行错误 事件背景更新工具执行的结果为：{e}")

        return self.result