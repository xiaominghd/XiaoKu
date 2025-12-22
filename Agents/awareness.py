"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
import asyncio
import json
from typing import Optional
from Memory.memory_mysql_v1 import *
from Event.EventManager import *
from Event import *
from Ku import *



class AwareAgentWork:

    def __init__(self):

        self.workflow_id = "7579157828373168154"

    def execute(self, content):
        workflow = coze.workflows.runs.create(workflow_id=self.workflow_id, parameters=content)
        return json.loads(workflow.data)["output"]

    @staticmethod
    def get_recent_conversation():

        events = HistoryTableManager().get_recent_contents(minutes=60)

        if len(events) == 0:
            return None
        else:
            conversations = events[0][1]
            results = []
            for conversation in json.loads(conversations):
                results.append(SingleContext(create_time=datetime.now(), role=conversation['role'], content=conversation['content']))

            return results



    async def get_info(self, agent:XiaoKu):

        user_profile = r"""用户是一个28岁的程序员，平时工作较为繁忙。
在周中平时换做一些好吃的，还喜欢打羽毛球。到了周末喜欢和朋友们一起打麻将和钓鱼等活动。最近在开发一个名叫小酷的AI助手"""

        recent_info = HistoryTableManager().select_recent_events()

        if recent_info is not None:
            recent_event = f"在{recent_info[5]}，事件{recent_info[2]}"
        else:
            recent_event = ""

        content = {"history":recent_event, "profile":user_profile}
        infos = self.execute(content)
        logger.info(infos)

        event_list = []
        first_bg = SingleContext(create_time=datetime.now(), role="outer", content="")
        for i, info in enumerate(infos):

            context = []

            bg = SingleContext(content=f"[背景]{info['reason']}", create_time=datetime.now(), role="outer")

            if i == 0:
                first_bg = bg

            context.append(bg)

            event_list.append(Event(name=info["name"], event_history=None,tail=context))


        agent.events.init_event_list(event_list)
        agent.context = Context(history=None, event_history=first_bg,tail=None)

        history = self.get_recent_conversation()
        if history is None:

            pass

        else:
            for h in history:
                await agent.events.current_event.insert_message(h)
                await agent.context.append_message(h)

        return agent



