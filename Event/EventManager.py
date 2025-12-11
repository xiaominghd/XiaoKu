"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import statistics
import re
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


    async def update(self, event_name:str):

        event = self.prepared_events_mapper[event_name]  # 通过映射表的方式找到当前数据

        self.current_event = event  # 当前事件需要进行一次总结
        self.finished_events.append(event)


        # 更新候选话题
        self.prepared_events = [event for event in self.prepared_events if event != self.current_event]

        # 更新已经完成的话题
        self.finished_events = [event for event in self.finished_events if event != self.current_event]

    async def check_current_conversation(self, message: SingleContext):

        history = self.current_event.history.trans_cache2openai()

        history = history + [{"role":message.role, "content":message.content}]

        conversation_str = history
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
请你只输出当前话题的名称，除此之外不要输出其他任何信息。
"""

        answer = get_qwen_max_answer(prompt)
        logger.info(f"当前的话题为：{answer}")

        if answer == self.current_event.name:
            await self.current_event.history.append_context(message)

        if answer in other_event:  # 当前正在进行状态切换

            logger.info(f"将当前话题：{self.current_event.name} 切换至 {answer}")

            await self.update(answer)  # 仅调整位置

            await self.current_event.history.append_context(message)

            return self.prepared_events_mapper[answer]  # 返回的数据类型是不同的


        elif answer not in other_event and answer != self.current_event.name:  # 当前正在创建新事件

            new_event = Event(name=answer)

            self.prepared_events_mapper[answer] = new_event

            self.finished_events.append(self.current_event)
            self.current_event = new_event

            await self.current_event.history.append_context(message)

            return self.prepared_events_mapper[answer]

    async def get_conversation_guide(self):
        conversations = []
        for message in self.current_event.history.cache[2:]:

            if any(marker in message.content for marker in ["[系统上下文开始]", "[指引信息开始]","[系统上下文结束]"]):
                continue

            else:

                conversations.append(message)

        if len(conversations) < 3:
            return None

        conversation_str = "\n".join([f"role:{conversation.role}, content:{conversation.content}"
                            for conversation in conversations[-10:]])
        prompt = f"""你是一个专业的对话分析助手，请根据提供的用户与助手的历史对话内容，生成结构化指引，以提升用户参与积极性，并引导助手进行更有效的互动。

请从以下三个维度进行分析并提供建议，并确保输出为**纯JSON格式**：

## 1. 需求响应
- 评估助手是否充分关注用户的情感与需求
- 检查助手在对话过程中是否保持了：感知主人情绪，提供温暖的共情回应的人格。
- 检查是否有误解用户意图或信息遗漏

## 2. 对话目标（远期互动方向）
- 基于当前话题，推荐2-3个用户可能感兴趣的子话题或延伸方向
- 助手可能从对话中提取用户潜在画像特征（如兴趣、身份、需求等）。
- 提供自然过渡到新话题的对话策略

## 输出要求
- 仅返回一个JSON对象，格式严格如下，除此之外不要输出其他任何信息：
{{
  "需求": "需求响应",
  "目标": "对话目标"
}}

用户和助手的对话如下：
{conversation_str}"""

        answer = await get_deepseek_answer(message=prompt)

        return answer

    # def check_conversation_interest(self):
    #
    #     # 根据当前对话响应情况快速判断用户的感兴趣程度
    #     # 兼具时间判据以及当前回复的判据
    #     analysis = (
    #         ConversationInterestAnalyzer.get_conversation_interest_level(self.current_event.history.cache))
    #
    #     if analysis['interest_level'] != "high":
    #
    #         return True
    #     else:
    #
    #         return False


