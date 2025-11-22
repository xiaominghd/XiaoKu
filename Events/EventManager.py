"""
@author: Gonghf
@date: 2025/11/17
@description: 需要实现一个非常快的事件管理器，主动的引导话题。
确定当前聊天所处的事件范畴，极快的更新历史信息，重要性判断和切换。
"""
import asyncio

from Scheduler import *
from base.api import *
from Events import *
from Tool.Agents.event_updater import *

class EventBank:

    def __init__(self, current_event:Event=None):

        # 使用三个区分别来管理正在讨论，备选和完结，完结区需要控制长度，当超长的时候会进行更新

        self.current_event  = current_event

        self.prepared_events = []

        self.finished_events = []

        self.prepared_events_mapper = {}

    async def init_from_nl(self, task_info:str):

        events = await self.get_event_from_nl(task_info)

        if len(events) != 0:

            self.prepared_events = events

            self.prepared_events_mapper = dict([(e.name, e) for e in self.prepared_events])

            self.current_event = self.prepared_events.pop(0)

            logger.info(f"事件列表初始化完成！当前事件信息为：{self.current_event.name} \n 当前事件背景信息为：{self.current_event.back_ground}")

        if len(events) == 0:

            logger.error(f"事件列表初始化失败。")

    async def clear(self):

        finish_events = self.finished_events + [self.current_event]

        self.prepared_events = []
        self.current_event = None
        self.prepared_events_mapper = {}
        self.finished_events = []  # 清空所有事件

        return finish_events

    # 事件列表更新
    async def update(self, event_name:str):

        event = self.prepared_events_mapper[event_name]  # 通过映射表的方式找到当前数据

        self.current_event = event  # 当前事件需要进行一次总结
        self.finished_events.append(event)

        # self.prepared_events_mapper.pop(event_name)  # 映射表不pop出去，防止再召回的情况报键不存在

        # 更新候选话题
        self.prepared_events = [event for event in self.prepared_events if event != self.current_event]

        # 更新已经完成的话题
        self.finished_events = [event for event in self.finished_events if event != self.current_event]


    # 判断是否是当前话题
    async def check_current_conversation(self, conversation: Msg):

        # 将当前的对话加入到事件当中去
        role_mapper = {"user": "主人", "assistant": "小酷"}

        pre_conversation = self.current_event.history

        conversation_str = "\n".join([f"{role_mapper[m.role]}:{m.content}" for m in pre_conversation+[conversation]])
        # 将当前的会话与之前的对话进行拼接

        other_event = [e.name for e in self.prepared_events + self.finished_events]

        other_event_str = "\n".join(other_event)

        prompt = f"""# 任务说明

## 核心目标
根据当前对话内容准确判断用户正在讨论的话题。

## 话题判断规则

### 1. 话题保持条件
当出现以下情况时，应保持当前话题不变：
- 用户和助手正在进行无实质内容的闲聊
- 对话内容仍然围绕当前话题展开
- 用户只是对当前话题进行补充、延伸或细化
- 对话中出现简单的回应、确认或社交性表达

### 2. 话题切换条件
**只有当用户明确表达切换意图时**，才认定为话题切换。明确意图包括：
- 直接声明："让我们换个话题吧"、"我们聊点别的"
- 明确提问新领域："你知道XXX吗？"、"我们讨论一下YYY"
- 使用转折词引入全新内容："话说回来..."、"另外..."，且后面跟随的是与当前话题无关的新内容

### 3. 话题延伸的定义
以下情况视为话题延伸，仍属于同一话题：
- 从主话题自然延伸到相关子话题（科技→人工智能）
- 在原有话题范围内进行深入讨论
- 举例说明或补充相关信息
- 话题的细化或具体化

### 4. 结束对话条件
当用户明确表达结束对话的意图时，应返回"结束"。明确意图包括：
- 直接告别："再见"、"拜拜"、"下次聊"
- 表达结束意愿："不想聊了"、"结束对话"、"就到这里吧"
- 其他明确的结束性话语

## 输出要求
- 仅输出话题名称或"结束"
- 优先匹配备选话题名称列表中的最接近项
- 若无匹配项，创建简短准确的话题名称总结
- 如果用户表达了结束对话意图，输出"结束"
- 如果用户表达了切换话题意图但未指定具体话题，默认返回其他话题列表中的第一个话题
- 话题名称应简洁明了，体现核心内容

## 输入信息
用户和助手的对话：{conversation_str}
用户和助手当前的话题（话题名称：话题总结）：
{self.current_event.name}:{self.current_event.summary}
用户和助手的其他话题名称列表：
{other_event_str}

## 处理流程
1. 首先判断是否有明确的结束对话意图：
   - 如有，输出"结束"
   - 如无，继续下一步
2. 判断是否有明确的话题切换意图：
   - 如无切换意图，检查是否属于当前话题的延伸或闲聊：
     - 如果是，保持当前话题
     - 如果否，可能为新话题，进入步骤3
3. 如有切换意图：
   - 如果用户指定了新话题内容，在备选话题名称列表中寻找最佳匹配：
     - 若找到匹配，返回该话题名称
     - 若无匹配，创建合适的话题名称
   - 如果用户未指定新话题（如只说"换个话题"但未说换什么），默认返回其他话题列表中的第一个话题
"""

        answer = get_qwen_flash_answer(prompt)

        if answer in other_event:  # 当前正在进行状态切换

            logger.info(f"将当前话题：{self.current_event.name} 切换至 {answer}")

            await self.update(answer)  # 仅调整位置

            asyncio.create_task(self.update_summary(self.prepared_events_mapper[answer]))  # 只更新总结
            self.current_event.history.append(conversation)

            return self.prepared_events_mapper[answer]  # 返回的数据类型是不同的


        elif answer not in other_event and answer != self.current_event.name: # 当前正在创建新事件

            new_event = Event(name=answer)

            self.finished_events.append(self.current_event)

            asyncio.create_task(self.update_summary(self.current_event))  # 更新总结信息

            self.current_event = new_event

            self.current_event.history.append(conversation)

            return self.prepared_events[answer]

        elif answer == "结束":
            events = self.clear()
            return events

        return None

    # 当前话题深度挖掘
    @staticmethod
    async def deep_analyse(current_bg:str, summary:str, topic_name:str, conversations:List[Msg]):

        role_mapper = {"user": "主人", "assistant": "小酷"}
        conversation_str = "\n".join([f"{role_mapper[m.role]}:{m.content}" for m in conversations])

        # 指定一个特定的条件进行更新
        query = f"""当前话题为：{topic_name}
当前的背景为：{current_bg}
历史对话总结为：{summary}
当前对话为：{conversation_str}"""

        result = await EventUpdaterAgent().execute(content=query)
        print(f"更新{topic_name}的背景信息为：{result}")

        return result

    # 主动引导话术生成
    async def generate_conversation(self):

        current_info = self.current_event

        topic = f"{current_info.name}\n 话题背景：{current_info.back_ground}"
        summary = f"{current_info.summary}"

        role_mapper = {"user": "主人", "assistant": "小酷"}
        conversation_str = "\n".join([f"{role_mapper[m.role]}:{m.content}" for m in current_info.history])

        prompt = r"""# 任务
你的任务是根据用户历史对话和当前话题信息，优先基于最新对话内容分析需要深入探讨的话题方向。
如果当前对话具有深度挖掘价值，则延续当前话题；如果无深度挖掘意义，则转向背景信息寻找子话题。最终生成一条自然连贯的推荐话术与用户互动。

# 工作流程

## 1. 当前对话优先分析
- **深度价值评估**：首先专注分析用户最新对话内容，判断是否具有深度挖掘意义。评估标准包括：
  - 话题是否包含未充分讨论的技术细节、应用场景或影响维度
  - 用户是否表现出持续兴趣或提出后续问题
  - 是否存在可延伸的具体案例或实践应用
- **延续性判断**：如果当前对话具备深度挖掘价值，立即锁定该方向进行深入拓展

## 2. 话题深度挖掘策略
- **当前话题延续**（优先执行）：
  - 基于最新对话的具体内容，挖掘相关但未讨论的细节层面
  - 结合用户身份特征和已知兴趣点，提出更深入的技术探讨
  - 联系行业最新动态，提供时效性强的延伸方向
- **背景话题转向**（仅当当前话题无挖掘价值时启用）：
  - 综合分析话题背景信息和历史会话总结
  - 识别与用户背景相关但未涉及的新子话题
  - 确保话题转换自然且符合对话逻辑

## 3. 话术生成规范
- **单条多句结构**：生成唯一一条推荐话术，可采用多句组合形式，包括：
  - 承接句：自然衔接最新对话内容
  - 问题句：提出开放式深入问题
  - 引导句：提供讨论方向或案例参考
- **对话连续性**：确保话术与最新对话内容直接相关，保持对话流畅度
- **深度引导性**：话术应能有效引导用户分享观点或展开详细讨论

# 返回数据
以JSON格式返回单条推荐话术，话术可为多句组合：
{
  "result": "完整的一条推荐话术"
}
<输入>
用户的当前的话题名称以及背景
<TOPIC>
用户和助手历史会话的总结
<SUMMARY>
用户和助手最新的对话信息
<CONTEXT>
"""
        prompt = prompt.replace("<TOPIC>", topic).replace("<SUMMARY>", summary).replace("<CONTEXT>", conversation_str)



        answer = get_deepseek_answer(message=[{"role":"user", "content":prompt}])

        try:
            answer = json.loads(answer)["result"]
            ku_answer = ku_speaking(history=conversation_str, text=answer)
            return ku_answer

        except Exception as e:
            print(f"解析返回的结果失败：{e}")
            return None

    # 整体事件处理机制
    async def get_conversation_guide(self):

        # 输入的仅有用户当前轮次的对话内容
        # 获取当前轮次的对话
        role_mapper = {"user": "主人", "assistant": "小酷"}

        conversation = "\n".join([f"{role_mapper[h.role]}:{h.content}" for h in self.current_event.history])

        prompt = r"""## 核心任务
作为智能对话助手，你需要根据完整的上下文等信息，判断当前聊天是否需要进行话题切换，并为聊天机器人推荐最合适的话术，确保对话自然流畅且符合用户兴趣。

**执行条件（需满足至少两项）：**
- 用户连续两轮以上给出简短、敷衍回复
- 用户明确表示"不感兴趣"或"换话题"
- 当前话题已重复讨论且无新进展

**具体执行流程：**
1. **切换时机判断**
   - 分析最近3轮对话的情绪倾向
   - 检测回复长度和内容质量的变化
   - 识别明确的负面反馈词汇

2. **话题选择策略**
   - 优先选择与用户背景相关的推荐话题
   - 考虑话题的普适性和趣味性
   - 避免与已讨论话题过于相似的内容

## 📝 输出规范

### 质量检查标准
- ✅ 话术长度：1-2句话，不超过50字
- ✅ 自然流畅：符合对话上下文，过渡自然
- ✅ 价值明确：为用户提供信息价值或讨论价值
- ✅ 个性化：结合用户身份和已知兴趣点
- ✅ 可操作性：机器人能够基于此话术继续对话
## 输出格式
如果不需要进行，请你输出一个空json
如果需要进行切换切换，请你以json的格式返回切换后的话题名称以及推荐的话术
除了输出此json之外，不要输出其他内容
返回结果示例：
{"话题名称":"具体的话题名称","推荐话术":"推荐的具体话术"}
## 🎪 上下文信息
**对话总结：**

**历史对话记录：**
<conversation>

**备选话题库：**
<topic_base>
"""

        if len(self.current_event.history) < 5:
            return
        prompt = prompt.replace("<conversation>", conversation).replace("<topic_base>", "\n".join([e.name for e in self.prepared_events]))
        response = get_qwen_max_answer(prompt)
        print(response)

        try:

            info = json.loads(response)
            if "话题名称" in info:

                new_topic = info["话题名称"]

                logger.info(f"开始进行话题切换，当前话题是:{self.current_event.name}，切换之后的新话题是：{new_topic}")

                self.finished_events.append(self.current_event)
                self.current_event = self.prepared_events_mapper[info["话题名称"]]
                self.prepared_events_mapper.pop(info["话题名称"])  # 映射表pop出去
                self.prepared_events = [event for event in self.prepared_events if event != self.current_event]

                return info["推荐话术"]

        except Exception as e:
            logger.error(f"进行话题切换报错:{e}")
            return None

    # 对于候选话题重新排序
    async def rerank(self, msg_bank:List[Msg]):

        # 已经发送的消息列表，实时的对推荐的话术列表进行重排序
        role_mapper = {"user": "主人", "assistant": "小酷"}

        msg_list_str = "\n".join([f"{role_mapper[m.role]}:{m.content}" for m in msg_bank])
        # 创建对话文本

        prepared_event = "\n".join([e.name for e in self.prepared_events])
        # 推荐话题列表列表

        prompt = f"""# 任务
你的任务是根据主人和小酷的历史对话，根据话题的匹配度，对推荐话题按照从高到低的顺序进行排序。
# 工作流程
1 首先你需要理解用户的和小酷当前的对话，分析用户对什么话题更感兴趣。
话题会以 [话题名称]:[话题总结] 的形式给出
2 排序的原则：
  1 优先选择与用户当前感兴趣的话题具有强关联性的话题。
  2 用户明显不喜欢或者是回避的话题应该被排到最后
# 输出要求
请你输出一个json格式的数据，其中值是一个排序后的话题名称列表，列表中所有的事件名称必须在参考的推荐话题当中。之外不要返回其他任何信息
返回结果示例：
{{"result":["话题1","话题2","话题3"]}}
用户和小酷的历史对话如下：
{msg_list_str}
推荐话题如下：
{prepared_event}
"""
        result = get_deepseek_answer([{"role":"user", "content":prompt}])

        try:
            result = json.loads(result)["result"]
            logger.info(f"排序后的话题推荐顺序为：{result}")

            new_prepare_event = []

            for score, r in enumerate(result):
                current_envent = self.prepared_events_mapper[r]
                current_envent.score = score + 1
                new_prepare_event.append(current_envent)

            self.prepared_events = new_prepare_event

        except Exception as e:

            logger.error(f"话题重排序时解构出错，错误信息为：{e}")

    # 更新事件总结信息
    @staticmethod
    async def update_summary(event:Event):

        if len(event.history) > 20:

            prompt = r"""你是一个专业的对话摘要生成助手，你的任务是结合历史总结和当前对话中生成一个简洁自然的对话摘要。
    
    # 摘要生成原则：
    结合历史与当前：综合历史总结和当前对话内容，确保摘要连贯反映完整的对话进展
    保持连贯叙事：用流畅的段落形式描述对话发展脉络，不要用列表或JSON
    聚焦关键信息：只保留用户需求、重要决定、个人偏好、待办事项等实质性内容
    忽略过程细节：省略问候语、确认词、思考过程等无关内容
    
    # 需要包含的关键要素（请严格基于对话内容，不要编造）：
    用户身份特征：姓名、称呼等个人特征
    核心需求：用户在历史及当前对话中想要解决的主要问题
    重要决定：双方达成的共识或做出的选择
    用户偏好：用户明确表达的喜欢/不喜欢、习惯等
    待办事项：需要后续跟进的任务
    
    # 输出要求：
    如果历史总结和当前对话内容均为空，输出空字符串
    如果历史总结为空，当前对话不为空，请你仅根据当前对话进行总结。
    请保证生成的结果的长度在3个连贯段落以内，语言简洁专业
    只输出摘要内容，不要添加其他任何信息
    对话内容：
    <历史总结>
    <HISTORY>
    </历史总结>
    
    <当前对话>
    <CONVERSATION>
    </当前对话>
    """
            role_mapper = {"user": "主人", "assistant": "小酷"}

            msg_list_str = "\n".join([f"{role_mapper[m.role]}:{m.content}" for m in event.history])
            history_length = len(event.history)

            query = prompt.replace("<HISTORY>", event.summary).replace("<CONVERSATION>", msg_list_str)

            new_summary = get_deepseek_answer(message=[{"role":"user", "content":query}])

            event.summary = new_summary

            for _ in range(history_length):  # 采用pop的形式防止漏掉信息
                event.history.pop(0)

        return event

    # 从自然语言中初始化事件的列表
    @staticmethod
    async def get_event_from_nl(tasks):

        prompt = r"""# 任务
你的任务是从提供的聊天计划中提取所有关键事件，并以结构化的JSON格式返回。每个事件应包括一个简短的名称（task_name）和背景信息（task_bg）。

# 执行流程
1. 仔细阅读聊天计划，识别出所有关键事件。关键事件指聊天中提到的具体行动、计划或讨论点。
2. 对于每个事件：
   - 分配一个简单且描述性的名称作为“task_name”（例如，“会议安排”或“项目讨论”）。
   - 提取事件的详细信息或上下文作为“task_bg”，用简洁语言总结。
3. 按照事件的重要程度对事件进行排序：从最重要到最不重要。重要程度基于事件在聊天中的显着性、影响或优先级；如果没有明确指示，请根据上下文合理判断。
4. 只返回JSON格式的结果，不要包含任何其他文本、注释或解释。

# 返回要求
- 返回一个有效的JSON对象，结构必须严格遵循示例。
- 至少要返回一个事件。
- 示例：
  {"results":[{"task_name":"事件1","task_bg":"事件背景1"},{"task_name":"事件2","task_bg":"事件背景2"}]}

聊天计划如下：
<TASKS>"""

        query = prompt.replace("<TASKS>", tasks)

        results = get_deepseek_answer(message=[{"role":"user", "content":query}])
        print(results)
        try:

            results = json.loads(results)["results"]
            return [Event(name=r["task_name"],back_ground=r["task_bg"]) for r in results]

        except Exception as e:
            print(f"初始化事件库时出现错误：{e}")
            return None







