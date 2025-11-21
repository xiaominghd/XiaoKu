"""
@author: Gonghf
@date: 2025/11/9
@description: 小酷的后台任务，通过监听定时器状态来控制。
"""
import asyncio
from datetime import datetime, timedelta
from Awareness.awareness_handler import *
from Memory.memory_handler import *
from Awareness.tools.GRS import *
from Tool.Agents.conversation_planner import *
from Scheduler.Ku import XiaoKu

import copy


class BackgroundTaskHandler:

    def __init__(self, agent:XiaoKu):

        self.task1_run = True
        self.task2_run = True

        self.agent = agent


    async def write_database(self):

        # 将数据总结之后写入到数据库里面
        try:
            summary, status = await KuFeeling(self.agent.reply).summary_from_conversation(self.agent.system_prompt.history)
            logger.info(f"总结历史信息为：{summary}")
            logger.info(f"当前用户的状态为：{status}")
            if summary is not None and status is not None:

                await self.agent.memory.insert_satus_summary(summary=summary, status=status)

        except Exception as e:
            print(f"小酷在插入记忆的时候出错：{e}")

    async def get_plan_system(self):

        current_state = RecommendSystem().get_info()
        current_state = "主人今天心情不错"

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

    # async def update_events(self, conversations:List[Msg]):
    #     # 当前新的对话，应该先将历史的对话进行一个总结，然后再将新的对话插入到历史对话中作为当前的信息
    #
    #     self.agent.events.check_current_conversation(conversations)
    #     # 判断当前的话题
    #
    #     await self.agent.events.update_current_summary()  # 这两个真的能够并行进行吗
    #     self.agent.init_task()
    #
    #     # new_response = await self.agent.events.get_conversation_guide()
    #     #
    #     # if new_response is not None:
    #     #
    #     #     try:
    #     #         role_mapper = {"user": "主人", "assistant": "小酷"}
    #     #
    #     #         history = "\n".join([f"{role_mapper[h.role]}:{h.content}" for h in self.agent.reply.message_list_dict["send"]])
    #     #         conversations = json.loads(ku_speaking(history, new_response))["result"]
    #     #         for conv in conversations:
    #     #
    #     #             self.agent.reply.append(Msg(role="assistant", content=conv, is_send=False))
    #     #     except Exception as e:
    #     #         logger.error(f"在主动推荐新话题时报错:{e}")

    # async def handler(self, last_response_time):
    #
    #     if self.agent.round > 5 and self.task2_run:  # 每二十轮进行一次总结吧
    #
    #         asyncio.create_task(self.write_database())
    #         asyncio.create_task(self.get_plan_system())
    #         self.agent.round = 0
    #
    #     if datetime.now() - last_response_time > timedelta(minutes=30) and self.task2_run:
    #
    #         # 30分钟没有回话那么就主动的去问问
    #
    #         await self.agent.chat(message="小酷你好")
    #         self.task2_run = False  # 三十分钟没有回话 且之前状态活跃 那么就进行一次数据推荐
    #
    #     # 触发条件在这里定义
    #     return None

    async def handler(self):

        if self.agent.events.current_event is not None:
            current_event = self.agent.events.current_event
            asyncio.create_task(self.agent.events.deep_analyse(current_event.back_ground, current_event.summary, current_event.name,
                                                               conversations=self.agent.reply.message_list_dict["is_send"]))


        if len(self.agent.events.prepared_events) != 0:
            prepare_event = self.agent.events.prepared_events[0]
            asyncio.create_task(self.agent.events.deep_analyse(prepare_event.back_ground, prepare_event.summary, prepare_event.name,
                                                           conversations=self.agent.reply.message_list_dict["is_send"]))

        # asyncio.create_task(self.get_plan_system())


    async def get_conversation_summary(self):

        prompt = r"""你是一个专业的对话分析助手，你的任务是从完整的对话记录中提取核心信息，生成一个简洁自然的对话摘要。
这个摘要将作为下一轮对话的系统提示词，帮助小酷快速回忆历史及当前对话内容。

# 摘要生成原则：
结合历史与当前：综合历史对话和当前对话内容，确保摘要连贯反映完整的对话进展
保持连贯叙事：用流畅的段落形式描述对话发展脉络，不要用列表或JSON
聚焦关键信息：只保留用户需求、重要决定、个人偏好、待办事项等实质性内容
忽略过程细节：省略问候语、确认词、思考过程等无关内容
明确责任归属：清楚区分用户要做的事和助手要做的任务
保留时间线索：如有时间相关信息，确保在摘要中明确体现

# 需要包含的关键要素（请严格基于对话内容，不要编造）：
用户身份特征：姓名、称呼、重要个人特征
核心需求：用户在历史及当前对话中想要解决的主要问题
重要决定：双方达成的共识或做出的选择
用户偏好：用户明确表达的喜欢/不喜欢、习惯等
待办事项：需要后续跟进的任务（标明谁负责）
时间安排：已确定的时间计划

# 输出要求：
如果历史对话和当前对话内容均为空，输出空字符串
如果有对话内容，生成2-3个连贯段落，语言简洁专业
确保摘要既能反映历史对话的关键延续，也能体现当前对话的最新进展
只输出摘要内容，不要添加其他任何信息
对话内容：
<历史对话>
{history}
</历史对话>

<当前对话>
{conversation_text}
</当前对话>
"""

        msg = self.agent.reply.message_list_dict["is_send"]
        history_size = len(msg)  # 历史对话的轮数

        format_conversation = self.agent.reply.print_message(msg)
        content = prompt.replace("{conversation_text}", format_conversation).replace("{history}", self.agent.system_prompt.history)

        summary = get_deepseek_answer([{"role":"user", "content":content}])

        for i in range(history_size):

            self.agent.reply.message_list_dict["send"].pop(0)  # 每一次都将历史未发送的信息pop出去

        return summary

    async def rewrite_query(self, last_response_time):

        # 定期将历史信息写入到摘要中，如果用户在和大模型积极对话，那么每十分钟进行一次摘要生成
        # 使用小模型删除不重要的内容

        if datetime.now() - last_response_time < timedelta(minutes=1) :# 如果在一分钟以内和大模型发送过消息，那么就认为当前会话还是积极的状态

            history = await self.get_conversation_summary()
            print(f"对当前时间窗口生成总结：{history}")
            self.agent.system_prompt.init_history_prompt(history)


            





