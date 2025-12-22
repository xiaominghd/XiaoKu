"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
from datetime import datetime
from Event import *

class Context:

    def __init__(self, history:List=None, event_history:SingleContext=None, tail:List=None):

        # 一个上下文信息需要用三个部分进行维护
        if history is None:

            self.history = []
        else:
            self.history = history

        if event_history is None:

            self.event_history = SingleContext(create_time=datetime.now(),role="outer", content="")

        else:

            self.event_history = event_history

        if tail is None:

            self.tail = []

        else:

            self.tail = tail


        self.lock = asyncio.Lock()


    async def append_message(self, context:SingleContext):

        async with self.lock:

            self.tail.append(context)  # 同步进行内容新增

    async def trans_event(self, pre_event:Event, new_event:Event):

        async with self.lock:
            # 所有都再外面进行处理
            self.history.append(pre_event.event_history)
            self.event_history = new_event.event_history
            self.tail = pre_event.tail + new_event.tail

    async def update_summary(self, new_event:Event):
        async with self.lock:
            self.event_history = new_event.event_history
            self.tail = new_event.tail















