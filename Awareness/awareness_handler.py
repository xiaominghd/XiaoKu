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

    async def summary_from_message_bank(self):

        role_mapper = {"user":"主人","assistant":"小酷"}

        # 使用message bank里面的事件去进行总结
        history_str = "\n".join([f"{role_mapper[m.role]}:{m.content}" for m in self.history])

        human_feeling_prompt = r"""你是一个智能的助手，你的任务是在小酷和主人的聊天中总结出以下的信息
1、聊天的总结。包括对于聊天内容的简要概述，既包括事件的全过程，也包括主人的一些重要的观点，在后续想要进一步了解的内容信息（如果有的话），但你要注意在总结过程中不要关注过多的细节问题。
2、主人的反馈。主要是针对于进行聊天过程中主人当前的心理状态，请不要进行过度的推断。
请你按顺序返回上述信息，并使用|将两者内容进行分隔，除此之外不要返回其他任何信息。
返回示例（仅做格式参考）：
主人和小酷分享了晚餐，并且想要进一步的了解健康饮食相关的知识。|主人心情高兴。
小酷和主人的聊天内容如下：
<history>
"""

        human_feeling = get_deepseek_answer([{'role':"user","content":human_feeling_prompt.replace("<history>", history_str)}])

        try:
            summary, status = human_feeling.split("|")
            return summary, status

        except Exception as e:
            print(f"在对大模型输出：{human_feeling}时报错：{e}")
            return None








