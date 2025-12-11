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
            print(f"❌ 检查表是否存在时出错: {e}")
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
            print(f"创建成功，{self.child_table_name}已存在")
        except Exception as e:
            print(f"创建表时出错: {e}")
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
            child_id = id + str(i)  # 重命名变量避免覆盖参数

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
            create_time= event.history.cache[0].create_time
            end_time = event.history.cache[-1].create_time
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

    def insert_chef_table(self, event_id, event) -> bool:
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






async def main():
    manager = HistoryTableManager()


    async def create_event3():
        from datetime import time
        context_manager2 = Context()

        message = SingleContext(create_time=datetime(2025, 11, 28, 20, 15, 30), content="小酷，我下个月想去旅行",
                                role="user")
        await context_manager2.append_context(message)
        print(context_manager2)

        message = SingleContext(create_time=datetime(2025, 11, 28, 20, 15, 35),
                                content="听起来很棒！主人有想好去哪里吗？", role="assistant")
        await context_manager2.append_context(message=message)

        # 较长时间间隔，用户在思考
        message = SingleContext(create_time=datetime(2025, 11, 28, 20, 17, 10),
                                content="还没决定，可能在云南和四川之间选择", role="user")
        await context_manager2.append_context(message=message)

        message = SingleContext(create_time=datetime(2025, 11, 28, 20, 17, 15),
                                content="两个地方都很美呢。云南有丽江大理，四川有九寨沟成都",
                                role="assistant")
        await context_manager2.append_context(message=message)

        message = SingleContext(create_time=datetime(2025, 11, 28, 20, 18, 23),
                                content="[背景]峨眉山推出凭持有峨眉山股票可以免门票游览的活动", role="user")
        await context_manager2.append_context(message=message)

        message = SingleContext(create_time=datetime(2025, 11, 28, 20, 18, 45),
                                content="我更想去看看自然风光，哪个更好？", role="user")
        await context_manager2.append_context(message=message)

        message = SingleContext(create_time=datetime(2025, 11, 28, 20, 18, 50),
                                content="如果主要是自然风光，四川的九寨沟和黄龙更壮观一些",
                                role="assistant")
        await context_manager2.append_context(message=message)

        message = SingleContext(create_time=datetime(2025, 11, 28, 20, 20, 15),
                                content="好的，我研究一下四川的行程，谢谢", role="user")
        await context_manager2.append_context(message=message)

        event = Event(name="旅行规划", summary="用户咨询旅行目的地，在云南和四川之间选择", history=context_manager2)
        return event

    def split_event(event: Event):

        max_round = 6
        chunks = []
        mini_chunk = []
        i = 0
        conversations = event.history.cache
        while i < len(conversations) - 1:

            if conversations[i].role == "outer":

                i += 1
                continue

            else:

                if len(mini_chunk) < max_round and "[指引信息开始]" not in conversations[i].content:

                    mini_chunk.append(conversations[i])
                    i += 1

                else:

                    conversation_str = ""
                    for j, info in enumerate(mini_chunk):
                        conversation_str += f"第{j + 1}轮 {info.role}:{info.content}\n"
                    prompt = f"""你的任务是分析对话的连贯性，判断从第几轮开始对话主题或内容方向发生了变化。

分析步骤：
1. 仔细阅读整个对话，理解每轮对话的主题和内容
2. 判断相邻轮次之间的连贯性，是否延续了相同的话题或逻辑
3. 找出第一个出现主题转换或内容跳跃的轮次

判断标准：
- 如果所有对话内容保持一致性，没有切换，则返回-1
- 如果从第n轮开始与第n-1轮的内容有不同（话题转变、跳跃到无关内容等），则返回n

请只以JSON格式返回结果，不要包含任何解释说明。
返回格式：{{"result": 2}}

需要分析的对话内容：
{conversation_str}
"""

                    try:

                        answer = json.loads(get_qwen_flash_answer(prompt))["result"]

                        if answer == -1:
                            chunks.append(mini_chunk)
                        else:
                            chunks.append(mini_chunk[:answer - 1])
                            mini_chunk = mini_chunk[answer:]

                    except Exception as e:
                        mini_chunk = []
                        logger.error(f"切片出错：{e}")
                        continue

        if len(mini_chunk) != 0:
            chunks.append(mini_chunk)

        return chunks
    event =await create_event3()
    id = generate_timestamp_key()
    chunks = split_event(event)
    manager.insert_child(chunks,id)


if __name__=="__main__":
    asyncio.run(main())










