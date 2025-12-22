"""
@author: Gonghf
@date: 2025/12/10
@description: 
"""
import asyncio

from elasticsearch import Elasticsearch
from Event import *
class HistoryIndexManager:

    def __init__(self):

        try:
            self.client = Elasticsearch(hosts=es_url, basic_auth=(es_usr, es_pwd), max_retries=3, verify_certs=False)
        except Exception as e:
            logger.error(f"ES连接失败，错误原因：{e}")

        if self.client.ping():
            logger.info("ES连接成功!")

        self.child_index_name = "chat_index_child"
        self.index_name = "chat_index"

    def create_child(self):

        dim = 2560
        settings = {
            "analysis": {"analyzer": {"default": {"type": "standard"}}},
            "similarity": {
                "custom_bm25": {
                    "type": "BM25",
                    "k1": 2.0,
                    "b": 0.75
                }
            },
        }
        mapping = {
            "properties": {
                "child_chat_id": {"type": "keyword"},
                "next_chat_id": {"type": "keyword"},
                "chat_id": {"type": "keyword"},
                "chat_content": {
                    "type": "nested",  # 使用nested类型存储对象数组
                    "properties": {
                        "role": {"type": "keyword"},  # "user" 或 "assistant"
                        "content": {"type": "text"}  # 对话内容
                    }
                },
                "user_content_vector": {"type": "dense_vector", "dims": dim},
                "assistant_content_vector": {"type": "dense_vector", "dims": dim}
            }
        }

        if not self.client.indices.exists(index=self.child_index_name):
            try:
                response = self.client.indices.create(index=self.child_index_name, settings=settings, mappings=mapping)
                logger.info(f"创建子对话索引成功: {response}")
            except Exception as e:
                logger.error(f"创建子对话索引失败: {e}")



    def insert_child(self, chunks, id:str):


        for i, chunk in enumerate(chunks):

            child_chat_id = str(int(id) + i)
            next_chat_id = str(int(id) + i + 1)
            chat_id = id

            conversation_str = "\n".join([f"{c.role}:{c.content}" for c in chunk])

            prompt = f"""你的任务是从对话中提取用户和助手的核心观点。  

抽象要求：
1. 每个观点应是经过概括的核心立场，剥离具体细节和例证
2. 保留涉及到的关键 人、事、物。
3. 用简洁的语言表述本质主张（建议15-30字）
4. 避免技术细节、具体示例和流程描述
5. 聚焦“主张什么”而非“如何实现”

请以严格 JSON 格式返回：  
{{
  "user_viewpoint": "用户观点概括",
  "assistant_viewpoint": "助手观点概括"
}}

对话内容：  
{conversation_str}"""

            try:

                infos = get_qwen_flash_answer(prompt)
                infos = json.loads(infos)

                user_embedding = get_qwen_embedding(infos['user_viewpoint'])[0]
                assistant_embedding = get_qwen_embedding(infos['assistant_viewpoint'])[0]


            except Exception as e:

                logger.error(f"切片向量化出错：{e}")
                continue

            try:

                doc = {"child_chat_id": child_chat_id,
                       "next_chat_id": next_chat_id,
                       "chat_id": chat_id,
                       "chat_content": [{"role":c.role,"content":c.content} for c in chunk],
                       "user_content_vector": user_embedding,
                       "assistant_content_vector": assistant_embedding
                       }

                response = self.client.index(
                    index=self.child_index_name,
                    id = child_chat_id,
                    document = doc
                )

                if response['result'] in ['created', 'updated']:
                    logger.info(f"成功插入文档: {child_chat_id}")
                else:
                    logger.error(f"插入失败: {response}")
            except Exception as e:
                logger.error(f"插入对话子索引失败：{e}")

    def delete_child(self):

        if self.client.indices.exists(index=self.child_index_name):
            try:
                self.client.indices.delete(index=self.child_index_name)
            except Exception as e:
                logger.error(f"删除子对话索引失败：{e}")

    def delete(self):

        if self.client.indices.exists(index=self.index_name):
            try:
                self.client.indices.delete(index=self.index_name)
            except Exception as e:
                logger.error(f"删除子对话索引失败：{e}")

    def create(self):

        dim = 2560

        settings = {
            "analysis": {"analyzer": {"default": {"type": "standard"}}},
            "similarity": {
                "custom_bm25": {
                    "type": "BM25",
                    "k1": 2.0,
                    "b": 0.75
                }
            },
        }
        mapping = {
            "properties": {
                "chat_id": {"type": "keyword"},
                "summary_content":{"type":"text"},
                "summary_vector": {"type": "dense_vector", "dims": dim}
            }
        }
        if not self.client.indices.exists(index=self.index_name):

            try:

                response = self.client.indices.create(index=self.index_name, settings=settings, mappings=mapping)
                logger.info(f"创建对话主索引成功:{response}")

            except Exception as e:
                logger.error(f"创建对话主索引失败:{e}")

    def insert(self, id, event:Event):

        status_vector = get_qwen_embedding(event.history)[0]

        doc = {
            "chat_id": id,
            "summary_content": event.history,
            "summary_vector": status_vector
        }

        response = self.client.index(
            index=self.index_name,
            id=id,
            document=doc
        )

        if response['result'] in ['created', 'updated']:
            logger.info(f"成功插入对话主索引文档: {id}")
            return True
        else:
            logger.error(f"插入对话主索引文档失败: {response}")
            return False

    def handle_event(self, chunks, event, event_id):

        self.insert(event_id, event)

        self.insert_child(id=event_id, chunks=chunks)

    def search_child_chat(self, query):
        query_vector = get_qwen_embedding(query)[0]

        # 2. 构建向量相似度查询DSL
        search_query = {
            "size": 10,
            "query": {
                "script_score": {
                    "query": {"match_all": {}},  # 匹配所有文档
                    "script": {
                        "source": """
                            double score1 = cosineSimilarity(params.query_vector, 'user_content_vector');
                            double score2 = cosineSimilarity(params.query_vector, 'assistant_content_vector');
                            // 将余弦相似度从[-1,1]映射到[0,1]或直接使用
                            // 可以根据需要调整权重或添加其他评分因素
                            return score1 * 0.6 + score2 *0.4;
                        """,
                        "params": {
                            "query_vector": query_vector
                        }
                    }
                }
            },
            "sort": [
                {"_score": {"order": "desc"}}  # 按相似度分数降序排序
            ]
        }

        response = self.client.search(index=self.child_index_name, body=search_query)
        hits = response.get('hits', {}).get('hits', [])
        results = []
        for hit in hits:
            score = hit.get('_score', 0.0)

            # 过滤低于阈值的結果
            if score < 0.6:
                continue

            source = hit.get('_source', {})
            result = {
                "score": float(score),  # 转换为Python float类型
                "child_chat_id": source.get("child_chat_id"),
                "next_chat_id": source.get("next_chat_id"),
                "chat_id": source.get("chat_id"),
                "content": source.get("chat_content")
            }
            results.append(result)
        return results

