"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from Memory.memory_es_v1 import *
from Memory.memory_mysql_v1 import *
from Event import *

class MemoryBank:

    def __init__(self):

        self.mysql = HistoryTableManager()
        self.es = HistoryIndexManager()

    @staticmethod
    def split_event(event: Event):

        max_round = 6
        chunks = []
        mini_chunk = []
        i = 0
        conversations = event.history.cache
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

        for info in key_infos:

            logger.info(info)

            results = self.es.search_child_chat(info)
            child_retrieve_result += results

        ids = [r["child_chat_id"] for r in child_retrieve_result]

        infos = self.mysql.update_child(ids)

        return child_retrieve_result


















