"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""

from Memory.memory_manager import *
from Event.EventManager import *
from typing import Dict
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
    """
    将文本按照标点符号切分为短句子，同时考虑引号内的情况
    """
    # 定义句子结束的标点符号（不包括省略号）
    end_punctuation = r'[。！？；]'


    pattern = r'''
        (?:                       # 非捕获分组
            [^。"'「」『』《》()（）{}【】]    # 不包含任何引号的字符
            |                     # 或
            (?:"[^"]*"|'[^']*'    # 双引号或单引号内的内容
               |「[^」]*」|『[^』]*』        # 中文引号内的内容
               |《[^》]*》|\([^)]*\)         # 书名号或圆括号内的内容
               |（[^）]*）|{[^}]*}           # 中文括号或花括号内的内容
               |【[^】]*】)                  # 方括号内的内容
        )*?                       # 非贪婪匹配
        (?:                       # 结束条件
            ''' + end_punctuation + r'''     # 句子结束标点
            |                       # 或
            $                       # 字符串结束
        )
    '''

    # 编译正则表达式，忽略空白字符和注释
    pattern = re.compile(pattern, re.VERBOSE | re.DOTALL)

    # 查找所有匹配
    sentences = []
    pos = 0

    while pos < len(text):
        match = pattern.match(text, pos)
        if match:
            sentence = match.group(0).strip()
            if sentence:  # 过滤空字符串
                sentences.append(sentence)
            pos = match.end()
        else:
            # 如果没有匹配到，向前移动一个字符，避免死循环
            sentences.append(text[pos:pos + 1])
            pos += 1

    return sentences


class XiaoKu:

    def __init__(self, reply:MessageBank,events:EventBank, memory:MemoryBank):

        self.reply = reply
        self.events = events

        self.context = Context()


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

        current_event = await self.events.check_current_conversation(content)  # 确定当前话题，在这个环节里面完成任务的更新

        if current_event == self.events.current_event.name:

            await self.events.update(event_name=current_event, message=content)
            await self.context.append_message(content)

        else:

            # 进行话题切换
            logger.info(f"将当前话题：{self.events.current_event.name} 切换至 {current_event}")

            pre_event = await self.events.update(event_name=current_event, message=content)

            await self.context.trans_event(pre_event, self.events.current_event)



        await self.response()

    async def response(self):
        self.events.current_event.round += 2

        history = trans_messages2openai(messages=self.context.history + [self.context.event_history] + self.context.tail)
        print(history)

        ku_response = chat_with_qwen(history)

        create_time = datetime.now()

        response_list = split_text(ku_response)


        for r in response_list:
            self.reply.not_send.append(SingleContext(create_time, role='assistant', content=r))

        merged_conversation = SingleContext(create_time, role='assistant', content="".join(response_list))

        await self.context.append_message(context=merged_conversation)
        await self.events.current_event.insert_message(message=merged_conversation)

    async def clear(self):

        for event in self.events.finished_events + [self.events.current_event]:
            await event.update_history()
            result = self.memory.insert_event(event)
            if result is not None:
                logger.info(f"插入事件:{result.name}, 对话轮数{result.round}")




