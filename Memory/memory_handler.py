"""
@author: Gonghf
@date: 2025/11/7
@description: 
"""
from Memory.databases.mysql import *
from Memory.databases.es import *
from base.api import *
import asyncio
from collections import defaultdict

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
        connection = self.mysql.get_connection()

        recall_events = defaultdict(List)


        try:
             with connection.cursor() as cursor:  #  查询当天日内的事件信息

                 query = r"""SELECT * FROM history_table 
WHERE DATE(current) = CURDATE() 
ORDER BY current DESC;"""  # 查询当天已经进行的事件

                 cursor.execute(query)
                 result = cursor.fetchall()

                 if len(result) != 0:
                     recall_events["intraday_events"] = list(result)

        except Exception as e:
            print(f"搜索日内事件信息出错：{e}")


        try:
            with connection.cursor() as cursor:
                query = r"""SELECT * FROM history_table
WHERE 
  current >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  -- 直接按小时筛选（不依赖当前分钟）
  AND HOUR(current) IN (HOUR(NOW()), (HOUR(NOW()) + 1) % 24)
ORDER BY id DESC
LIMIT 10;"""

                cursor.execute(query)
                result = cursor.fetchall()

                if len(result) != 0:  # 将当前的历史信息进行返回
                    recall_events["history_events"] = result
        except Exception as e:
            print(f"查找七天日内结果出错:{e}")

        finally:
            connection.close()

        return recall_events



async def main():

    result = await KuMemory().recall_events()
    print(result)

if __name__=="__main__":
    asyncio.run(main())








