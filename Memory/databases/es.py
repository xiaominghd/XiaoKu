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
        # dim = 2560

    async def insert(self, id, status):

        # Todo 怎么去设计状态嵌入的方法
        status_vector = get_qwen_embedding(status)

        doc = {
            "memory_id": id,
            "memory": status,
            "memory_vector": status_vector
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




