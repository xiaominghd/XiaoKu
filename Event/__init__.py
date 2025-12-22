"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from typing import List
from base.api import *
import copy
from datetime import datetime

class SingleContext:

    def __init__(self, create_time, role, content):

        self.create_time = create_time
        self.role = role
        self.content = content

class Event:

    def __init__(self, name:str=None, event_history:SingleContext=None, tail:List[SingleContext]=None):
        if tail is not None:
            self.tail = tail
            self.round = len(tail)
        else:

            self.tail = []
            self.round = 0

        if event_history is None:
            self.event_history = SingleContext(create_time=datetime.now(),role="outer", content="")
        else:
            self.event_history = event_history


        self.name = name
        self.messages = []

        self.lock = asyncio.Lock()

    async def insert_message(self, message:SingleContext):

        async with self.lock:

            self.tail.append(message)
            self.messages.append(message)

    async def update_history(self):

        if len(self.tail) < 20:
            # 超过20轮就更新一次小尾巴，小尾巴保持在15轮之后第一个user的位置
            return
        else:

            old_tail_length = len(self.tail)

            try:
                target_index = next(i for i, v in enumerate(self.tail) if i > 14 and v.role=="user")
            except StopIteration:
                return

            new_tail = copy.deepcopy(self.tail[target_index:])  # 不能直接改
            prepared_merge_tail = copy.deepcopy(self.tail[:target_index])
            conversation_str = "\n".join([f"{c.role}：{c.content}" for c in prepared_merge_tail])

            prompt = f"""你需要根据用户的历史对话总结和最新的对话走向情况，形成一份新的总结。
请遵循以下要求生成总结：

**总结要求**
- 如果历史对话总结为空，则根据最新的对话走向情况，生成一段总结。
- 如果历史对话总结不为空，请你提炼最新对话中的关键信息，对历史对话总结进行续写。
- 给定的对话中可能会存在以[背景]和[历史]开头，角色为outer的信息。对于这类信息，你需要判断其中是否存在对当前对话有意义的内容。
如果没有，请及时舍弃。如果有，请你将这些有意义的信息进行压缩之后入到对话总结中。

**总结角度**
1. **核心议题与问题**：对话讨论的主题、用户的核心需求或待解决的问题
4. **达成的决议与解决方案**：双方明确同意的结论、采纳的方案、确认的答案
5. **计划中的后续步骤**：约定的下一步行动、待办事项、预期交付成果及时间（如有）
6. **未解决或待定事项**：尚未明确的问题、需要后续跟进的点、存在的疑虑或分歧

**输出格式要求：**
- 以连贯、简洁的段落形式输出总结内容，并且保持只有一段。
- 语言保持专业、清晰，避免模糊表述（如“一些”“几个”）
- 仅输出总结内容，不包含任何额外解释、标题或注释

**历史总结：**
{self.event_history.content}

**最新对话内容：**
{conversation_str}"""

            new_history = await get_qwen_max_answer_async(prompt, enable_think=False)

            async with self.lock:

                contexts = new_tail + self.tail[old_tail_length:]
                self.tail = contexts
                self.event_history = SingleContext(create_time=datetime.now(), role="outer", content=new_history)

            return self.event_history

    async def get_key_point(self):


        infos = trans_messages2str(self.tail)  # 将当前的尾巴用于检索历史信息

        if infos == "":
            return []


        prompt = f"""你是一个聪明的助手，你的任务是根据用户和助手的对话，生成当前对话的2-3个主题。这些主题将会被用于在历史信息中检索具有相似主题的事件。
请你以json的形式进行返回，返回示例，除此之外不要返回其他信息:{{"result":["主题1","主题2"]}}
用户和助手的对话情况如下：
{infos}"""

        info = await get_qwen_max_answer_async(prompt)

        try:

            info = json.loads(info)
            return info["result"]

        except Exception as e:
            logger.error(f"获取关键信息失败：{e}")
            return []





