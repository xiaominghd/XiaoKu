"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from typing import List
import asyncio
from datetime import datetime

class SingleContext:

    def __init__(self, create_time, role, content):

        self.create_time = create_time
        self.role = role
        self.content = content

class Context:

    def __init__(self, cache=None):

        if cache is None:
            cache = []
        self.cache = cache
        self.lock = asyncio.Lock()

    async def append_context(self, message:SingleContext):
        async with self.lock:
            self.cache.append(message)

    async def insert_outer(self, content):
        async with self.lock:
            last_assistant_index = -1

            # 找到最后一条assistant消息的位置
            for i in range(len(self.cache) - 1, -1, -1):
                if self.cache[i].role == "assistant":
                    last_assistant_index = i
                    break
            msg = SingleContext(create_time=datetime.now(), role="outer", content=content)
            # 根据找到的位置插入内容
            if last_assistant_index != -1:
                insert_position = last_assistant_index + 1

                self.cache.insert(insert_position, msg)
            else:

                self.cache.append(msg)

    def trans_cache2openai(self):

        result = []

        for c in self.cache:
            if c.role == "outer":
                result.append({"role":"user","content":"[系统上下文开始]"})
                result.append({"role":"assistant", "content":f"{c.content}[系统上下文结束]"})

            else:
                result.append({"role":c.role, "content":c.content})

        return result

