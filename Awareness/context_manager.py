"""
@author: Gonghf
@date: 2025/11/25
@description: 管理历史信息
"""
import math
import re
import numpy as np
from Scheduler import *
from Events.EventManager import *
from sklearn.metrics.pairwise import cosine_similarity

class ContextManager:

    def __init__(self, msg_bank:MessageBank, event_bank:EventBank):

        self.messages = msg_bank
        self.events = event_bank

    def split_context(self):

        merged = []
        n = len(self.messages.message_list_dict["is_send"])
        i = 0
        while i < n:
            current = self.messages.message_list_dict["is_send"][i]

            if current.content == "[系统上下文开始]":

                if i + 1 < n and "[系统上下文结束]" in self.messages.message_list_dict["is_send"][i + 1].content:
                    system_content =current.content  + self.messages.message_list_dict["is_send"][i + 1].content

                    merged.append(Msg(role='outer', content=system_content, is_send=False))

                    i += 2  # 跳过这两条已处理的消息
                    continue

                else:
                    # 如果没有找到配对的结束标记，保留原始内容
                    merged.append(current)
                    i += 1
            else:
                # 普通对话合并
                current_role = current.role
                current_content = [current.content]

                # 检查后续相同角色的消息
                j = i + 1
                while j < n:
                    next_item = self.messages.message_list_dict["is_send"][j]

                    # 如果遇到系统上下文开始，停止合并
                    if next_item.content == "[系统上下文开始]":
                        break

                    # 如果角色相同，合并内容
                    if next_item.role == current_role:
                        current_content.append(next_item.content)
                        j += 1
                    else:
                        break

                # 合并相同角色的内容
                merged_content = "".join(current_content)
                merged.append(Msg(role=current_role, content=merged_content, is_send=True))

                i = j  # 移动到下一个未处理的消息

        return merged

    @staticmethod
    def get_current_event_embedding(event:Event) :

        if event.summary is not None:

            summary_embedding = get_qwen_embedding(event.summary)[0]

        else:

            summary_embedding = None

        user_content = [h.content for h in event.history if h.role == "user"]
        residual_embedding = np.mean(get_qwen_embedding(user_content), axis=0)  # 将用户表达的内容做一个平均

        return summary_embedding, residual_embedding

    @staticmethod
    def extract_history_and_background(text):
        """
        从系统上下文文本中提取历史和背景信息

        Args:
            text (str): 包含系统上下文的文本

        Returns:
            tuple: (history_list, background_list) 包含历史信息列表和背景信息列表
        """
        # 移除开头和结尾的系统上下文标记

        cleaned_text = re.sub(r'^\[系统上下文开始\]|\[系统上下文结束\]$', '', text).strip()

        # 使用正则表达式匹配所有标签和内容
        # 这个模式会匹配 [历史] 或 [背景] 后跟任意字符，直到下一个标签或字符串结束
        pattern = r'\[(历史|背景)\](.*?)(?=\[历史\]|\[背景\]|$)'
        matches = re.findall(pattern, cleaned_text, re.DOTALL)

        # 分别提取历史和背景信息
        history_list = []
        background_list = []

        for tag, content in matches:
            content = content.strip()
            if tag == '历史':
                history_list.append(content)
            elif tag == '背景':
                background_list.append(content)

        return history_list, background_list

    @staticmethod
    async def get_important_info(event_embedding, info_list, forget_rate):

        info_embedding = get_qwen_embedding(info_list)

        summary_score = cosine_similarity([event_embedding[0]], info_embedding)[0]
        res_score = cosine_similarity([event_embedding[1]], info_embedding)[0]

        scores = np.maximum(summary_score, res_score)  # 逐元素比较较大的一个结果
        scores = forget_rate * scores  # 乘上遗忘参数

        high_score_indices = np.where(scores > 0.1)[0]

        # 返回对应info_list中的元素组成的新列表
        important_info = [info_list[i] for i in high_score_indices]

        return important_info

    async def pop_history(self):

        history = self.split_context()  # 将历史信息进行中整合

        current_history_length = len(history)  # 计算当前历史事件的长度

        # 计算当前事件描述的embedding
        event_embedding = self.get_current_event_embedding(self.events.current_event)

        for i, h in enumerate(history):

            if h.role != "outer": continue

            forget_rate = math.exp(-0.1 * (current_history_length - i))  # 设置一个遗忘参数

            current_history, current_background = self.extract_history_and_background(h.content)

            important_history = await self.get_important_info(event_embedding, current_history, forget_rate)
            important_background = await self.get_important_info(event_embedding, current_background, forget_rate)

            h.content = ("[系统上下文开始]" + "[历史]".join(important_history) +
                         "[背景]".join(important_background) + "[系统上下文结束]")

async def main():

    messages = [
        {"role": "user", "content": "早上好呀小酷"},
        {"role": "user", "content": "现在十一点了在忙什么呢"},
        {"role": "assistant",
         "content": "主人早上好～不过现在都十一点啦，该说“上午好”咯！昨天喝那么多酒，今天头还疼吗？记得多喝水，我有点担心你呢。"},
        {"role": "user", "content": "[系统上下文开始]"},
        {"role": "assistant","content": """[历史]用户最近在开发小酷的时候遇到了一些问题，包括对于小酷的记忆管理 [历史]用户最近在开发小酷的时候遇到了一些问题，包括对于小酷的记忆管理 [背景]新闻：上下文工程或取代提示词工程成为更好的历史信息管理工具[系统上下文结束]"""},
        {"role": "user", "content": "昨晚可没有喝太多，我能够注意得到自己的身体呢"},
        {"role": "assistant", "content": "那就好呀～主人能照顾好自己，我就放心多啦！"},
        {"role": "user", "content": "小酷知道喝酒对哪个部位的损伤最大吗"},
    ]



    msg_bank = MessageBank()
    for m in messages:
        msg = Msg(role=m["role"], content=m["content"], is_send=True)
        msg_bank.message_list_dict["is_send"].append(msg)

    current = Event(name="帮助主人健康慰问", summary="用户感觉自己有点胃痛", history=msg_bank.message_list_dict["is_send"])
    cm = ContextManager(msg_bank=msg_bank, event_bank=EventBank(current_event=current))

    await cm.pop_history()


if __name__=="__main__":
    asyncio.run(main())
