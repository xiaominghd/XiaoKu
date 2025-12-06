"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from Memory.memory_es import *
from Memory.memory_mysql import *
from Event import *

class MemoryBank:

    def __init__(self):

        self.mysql = HistoryTableManager()
        self.es = HistoryIndexManager()

    def insert_event(self, event:Event):

        if event.round > 5:  # 小于三十轮的对话根本不管

            event_id = generate_timestamp_key()
            self.mysql.insert_table(event_id, event)
            self.es.insert(event_id, event)
            return event

        else:
            return None







