"""
@author: Gonghf
@date: 2025/11/9
@description: 小酷的后台任务，通过监听定时器状态来控制。
"""

from datetime import datetime, timedelta
from Awareness.awareness_handler import *
from Memory.memory_handler import *
from Awareness.tools.GRS import *
from Tool.Agents.conversation_planner import *
from Scheduler.Ku import XiaoKu


class BackgroundTaskHandler:

    def __init__(self, agent:XiaoKu):

        self.task1_run = True
        self.task2_run = True

        self.agent = agent


    async def write_database(self):

        # 将数据总结之后写入到数据库里面
        try:
            summary, status = await KuFeeling(self.agent.reply).summary_from_message_bank()
            await self.agent.memory.insert_satus_summary(summary=summary, status=status)

        except Exception as e:
            print(f"小酷在插入记忆的时候出错：{e}")

    async def get_plan_system(self):

        current_state = RecommendSystem().get_info()

        try:
            plan = await ConversationPlannerAgent().execute(content=current_state)  # 主要的耗时点

            now = datetime.now()

            current_time = now.strftime('%Y年%m月%d日 %H时')

            weekday_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            weekday_str = weekday_cn[now.weekday()]

            now = f"{current_time} {weekday_str}"

            self.agent.init_system_prompt_with_plan(now, plan)

        except Exception as e:
            print(f"制定主动聊天计划时出错：{e}")
            return None


    async def handler(self, last_response_time):

        if datetime.now() - last_response_time > timedelta(minutes=10) and self.task1_run:

            await self.write_database()

            self.task1_run = False  # 十分钟没有回话 且之前的状态活跃 那么就写一次数据库

        if datetime.now() - last_response_time > timedelta(minutes=30) and self.task2_run:

            await self.get_plan_system()
            await self.agent.chat(message="小酷你好")

            self.task2_run = False  # 三十分钟没有回话 且之前状态活跃 那么就进行一次数据推荐

        if datetime.now() - last_response_time <= timedelta(seconds=60):
            self.task1_run = True
            self.task2_run = True

        return None



