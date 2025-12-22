"""
@author: Gonghf
@date: 2025/12/10
@description: 
"""
import asyncio
import pymysql
from base.api import *
from typing import Optional, Tuple

from Event import *

class HistoryTableManager:

    def __init__(self):
        self.db_config = mysql_config

        self.child_table_name = "chat_table_child"
        if not self.table_exists(self.child_table_name):
            self.create_child_table()

        self.table_name = "chat_table"
        if not self.table_exists(self.table_name):
            self.create_table()

    def get_connection(self):

        return pymysql.connect(**self.db_config)

    def table_exists(self, table_name) -> bool:
        """检查表是否存在"""
        connection = self.get_connection()
        try:

            with connection.cursor() as cursor:
                sql = """
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
                """
                cursor.execute(sql, (self.db_config['database'], table_name))
                result = cursor.fetchone()

                return result[0] > 0

        except Exception as e:
            logger.error(f"❌ 检查表是否存在时出错: {e}")
            return False
        finally:
            connection.close()

    def create_child_table(self):

        connection = self.get_connection()

        try:

            with connection.cursor() as cursor:

                sql = f"""create table if not exists {self.child_table_name}(
                id varchar(17) primary key,
                content json,
                create_time DATETIME,
                recent_update_time DATETIME,
                retrieve_num INT
                
)"""
                cursor.execute(sql)
            connection.commit()
            logger.info(f"创建成功，{self.child_table_name}已存在")
        except Exception as e:
            logger.info(f"创建表时出错: {e}")
        finally:
            connection.close()

    def create_table(self):

        connection = self.get_connection()
        try:  # 查找今天日内的聊天情况
            with connection.cursor() as cursor:
                create_table_sql = f"""
                        CREATE TABLE IF NOT EXISTS {self.table_name} (
                            id VARCHAR(16) PRIMARY KEY,
                            type enum("娱乐","工作","日常","健康","其他") NOT NULL,
                            summary TEXT,
                            round INT,
                            sentiment enum("积极","中性","消极"),
                            create_time DATETIME,
                            exist_minutes INT,
                            keywords JSON
                        )
                        """
                cursor.execute(create_table_sql)
            connection.commit()
            logger.info(f"创建成功，表{self.table_name}已存在")
        except Exception as e:
            logger.error(f"创建表时出错: {e}")
        finally:
            connection.close()

    def insert_child(self, chunks, id):
        connection = self.get_connection()

        for i, chunk in enumerate(chunks):
            child_id = str(int(id) + i)  # 重命名变量避免覆盖参数

            content = json.dumps([{'role': c.role, 'content': c.content} for c in chunk], ensure_ascii=False)
            create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            retrieve_num = 0

            # 使用参数化查询，这是更安全的方式
            sql = f"""INSERT INTO {self.child_table_name} (id, content, create_time, recent_update_time, retrieve_num)
                      VALUES (%s, %s, %s, %s, %s)"""

            try:
                with connection.cursor() as cursor:
                    # 传递参数元组
                    cursor.execute(sql, (child_id, content, create_time, create_time, retrieve_num))
                connection.commit()
                logger.info(f"✅ 成功插入记录: {child_id}")

            except pymysql.Error as e:
                logger.error(f"❌ 插入记录时出错: {e}")
                connection.rollback()

        connection.close()

    def update_child(self, child_ids):
        """
        批量更新多个子表记录

        Args:
            child_ids: 要更新的记录ID列表
        Returns:
            成功更新的记录数量
        """
        if not child_ids:
            return 0

        connection = self.get_connection()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        updated_count = 0

        try:
            with connection.cursor() as cursor:
                # 使用IN子句批量更新
                format_strings = ','.join(['%s'] * len(child_ids))
                sql = f"""UPDATE {self.child_table_name} 
                          SET recent_update_time = %s, 
                              retrieve_num = retrieve_num + 1
                          WHERE id IN ({format_strings})"""

                # 构造参数：当前时间 + 所有ID
                params = [current_time] + child_ids
                cursor.execute(sql, tuple(params))
                updated_count = cursor.rowcount

            connection.commit()
            logger.info(f"✅ 批量更新完成: 成功更新 {updated_count} 条记录")

        except pymysql.Error as e:
            logger.error(f"❌ 批量更新记录时出错: {e}")
            connection.rollback()
            updated_count = 0
        finally:
            connection.close()

        return updated_count

    @staticmethod
    def get_event_info(event:Event) -> Optional[Tuple[str, str, List[str]]]:
        """
        从事件中提取类型、情感和关键词

        Args:
            event: 事件对象

        Returns:
            元组 (事件类型, 情感态度, 关键词列表) 或 None
        """
        summary = event.event_history.content

        conversation = trans_messages2openai(event.tail)

        prompt = f"""你是一个聪明的助手，你的任务是从指定的事件信息中提取出以下信息。
# 事件类型(每一个事件只能属于以下五种类型之一：娱乐，工作，日常，健康，其他)
1、娱乐。如果用户讨论关于娱乐的事情，比如和朋友一起玩等轻松的话题，可以归为娱乐。
2、工作。如果用户讨论关于工作的事情，包括上班，学习等话题，可以归为工作。
3、日常。用户讨论的话题是日常的闲聊，比如询问天气，吃饭等每天都会发生的行为，则归为日常，
4、健康。用户讨论的关于身体健康或者是运动的话题。
5、其他。如果用户讨论的话题不明确属于上述几类事件类型中的任何一种，则分类为其他。
# 情感态度（每一个事件只能属于以下三种类型之一：积极，消极，中性）
1、积极。是指用户明确表达出了高兴，愉快的感情态度，有积极的情绪。
2、消极。是指用户明确表达出了讨厌，不喜欢等情感太多，有消极的情绪。
3、中性。用户并没有明确的情感变化。
# 关键词
请用1-2个词对事件整体信息进行总结，要求这个词能够反映用户的行为。
要求返回一个json数据，除此之外不要返回其他任何信息。
返回示例：{{"事件类型":"工作","情感态度":"中性","关键词":["吐槽工作"]}}
事件信息如下:
事件总结:
{summary}
用户和助手的对话：
{conversation}
"""
        try:
            answer = get_qwen_flash_answer(prompt)
            event_info = json.loads(answer)

            event_type = event_info.get("事件类型")
            sentiment = event_info.get("情感态度")
            keywords = event_info.get("关键词", [])

            # 验证必要字段
            if not all([event_type, sentiment]):
                logger.error("缺少必要的事件信息字段")
                return None

            return event_type, sentiment, keywords

        except json.JSONDecodeError as e:
            logger.error(f"解析JSON响应失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取事件详细信息出错: {e}")
            return None

    def prepare_event_data(self, event, id):
        try:
            # 获取事件基本信息
            event_info = self.get_event_info(event)

            if event_info is None:
                logger.info(f"获取事件基本信息出错")
                return None

            event_type, sentiment, keywords = event_info

            # 处理时间
            create_time= event.messages[0].create_time
            end_time = event.messages[-1].create_time
            # 计算持续时间

            def calculate_duration(start_time: datetime, end_time: datetime) -> int:

                duration = end_time - start_time
                return max(1, int(duration.total_seconds() / 60))  # 至少1分钟
            exist_minutes = calculate_duration(create_time, end_time)

            # 生成ID
            # 准备数据
            event_data = {
                'id': id,
                'type': event_type,
                'summary': event.history,
                'round': event.round,
                'sentiment': sentiment,
                'create_time': create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'exist_minutes': exist_minutes,
                'keywords': json.dumps(keywords, ensure_ascii=False)  # 确保正确的JSON格式
            }

            return event_data

        except Exception as e:
            logger.error(f"准备事件数据时出错: {e}")
            return None

    def insert_chef_table(self, event_id, event) -> bool:
        """
        将事件插入数据库

        Args:
            event: 事件对象

        Returns:
            插入是否成功
        """
        # 准备数据
        event_data = self.prepare_event_data(event=event, id=event_id)
        if event_data is None:
            print("无法准备事件数据，插入失败")
            return False

        # 构建SQL
        sql = f"""
        INSERT INTO  {self.table_name}
        (id, type, summary, round, sentiment, create_time, exist_minutes, keywords) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        # 参数
        params = (
            event_data['id'],
            event_data['type'],
            event_data['summary'],
            event_data['round'],
            event_data['sentiment'],
            event_data['create_time'],
            event_data['exist_minutes'],
            event_data['keywords']
        )

        # 执行插入
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
            connection.commit()
            print(f"✅ 成功插入记录: {event_data['id']}")
            return True

        except pymysql.Error as e:
            print(f"❌ 插入记录时出错: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()

    def insert_table(self, chunks, event, event_id):

        self.insert_child(chunks, event_id)  # 将chunk插入到子表中

        self.insert_chef_table(event_id, event)  # 将event插入到主表中

    def search_event_by_id(self, chat_id):

        sql = f"select * from {self.child_table_name} where id={chat_id}"
        connection = self.get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                connection.close()
                if result is not None:

                    return {'create_time':result[2], 'retrieve_time':result[4]}

                else:
                    return None
        except Exception as e:
            logger.error(f"检索特定事件失败，失败原因：{e}")
            connection.close()
            return None

    def select_recent_events(self):

        connection = self.get_connection()

        try:

            with connection.cursor() as cursor:

                sql = f"""SELECT * from {self.table_name} ORDER by create_time DESC limit 1"""

                cursor.execute(sql)

                result = cursor.fetchone()
                return result

        except Exception as e:
            print(f"查询记录时出错：{e}")
            return None
        finally:
            connection.close()

    def get_recent_contents(self, minutes=300):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # 方法1: 使用 NOW() 函数
                sql = f"""
                SELECT id, content, create_time 
                FROM {self.child_table_name}
                WHERE create_time > NOW() - INTERVAL {minutes} MINUTE
                ORDER BY id DESC
                """
                cursor.execute(sql)
                results = cursor.fetchall()
                return list(results)
        except Exception as e:
            print(f"查询时出错: {e}")
            return []
        finally:
            connection.close()

    def get_today_summaries(self):
        """
        获取今天创建的所有记录的summary
        """
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                # 方法1: 使用 DATE(create_time) = CURDATE()
                sql = f"""
                SELECT id, type, summary, create_time, sentiment
                FROM {self.table_name}
                WHERE DATE(create_time) = CURDATE()
                ORDER BY create_time DESC
                """
                cursor.execute(sql)
                results = cursor.fetchall()
                return results
        except Exception as e:
            logger.error(f"查询今天summary时出错: {e}")
            return []
        finally:
            connection.close()











async def main():
    manager = HistoryTableManager()
    previous_conversation = manager.get_recent_contents()
    print(previous_conversation)

if __name__=="__main__":
    asyncio.run(main())