async def main():
    manager = HistoryIndexManager()
    # results = manager.search_child_chat(query="RAG检索")
    # print(results)
    # manager.delete()
    # manager.delete_child()
    # manager.create()
    # manager.create_child()

    # async def create_event3():
    #     from datetime import time
    #     context_manager2 = Context()
    #
    #     message = SingleContext(create_time=datetime(2025, 11, 28, 20, 15, 30), content="小酷，我下个月想去旅行",
    #                             role="user")
    #     await context_manager2.append_context(message)
    #     print(context_manager2)
    #
    #     message = SingleContext(create_time=datetime(2025, 11, 28, 20, 15, 35),
    #                             content="听起来很棒！主人有想好去哪里吗？", role="assistant")
    #     await context_manager2.append_context(message=message)
    #
    #     # 较长时间间隔，用户在思考
    #     message = SingleContext(create_time=datetime(2025, 11, 28, 20, 17, 10),
    #                             content="还没决定，可能在云南和四川之间选择", role="user")
    #     await context_manager2.append_context(message=message)
    #
    #     message = SingleContext(create_time=datetime(2025, 11, 28, 20, 17, 15),
    #                             content="两个地方都很美呢。云南有丽江大理，四川有九寨沟成都",
    #                             role="assistant")
    #     await context_manager2.append_context(message=message)
    #
    #     message = SingleContext(create_time=datetime(2025, 11, 28, 20, 18, 23),
    #                             content="[背景]峨眉山推出凭持有峨眉山股票可以免门票游览的活动", role="user")
    #     await context_manager2.append_context(message=message)
    #
    #     message = SingleContext(create_time=datetime(2025, 11, 28, 20, 18, 45),
    #                             content="我更想去看看自然风光，哪个更好？", role="user")
    #     await context_manager2.append_context(message=message)
    #
    #     message = SingleContext(create_time=datetime(2025, 11, 28, 20, 18, 50),
    #                             content="如果主要是自然风光，四川的九寨沟和黄龙更壮观一些",
    #                             role="assistant")
    #     await context_manager2.append_context(message=message)
    #
    #     message = SingleContext(create_time=datetime(2025, 11, 28, 20, 20, 15),
    #                             content="好的，我研究一下四川的行程，谢谢", role="user")
    #     await context_manager2.append_context(message=message)
    #
    #     event = Event(name="旅行规划", summary="用户咨询旅行目的地，在云南和四川之间选择", history=context_manager2)
    #     return event
    # event =await create_event3()
    # id = generate_timestamp_key()
    # manager.handle_event(id, event)


if __name__=="__main__":
    asyncio.run(main())























