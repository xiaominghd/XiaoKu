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

        mysql_flag = await self.mysql.insert_record(id=id,status=status, envent=summary)
        es_flag = await self.es.insert(id=id, status=status)





