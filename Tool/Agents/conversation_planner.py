"""
@author: Gonghf
@date: 2025/11/9
@description: 
"""
from typing import Optional
import asyncio

import cozepy

from base.api import *


class ConversationPlannerAgent:

    def __init__(self):

        self.name = "conversation_planner"
        self.describe = r"输入当前状态和历史信息，给小酷推荐聊天话题"
        self.input = r"用户当前的状态和历史信息"
        self.status = "未开始"
        self.result = None
        self._task: Optional[asyncio.Task] = None


    async def execute(self, content: str):
        """实际的异步执行任务"""
        try:
            logger.info(f"开始执行 聊天规划工具输入当前的状态信息为：{content}")
            self.status = f"开始执行 输入的当前状态信息：{content}"

            bot_id = conversation_planner_agent_id
            user_id = '123456789'

            chat_poll = await asyncio.to_thread(
                coze.chat.create_and_poll,
                bot_id=bot_id,
                user_id=user_id,
                additional_messages=[Message.build_user_question_text(content)]
            )

            self.result = [message.content for message in chat_poll.messages if message.type=='answer'][0]

            self.status = f"执行完成 聊天规划工具执行的结果为：{self.result}"

        except Exception as e:
            self.status = f"执行错误 生成对话规划出错：{e}"
            self.result = f"未生成聊天计划，按照正常顺序进行聊天"
            logger.error(f"执行错误 聊天规划工具执行的结果为：{e}")

        return self.result

async def main():

    planner = ConversationPlannerAgent()
    content = r"""现在是2025年11月08日 星期六 20时
当前状态：2025年11月08日 20时 周六 状态： 主人心情不错
时间：2025年11月04日 15时 周二 事件：主人今天心情不错，询问小酷是否愿意分享今日趣事，随后表达了想了解股市行情的愿望。小酷回应说今日股市整体下跌，但大盘股的表现优于小盘股。得知此消息后，主人感到有些失落，希望转换话题。 状态：主人今天心情不错时间
2025年11月06日 17时 周四 事件：主人和小酷分享了晚餐的喜悦，主人吃了黄焖鸡并计划下次加入金针菇和土豆。最后，主人表示希望换个话题。 状态：主人今天心情不错
2025年11月07日 21时 周五 事件：主人试玩一下崩坏星穹铁道这个游戏，向小酷表示这个游戏奖励越来越多了。 状态：主人今天心情不错
2025年11月08日 16时 周六 事件：主人跟小酷说感冒了不想聊天 状态：主人今天心情不好
"""
    print("开始执行任务")
    result = await planner.execute(content)
    print(result)

if __name__=="__main__":
    asyncio.run(main())



