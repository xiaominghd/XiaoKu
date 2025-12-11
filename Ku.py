"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from typing import Dict
from Memory.memory_manager import *
from Event.EventManager import *
import random
from base.qwen_chat import *
from Context import *
from typing import Optional
import re

class MessageBank:

    def __init__(self):

        self.not_send = []
        self.is_send = []

    def send(self):

        message = self.not_send.pop(0)
        self.is_send.append(message)
        return message


def split_text(text):
    pattern = r'[^。！…]*(?:[。！…]+|$)'
    result = re.findall(pattern, text)
    # 过滤空字符串
    result = [s for s in result if s]
    return result


def select_sentences(response_list):
    if not response_list:
        return []

    # 确保第一句话一定返回
    selected = [response_list[0]]

    # 如果只有一句话，直接返回
    if len(response_list) == 1:
        return selected

    # 从第二句话开始，随机选择50%
    remaining_sentences = response_list[1:]

    # 计算需要选择的句子数量（向上取整）
    num_to_select = max(1, round(len(remaining_sentences) * 0.5))

    # 随机选择句子，但保持原有顺序
    indices = sorted(random.sample(range(len(remaining_sentences)), num_to_select))
    selected.extend([remaining_sentences[i] for i in indices])

    return selected



class XiaoKu:

    def __init__(self, reply:MessageBank,events:EventBank, memory:MemoryBank):

        self.reply = reply
        self.events = events


        self.memory = memory

        self.round = 0

    @staticmethod
    def _parse_tool_call(response: str) -> Optional[Dict]:
        """解析工具调用"""
        try:
            import json
            return json.loads(response)
        except:
            return None


    async def chat(self, message:str):

        content = SingleContext(create_time=datetime.now(), role="user", content=message)


        await self.events.check_current_conversation(content)  # 确定当前话题，在这个环节里面完成任务的更新

        await self.response()

    async def response(self):
        self.events.current_event.round += 2
        history = self.events.current_event.history.trans_cache2openai()
        # 构建历史信息

        ku_response = chat_with_qwen(history)

        create_time = datetime.now()

        response_list = split_text(ku_response)

        for r in response_list:
            self.reply.not_send.append(SingleContext(create_time, role='assistant', content=r))
        await self.events.current_event.history.append_context(SingleContext(create_time, role='assistant', content="".join(response_list)))

    def clear(self):

        for event in self.events.finished_events + [self.events.current_event]:
            event.update_summary()
            result = self.memory.insert_event(event)
            if result is not None:
                logger.info(f"插入事件:{result.name}, 对话轮数{result.round}")

    # async def get_guidance(self):
    #     info = await self.events.get_conversation_guide()
    #
    #     if info is not None:
    #         info = json.loads(info)
    #         self.events.current_event.history.append_context(SingleContext(create_time=datetime.now(),role="user",
    #                                                                    content=f'[指引信息开始]当下回复：{info["回复"]}远期目标：{info["目标"]}世界知识：{info["注意"]}[指引信息结束]'))
    #         await self.response()




