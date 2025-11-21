"""
@author: Gonghf
@date: 2025/11/7
@description: 小酷对于当前对话状态的感知
"""
import json

from base.api import *
from Scheduler import *
class KuFeeling:

    def __init__(self, reply:MessageBank):

        self.reply = reply

    async def summary_from_conversation(self, history):

        reply = self.reply

        current_conversation = reply.message_list_dict["is_send"]
        current_conversation_str = reply.print_message(current_conversation)  # 获取当前对话

        current_summary = history

        human_feeling_prompt = f"""你是一个信息提取助手，任务是从提供的对话历史聊天总结和当前聊天记录中，提取出两类核心信息用于后续检索：

1.  **客观事件信息**：对话中讨论的核心问题、已采取的行动、达成的决议或解决方案、计划的后续步骤等客观事实。
2.  **主观用户反馈**：用户表达出的情绪状态（如满意、沮丧、困惑）、明确提出的偏好（如喜欢/不喜欢）、个人习惯以及其对事件或解决方案的直接评价。

请严格输出一个json形式的对象，json的key分别是客观事件信息和主观用户反馈，value分别是两者的简单总结内容。除此之外不要输出其他任何信息。
输出格式示例（仅做格式参考）：
{{
"客观事件信息":"客观事件信息总结",
"主观用户反馈":"主观用户反馈总结"
}}
历史聊天总结：
{current_summary}
当前聊天
{current_conversation_str}"""


        human_feeling = get_deepseek_answer([{'role':"user","content": human_feeling_prompt}])

        try:
            human_feeling = json.loads(human_feeling)
            summary, status = human_feeling["客观事件信息"], human_feeling["主观用户反馈"]

            print(f"对当前历史信息进行总结之后的内容为：{summary}")
            print(f"对当前用户状态进行总结之后的内容为：{status}")
            return summary, status

        except Exception as e:
            print(f"在对大模型输出：{human_feeling}时报错：{e}")
            return None, None








