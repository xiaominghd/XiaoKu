"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
"""
@author: Gonghf
@date: 2025/10/31
@description: 
"""
import pymysql
from base.config import *
from typing import Optional
import re
from base.api import *


class HistoryTableManager:

    def __init__(self):
        self.db_config = mysql_config

        if not self.table_exists():

            self.create_table()


    def get_connection(self):

        return pymysql.connect(**self.db_config)

    def table_exists(self) -> bool:
        """检查表是否存在"""
        connection = self.get_connection()
        try:

            with connection.cursor() as cursor:
                sql = """
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
                """
                cursor.execute(sql, (self.db_config['database'], 'history_table'))
                result = cursor.fetchone()

                return result[0] > 0

        except Exception as e:
            print(f"❌ 检查表是否存在时出错: {e}")
            return False
        finally:
            connection.close()

    def create_table(self):

        connection = self.get_connection()
        try:  # 查找今天日内的聊天情况
            with connection.cursor() as cursor:
                create_table_sql = """
                        CREATE TABLE IF NOT EXISTS history_table (
                            id VARCHAR(16) PRIMARY KEY,
                            status VARCHAR(512),
                            event VARCHAR(512),
                            current TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        """
                cursor.execute(create_table_sql)
            connection.commit()
            print("成功已存在")
        except Exception as e:
            print(f"创建表时出错: {e}")
        finally:
            connection.close()





    async def insert_record(self, id, status, envent):

        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO history_table (id, status, event) VALUES (%s, %s, %s)"
                cursor.execute(sql, (id, status, envent))
            connection.commit()
            print(f"✅ 成功插入记录: {id}")
            return True
        except pymysql.Error as e:
            print(f"❌插入记录时出错：{e}")
            return False
        finally:
            connection.close()

    def select_by_id(self, id: str) -> Optional[dict]:
        """根据ID查询记录"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM history_table WHERE id = %s"
                cursor.execute(sql, (id,))
                result = cursor.fetchone()

                return result
        except Exception as e:
            print(f"查询记录时出错: {e}")
            return None
        finally:
            connection.close()

    def select_all(self):
        """查询所有记录"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM history_table"
                cursor.execute(sql)
                results = cursor.fetchall()
                return results
        except Exception as e:
            print(f"查询所有记录时出错: {e}")
            return []
        finally:
            connection.close()

    def delete_record(self, id: str):
        """删除记录"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                sql = "DELETE FROM history_table WHERE id = %s"
                cursor.execute(sql, (id,))
            connection.commit()
            print("记录删除成功")
            return True
        except Exception as e:
            print(f"删除记录时出错: {e}")
            return False
        finally:
            connection.close()

    def count_records(self):
        """统计记录数量"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                sql = "SELECT COUNT(*) as count FROM history_table"
                cursor.execute(sql)
                result = cursor.fetchone()
                return result['count']
        except Exception as e:
            print(f"统计记录时出错: {e}")
            return 0
        finally:
            connection.close()

    def select_current_state(self):

        # id是主键，通过id快速的找到用户最近的心理状态活动

        connection = self.get_connection()

        try:

            with connection.cursor() as cursor:

                sql = "select * from history_table order by id desc limit 1"
                cursor.execute(sql)
                result = cursor.fetchone()

                status = None
                current_id = None

                if result is not None:

                    status = result[1]
                    current_id = result[0]

            connection.close()
            return current_id, status


        except Exception as e:
            print(f"查询用户最新状态时出错:{e}")
            return None

    def select_by_ids(self, ids: list) -> list:
        """根据ID列表批量查询记录"""
        if not ids:
            return []

        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                placeholders = ', '.join(['%s'] * len(ids))
                sql = f"SELECT * FROM history_table WHERE id IN ({placeholders})"
                cursor.execute(sql, ids)
                results = cursor.fetchall()
                return results
        except Exception as e:
            print(f"批量查询记录时出错: {e}")
            return []
        finally:
            connection.close()

    @staticmethod
    def format_output(mysql_output):

        pattern = r'(\d{4})-(\d{2})-(\d{2}) (\d{2})'
        match = re.search(pattern, str(mysql_output[3]))

        if match:
            year, month, day, hour = match.groups()
            match = f"{year}年{month}月{day}日 {hour}时"  # 2025年11月04日 18时

        return f"时间：{match} 事件：{mysql_output[2]} 主人心情状态：{mysql_output[1]}"


if __name__=="__main__":

    db_manager = HistoryTableManager()

    record = db_manager.select_current_state()
    print(record)






