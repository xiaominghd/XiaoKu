"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
"""
@author: Gonghf
@date: 2025/11/3
@description: 
"""
import warnings
warnings.filterwarnings("ignore")
from base.api import *

from elasticsearch import Elasticsearch

class HistoryIndexManager:

    def __init__(self):

        try:
            self.client = Elasticsearch(hosts=es_url, basic_auth=(es_usr, es_pwd), max_retries=3, verify_certs=False)
            print("ES连接成功")
        except Exception as e:
            print(f"ES连接失败，错误原因：{e}")

        self.index = r"history"
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
                    "status":{"type":"text", "similarity":"custom_bm25"},
                    "memory_id":{"type":"keyword"},
                    "status_vector":{"type":"dense_vector","dims":dim}
                }
        }

        if not self.client.indices.exists(index=self.index):  # 如果不存在，则创建
            try:
                response = self.client.indices.create(index=self.index, settings=settings, mappings=mapping)
                print(f"成功创建索引:{self.index}, 返回信息为：{response}")
            except Exception as e:
                print(f"创建索引失败：{e}")

    async def insert(self, id, status):

        # Todo 怎么去设计状态嵌入的方法
        status_vector = get_qwen_embedding(status)

        doc = {
            "memory_id": id,
            "status": status,
            "status_vector": status_vector
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

    def search_similar_state(self, state):

        query_vector = get_qwen_embedding(state)

        query_body = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'status_vector') + 1",  # 使用变量label_col
                    "params": {"query_vector": query_vector}
                }
            }
        }
        try:
            response = self.client.search(index=self.index, query=query_body, size=4)
            result = []


            for hit in response['hits']['hits']:

                if hit['_score'] > 1.5 :  # 需要排除当前的事件

                    result.append(hit['_source']['memory_id'])

            return result

        except Exception as e:
            print(f"查询ES相关事件发生错误：{e}")
            return []

    def delete_index(self):

        if self.client.indices.exists(index=self.index):
            try:
                response = self.client.indices.delete(index=self.index)
                print(f"成功删除索引:{self.index}")
            except Exception as e:
                print(f"删除索引出现错误：{e}")



if __name__=="__main__":

    history = HistoryIndexManager()
    # history.delete_index()
    print(history.search_similar_state(state="心情不错"))






