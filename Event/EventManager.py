"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from Event import *
from typing import List
class EventBank:

    def __init__(self, current_event:Event=None):

        self.current_event = current_event

        self.prepared_events = []

        self.finished_events = []

        self.prepared_events_mapper = {}

    def init_event_list(self, event_list:List[Event]):

        self.current_event = event_list[0]

        self.prepared_events = event_list[1:]

        for event in event_list:

            self.prepared_events_mapper[event.name]=event

    async def update(self, event_name, message:SingleContext):
        if event_name == self.current_event.name:
            self.current_event.tail.append(message)
            return self.current_event

        if event_name in self.prepared_events_mapper:  # 当前正在进行状态切换

            logger.info(f"将当前话题：{self.current_event.name} 切换至 {event_name}")

            await self.current_event.update_history()

            res = self.current_event

            self.finished_events.append(self.current_event)
            self.current_event = self.prepared_events_mapper[event_name]

            self.current_event.tail.append(message)

            return res

        elif event_name not in self.prepared_events_mapper:  # 当前正在创建新事件

            new_event = Event(name=event_name)
            res = self.current_event
            await self.current_event.update_history()

            self.prepared_events_mapper[event_name] = new_event

            self.finished_events.append(self.current_event)
            self.current_event = new_event

            self.current_event.tail.append(message)
            return res



    async def check_current_conversation(self, message: SingleContext):

        history = trans_messages2openai(self.current_event.tail, load_outer=False)  # 获取当前的历史信息
        history = history + [{"role":message.role, "content":message.content}]


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
用户和助手的对话：{history}
用户和助手当前的话题：
{self.current_event.name}
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
请你只输出当前话题的名称，除此之外不要输出其他任何信息。
"""

        answer = get_qwen_max_answer(prompt)
        logger.info(f"当前的话题为：{answer}")

        return answer

    async def get_conversation_guide(self):
        conversations = [self.current_event.event_history] + self.current_event.tail
        # 将历史信息与当前对话信息进行整合 成为新的历史信息


        if len(conversations) < 10:

            conversation_str = "\n".join([f"role:{conversation.role}, content:{conversation.content}"
                            for conversation in conversations])
        else:
            conversation_str = "\n".join([f"role:{conversation.role}, content:{conversation.content}"
                                          for conversation in conversations[-10:]])

        if len(conversation_str) == 0:
            return None

        prompt = f"""你是一个专业的对话分析助手，请你根据提供的用户和助手的历史对话，生成以下两类信息：

## 1. 对话评价
- 检查助手在与主人的对话中对主人情绪的回应和感知是否充分。
- 检查助手在与主人的对话中是否存在幻觉：例如提及了历史信息之外的其他行为或者是反复提及与对话无关的行为
- 检查助手理解用户的意图是否存在遗漏的情况

## 2. 对话目标
- 基于当前话题以及外部信息，推荐2-3个用户可能感兴趣的子话题或延伸方向。
- 基于当前话题，助手可以尝试挖掘出的用户的画像特征（例如，性格、习惯），并基于设计对话的话题。
- 提供自然过渡到新话题的对话策略

## 输出要求
- 仅返回一个JSON对象，对话评价和对话目标均保持在50-100字之间，且只有一段。格式严格如下，除此之外不要输出其他任何信息：
{{
  "评价": "对话评价",
  "目标": "对话目标"
}}

用户和助手的对话如下：
{conversation_str}"""

        answer = await get_qwen_max_answer_async(message=prompt, enable_think=True, enable_search=True)

        return answer



