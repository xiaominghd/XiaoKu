"""
@author: Gonghf
@date: 2025/11/30
@description: 
"""
import asyncio
import pymysql
from base.api import *
from typing import Optional, Tuple
from datetime import datetime, date
from typing import List


def calculate_duration(start_time: datetime, end_time: datetime) -> int:

    duration = end_time - start_time
    return max(1, int(duration.total_seconds() / 60))  # 至少1分钟


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
                cursor.execute(sql, (self.db_config['database'], 'history_table_v1'))
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
                        CREATE TABLE IF NOT EXISTS history_table_v1 (
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
            print("成功已存在")
        except Exception as e:
            print(f"创建表时出错: {e}")
        finally:
            connection.close()

    @staticmethod
    def get_event_info(event) -> Optional[Tuple[str, str, List[str]]]:
        """
        从事件中提取类型、情感和关键词

        Args:
            event: 事件对象

        Returns:
            元组 (事件类型, 情感态度, 关键词列表) 或 None
        """
        summary = event.summary
        conversation = event.history.trans_cache2openai()

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
                print("缺少必要的事件信息字段")
                return None

            return event_type, sentiment, keywords

        except json.JSONDecodeError as e:
            print(f"解析JSON响应失败: {e}")
            return None
        except Exception as e:
            print(f"获取事件详细信息出错: {e}")
            return None

    def prepare_event_data(self, event_id, event) -> Optional[dict]:

        try:
            # 获取事件基本信息
            event_info = self.get_event_info(event)
            if event_info is None:
                return None

            event_type, sentiment, keywords = event_info

            # 处理时间
            create_time= event.history.cache[0].create_time
            end_time = event.history.cache[-1].create_time
            # 计算持续时间
            exist_minutes = calculate_duration(create_time, end_time)

            # 生成ID
            # 准备数据
            event_data = {
                'id': event_id,
                'type': event_type,
                'summary': event.summary,
                'round': event.round,
                'sentiment': sentiment,
                'create_time': create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'exist_minutes': exist_minutes,
                'keywords': json.dumps(keywords, ensure_ascii=False)  # 确保正确的JSON格式
            }

            return event_data

        except Exception as e:
            print(f"准备事件数据时出错: {e}")
            return None

    def insert_table(self, event_id, event) -> bool:
        """
        将事件插入数据库

        Args:
            event: 事件对象

        Returns:
            插入是否成功
        """
        # 准备数据
        event_data = self.prepare_event_data(event_id, event)
        if event_data is None:
            print("无法准备事件数据，插入失败")
            return False

        # 构建SQL
        sql = """
        INSERT INTO history_table_v1 
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

    def select_recent_events(self):

        connection = self.get_connection()

        try:

            with connection.cursor() as cursor:

                sql = """SELECT * from history_table_v1 ORDER by create_time DESC limit 1"""

                cursor.execute(sql)

                result = cursor.fetchone()
                return result

        except Exception as e:
            print(f"查询记录时出错：{e}")
            return None
        finally:
            connection.close()
        

if __name__=="__main__":
    manager = HistoryTableManager()
    print(manager.select_recent_events())







