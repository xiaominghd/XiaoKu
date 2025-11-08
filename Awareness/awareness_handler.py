"""
@author: Gonghf
@date: 2025/11/7
@description: 小酷对于当前对话状态的感知
"""
from base.api import *
from Scheduler import *
from Memory.memory_handler import *
from Memory.databases.es import *

class KuFeeling:

    def __init__(self, messages:MessageBank):

        self.history = messages.message_list_dict["send"]

    async def summary_from_message_bank(self, memory:KuMemory):

        role_mapper = {"user":"主人","assistant":"小酷"}



        # 使用message bank里面的事件去进行总结
        history_str = "\n".join([f"{role_mapper[m.role]}:{m.content}" for m in self.history])

        human_feeling_prompt = r"""你是一个智能助手，你的任务是从主人和小酷的对话历史中提取并总结以下关键信息：

涉及的事件：总结对话中提及的主要事件，包括事件的关键内容、发展过程和相关结果（如提及）。

用户的状态：分析主人在对话中表现出的行为、心情、意图和情感变化，用于构建全面的用户画像。

输出要求：

将两个总结用“|”符号分隔，格式为“事件总结：内容 | 用户状态：内容”。

只输出总结部分，不要添加任何其他文字、解释或格式。

对话历史如下:
<history>"""

        human_feeling = get_deepseek_answer([{'role':"user","content":human_feeling_prompt.replace("<history>", history_str)}])

        try:

            summary, status = human_feeling.split("|")
            summary = summary.split("：")[1]
            status = status.split("：")[1]


        except Exception as e:
            print(f"在对大模型输出：{human_feeling}时报错：{e}")
            return None

        await memory.insert_satus_summary(summary, status)
        return None