async def main():
    msg1 = Msg(role='user', content="那AI电力现在有哪些方案呢",is_send=True)
    msg2 = Msg(role="assistant", content="主人AI对GPU耗电还是非常大的",is_send=True)
    event1 = Event(name="科技行为讨论", summary="用户和小酷讨论了关于AI电力的情况，并且对AI训练对GPU资源的高消耗表示惊讶",
                   history=[msg2, msg1], back_ground="用户最近对AI大模型以及其发展展现了较高的兴趣。最新消息，AI巨头英伟达公布了最新的财报，三季度营收提升百分之五十",score=1)

    envent_list = EventBank(current_event=event1)

    # asyncio.create_task(envent_list.init_from_nl(task_info="2025年11月19日（星期三），重庆今日天气多云，气温6-13℃，东北风转北风1级，湿度64%。"
    #                                    "今日科技类热点讨论围绕“AI时代‘提出好问题’与‘知道真答案’哪个更重要”展开：赵泠认为“知道真答案”更重要，因“提出好问题”依赖可靠知识；也有人认为AI时代提问精准更高效，如豆包等软件可通过“身份+问题+要求”模式给出答案。"
    #                                    "今日美食类话题涉及“炸鸡炸猪常见但炸牛少见”的现象：日本炸牛排出现早于炸猪排，但因猪肉价格便宜等因素，"
    #                                    "炸猪排更流行；近10年（2015-2025）炸猪排赛道拥挤，部分炸牛排品牌迎来机遇，炸牛排价格一般1200-2000日元。"))
    await envent_list.generate_conversation()



if __name__=="__main__":
    asyncio.run(main())






