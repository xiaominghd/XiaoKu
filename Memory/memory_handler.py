"""
@author: Gonghf
@date: 2025/11/7
@description: 
"""
from Memory.databases.mysql import *
from Memory.databases.es import *
from base.api import *

class KuMemory:

    def __init__(self):

        self.mysql = HistoryTableManager()
        self.es = HistoryIndexManager()

    async def insert_satus_summary(self, summary, status):

        id = generate_timestamp_key()

        try:

            await self.mysql.insert_record(id=id,status=status, envent=summary)

            await self.es.insert(id=id, status=status)

        except Exception as e:
            print(f"插入记忆事件发生错误：{e}")

    async def recall_events(self):

        # 召回历史信息，构建历史回忆
        cursor = self.mysql.get_connection().cursor()
        query = r"""SELECT * FROM history_table 
WHERE DATE(current) = CURDATE() 
ORDER BY current DESC;"""
        cursor.execute(query)








