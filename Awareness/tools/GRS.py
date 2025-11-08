"""
@author: Gonghf
@date: 2025/11/8
@description: 使用大模型进行用户行为推荐
"""
from Memory.databases.mysql import *
from Memory.databases.es import *

from datetime import datetime


class RecommendSystem:

    def __init__(self):

        self.mysql = HistoryTableManager()
        self.es = HistoryIndexManager()

    def get_info(self):

        now = datetime.now()

        current_time = now.strftime('%Y年%m月%d日 %H时%M分%S秒')
        print(f"获取到当前时间为：{current_time}")

        current_id, current_state = self.mysql.select_current_state()
        print(f"获取到当前状态为：{current_state}")

        similar_id_list = self.es.search_similar_state(state=current_state)
        print(f"获取当前相似的事件为：{similar_id_list}")

        events_list = self.mysql.select_by_ids(similar_id_list)
        print(f"获取与当前相似的事件信息为：{events_list}")

        events = "\n".join([self.mysql.format_output(e) for e in events_list])

        return events





if __name__=="__main__":

    rs = RecommendSystem()
    print(rs.get_info())




