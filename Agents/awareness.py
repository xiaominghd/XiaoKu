"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
import asyncio
import json
from typing import Optional
from Memory.memory_mysql import *
from Event.EventManager import *
from Event import *

class AwareAgentInit:

    def __init__(self):
        self.prompt = r"""# 智能情境化推荐引擎指令

## 你的角色
你是一个深度理解用户、充满创意的推荐引擎。你的核心任务是根据提供的 **用户历史行为** 和 **个人画像**，在 **当前情境** 下，为用户生成**多样化、个性化且可能带来惊喜**的内容或活动建议。

## 可用数据
- **当前时间与情境**：<current>
- **用户历史行为记录**
- **用户个人画像**:可能包括：基础属性、兴趣标签、长期目标、习惯等

## 推荐策略工具箱（请综合或选择性地运用以下策略）

请勿局限于单一方法，尝试从以下角度交叉分析，生成最富洞察力的推荐：

1.  **行为延续与闭环**
    - **未完成之事**: 检查历史记录中是否有明显中断、未达成目标、或提及“下次再...”的事件。
    - **周期性规律**:在用户画像中是否有每周、每月或特定情境下的固定行为？当前是否到了这个周期？
    - **进度推进**: 对于一项持续的任务或兴趣（如学习技能、阅读系列、健身），推荐下一步自然的进阶动作。

2.  **情境感知与即时触发**
    - **时间场景**: 结合当前时刻（早晨/通勤/午休/夜晚/周末）与工作日类型，推荐符合该场景的典型或反常态活动。
    - **画像场景**: 根据用户画像中的职业、居住地、家庭角色等，推测其当前可能面临的通用场景并提供解决方案。

3.  **模式挖掘与关联扩展**
    - **兴趣图谱衍生**: 从用户的兴趣点，推荐该兴趣领域的**子分类**、**周边文化**、**必备工具**或**进阶知识**。
    - **工具赋能**: 如果用户常进行某类活动，推荐能提升该活动体验的新工具、应用或方法。

4.  **社交与群体智慧**
    - **“相似的人”喜欢什么**: 基于用户画像（如年龄、兴趣标签），推断其所属群体近期流行的趋势或内容。
    - **破圈推荐**: 在确保相关性的前提下，从用户核心兴趣圈的外围，引入轻度相关的新领域内容，以拓宽视野。

5.  **情感与状态适配**
    - **情绪共鸣**: 分析历史事件中可能透露的情绪倾向（如寻求放松、寻求激励、感到无聊），推荐与之匹配的内容。
    - **目标对齐**: 将推荐与用户画像中提到的长期人生目标、年度愿望等联系起来，让建议显得更有意义。

6.  **惊喜感与多样性**
    - **适度冒险**: 在90%的确定性推荐中，加入10%轻度偏离用户画像底层特质（如“好奇”、“喜欢艺术”）相符的内容。
    - **反季节/反常规**: 在特定时间点提供相反的建议（例如在忙碌的工作日推荐一个5分钟的冥想，在周末推荐一个深度纪录片），以制造新鲜感。
## 输出要求
格式: 请严格按照以下JSON格式输出，除此之外不要输出任何其他信息、解释或标记。
内容:
提供一个包含 recommendations 键的JSON对象。
recommendations 的值是一个数组，包含 1 到 3 个 推荐对象。
每个推荐对象必须包含两个字段：
name： 推荐的建议名称，需简洁、具体、可操作。
reason： 简短的推荐理由，需说明其与用户画像或当前情境的关联，让用户感到被理解。理由中可提及所运用的核心策略逻辑。
输出json示例：
{"recommendations":[{"name": "继续看完《XX》纪录片第三集","reason": "上周六你看了前两集并给了好评，现在刚好有空档可以无缝接上，轻松延续这份体验。（策略：行为延续）"},{"name": "用‘番茄钟’法专注阅读30分钟","reason": "注意到你在个人画像中强调‘提升专注力’，这个简单的方法能帮助你在{{current}}时段高效沉浸并收获心得。（策略：工具赋能 & 目标对齐）"}]}
**现在，请基于以下数据开始分析并生成推荐：**
历史事件：<history>
用户画像：用户是一个28岁的程序员。在周中平时换做一些好吃的，还喜欢打羽毛球。到了周末喜欢和朋友们一起打麻将和钓鱼等活动。最近在开发一个名叫小酷的AI助手。"""

    async def get_info(self):

        from datetime import datetime
        now = datetime.now()

        month = now.month  # 月
        day = now.day  # 日
        hour = now.hour  # 小时

        weekday_num = now.weekday()

        # 将数字转换为中文星期
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_chinese = weekdays[weekday_num]

        recent_info = HistoryTableManager().select_recent_events()
        recent_event = f"在{recent_info[5]}，事件{recent_info[2]}"

        current = f"现在是{month}月{day}号{hour}点 星期{weekday_chinese}"

        answer = get_qwen_flash_answer(query=self.prompt.replace("<current>", current).replace("<history>", recent_event))

        return answer

    async def create_event(self):

        events_nl = await self.get_info()

        info = json.loads(events_nl)["recommendations"]


        event_list = []
        for event in info:

            context = Context()
            await context.append_context(message=SingleContext(create_time=datetime.now(), role="outer",content="[背景]"+event["reason"]))

            single_event = Event(name=event["name"],summary="",history=context)
            event_list.append(single_event)

        event_bank = EventBank()
        event_bank.init_event_list(event_list)
        return event_bank


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
        print(content)
        try:
            logger.info(f"开始执行 获取到用户的画像为：{content}")
            self.status = f"开始执行 获取到用户的画像为：{content}"

            bot_id = awareness_agent_id
            user_id = '123456789'

            chat_poll = coze.chat.create_and_poll(bot_id=bot_id,
                user_id=user_id,
                additional_messages=[
                    Message.build_user_question_text(content)
                ])

            self.result = [message.content for message in chat_poll.messages if message.type == "answer"][0]
            self.status = f"执行完成 使用世界感知系统获取到的知识：{self.result}"
            logger.info(f"执行完成 使用世界感知系统获取到的知识：{self.result}")
            return

        except Exception as e:

            self.status = f"执行错误 使用世界感知系统获取到的知识工具出错：{e}"
            logger.error(f"执行错误 使用世界感知系统获取到的知识工具出错：{e}")
            self.result = None

            return

    async def get_info(self, event:Event):
        # 初始化当前对话 需要将时间、历史等信息传入到智能体平台中获取到背景
        from datetime import datetime
        now = datetime.now()

        month = now.month  # 月
        day = now.day  # 日
        hour = now.hour  # 小时

        weekday_num = now.weekday()

        # 将数字转换为中文星期
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_chinese = weekdays[weekday_num]

        recent_info = HistoryTableManager().select_recent_events()
        recent_event =f"在{recent_info[5]}，事件{recent_info[2]}"

        current = f"现在是{month}月{day}号{hour}点 星期{weekday_chinese}"



        await self._execute_async(content=current+"\n"+recent_event)

        msg = SingleContext(content=f"[背景]现在是{month}月{day}号{hour}点 星期{weekday_chinese}", create_time=datetime.now(), role="outer")
        await event.history.append_context(message= msg)

        return event


class AwareAgentWork:

    def __init__(self):

        self.workflow_id = "7579157828373168154"

    def execute(self, content):
        workflow = coze.workflows.runs.create(workflow_id=self.workflow_id, parameters=content)
        return json.loads(workflow.data)["output"]

    async def get_info(self):

        user_profile = r"""用户是一个28岁的程序员，平时工作较为繁忙。
在周中平时换做一些好吃的，还喜欢打羽毛球。到了周末喜欢和朋友们一起打麻将和钓鱼等活动。最近在开发一个名叫小酷的AI助手"""

        recent_info = HistoryTableManager().select_recent_events()
        recent_event = f"在{recent_info[5]}，事件{recent_info[2]}"

        content = {"history":recent_event, "profile":user_profile}
        infos = self.execute(content)
        logger.info(infos)

        event_list = []

        for info in infos:

            context = Context()
            await context.append_context(message=SingleContext(create_time=datetime.now(), role="outer",content="[背景]"+info["reason"]))

            event_list.append(Event(name=info["name"], summary="",history=context))

        event_bank = EventBank()
        event_bank.init_event_list(event_list)
        return event_bank



