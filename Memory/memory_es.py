"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from elasticsearch import Elasticsearch
from Event import *
import warnings
warnings.filterwarnings("ignore")

class HistoryIndexManager:

    def __init__(self):

        try:
            self.client = Elasticsearch(hosts=es_url, basic_auth=(es_usr, es_pwd), max_retries=3, verify_certs=False)
        except Exception as e:
            logger.error(f"ES连接失败，错误原因：{e}")

        if self.client.ping():
            logger.info("ES连接成功!")


        self.index = r"history_v1"
        self.create()


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
            "properties":
                {
                    "memory_id":{"type":"keyword"},
                    "summary_vector":{"type":"dense_vector","dims":dim}
                }
        }

        if not self.client.indices.exists(index=self.index):  # 如果不存在，则创建
            try:
                response = self.client.indices.create(index=self.index, settings=settings, mappings=mapping)
                print(f"成功创建索引:{self.index}, 返回信息为：{response}")
            except Exception as e:
                print(f"创建索引失败：{e}")

    async def insert(self, id, event:Event):

        # Todo 怎么去设计状态嵌入的方法
        status_vector = get_qwen_embedding(event.summary)[0]

        doc = {
            "memory_id": id,
            "summary_vector": status_vector
        }

        response = self.client.index(
            index=self.index,
            id=id,
            document=doc
        )

        if response['result'] in ['created', 'updated']:
            print(f"✅ 成功插入文档: {id}")
            return True
        else:
            print(f"❌ 插入失败: {response}")
            return False

    def delete_index(self):

        if self.client.indices.exists(index=self.index):
            try:
                response = self.client.indices.delete(index=self.index)
                print(f"成功删除索引:{self.index}")
            except Exception as e:
                print(f"删除索引出现错误：{e}")