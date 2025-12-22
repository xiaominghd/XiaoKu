"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from Memory.memory_es_v1 import *
from Memory.memory_mysql_v1 import *
from Event import *
from datetime import datetime

class MemoryBank:

    def __init__(self):

        self.mysql = HistoryTableManager()
        self.es = HistoryIndexManager()

        self.is_retrieved = []

    @staticmethod
    def split_event(event: Event):

        max_round = 6
        chunks = []
        mini_chunk = []
        i = 0
        conversations = event.messages
        while i < len(conversations) - 1:

            if conversations[i].role == "outer":

                i += 1
                continue

            else:

                if len(mini_chunk) < max_round and "[指引信息开始]" not in conversations[i].content:

                    mini_chunk.append(conversations[i])
                    i += 1

                else:

                    conversation_str = ""
                    i += 1
                    for j, info in enumerate(mini_chunk):
                        conversation_str += f"第{j + 1}轮 {info.role}:{info.content}\n"
                    prompt = f"""你的任务是分析对话的连贯性，判断从第几轮开始对话主题或内容方向发生了变化。

分析步骤：
1. 仔细阅读整个对话，理解每轮对话的主题和内容
2. 判断相邻轮次之间的连贯性，是否延续了相同的话题或逻辑
3. 找出第一个出现主题转换或内容跳跃的轮次

判断标准：
- 如果所有对话内容保持一致性，没有切换，则返回-1
- 如果从第n轮开始与第n-1轮的内容有不同（话题转变、跳跃到无关内容等），则返回n

请只以JSON格式返回结果，不要包含任何解释说明。
返回格式：{{"result": 2}}

需要分析的对话内容：
{conversation_str}
"""

                    try:

                        answer = json.loads(get_qwen_flash_answer(prompt))["result"]

                        if answer == -1:
                            chunks.append(mini_chunk)
                        else:
                            chunks.append(mini_chunk[:answer - 1])
                            mini_chunk = mini_chunk[answer:]
                        logger.info(f"切片位置到达{i}轮，总共{len(conversations) - 1}轮")

                    except Exception as e:
                        mini_chunk = []
                        logger.error(f"切片出错：{e}")
                        continue

        if len(mini_chunk) != 0:
            chunks.append(mini_chunk)

        return chunks

    def insert_event(self, event:Event):

        if event.round > 5:  # 小于五轮的对话根本不管

            event_id = generate_timestamp_key()
            logger.info(f"开始进行切片")
            chunks = self.split_event(event)

            self.mysql.insert_table(chunks, event, event_id)
            self.es.handle_event(chunks, event, event_id)
            return event

        else:
            return None

    async def get_event_memory(self, event:Event):

        # 根据当前的事件信息检索数据库（关键query）
        # 将检索之后的结果组成结构化的信息。
        key_infos = await event.get_key_point()

        child_retrieve_result = []
        ids = []

        for info in key_infos:

            logger.info(info)

            results = self.es.search_child_chat(info)
            for result in results:

                if result['child_chat_id'] in self.is_retrieved:
                    continue
                else:
                    ids.append(result['child_chat_id'])
                    self.is_retrieved.append(result['child_chat_id'])
                # 防止同一信息反复检索
                history = await self.get_text_memory(result)
                if history is not None:
                    child_retrieve_result.append(history)


        infos = self.mysql.update_child(ids)

        return child_retrieve_result


    async def get_text_memory(self, infos):

        # 获取当前的时间，以及历史的事件信息，将检索到的结果转化为结构化的内容，插入到上下文当中。
        current_time = datetime.now()
        text_time_flag = self.mysql.search_event_by_id(infos['child_chat_id'])
        if text_time_flag is not None:
            conversation_str = "\n".join([f"{r['role']}:{r['content']}" for r in infos['content']])
            prompt = f"""你是一个聪明的助手，你的任务是在当下，对历史的用户和助手的对话进行总结。
    总结的内容需要包含：
    1、时间信息。当前时间是{current_time} 历史信息发生的时间是{text_time_flag['create_time']}。
    请你以相对时间（几天前，几小时前）或者是绝对时间（具体的时间）标明历史时间发生的时间
    2、对话信息。请你从用户和助手的对话中，对其中的关键信息形成一个简单的总结，保持在50字以内。
    3、请你将上述的总结内容整合成一段话进行返回，除此之外不要返回其他任何信息。
    用户和助手的对话信息：
    {conversation_str}"""
            history = await get_qwen_max_answer_async(prompt)

            return history
        else:
            return None





















