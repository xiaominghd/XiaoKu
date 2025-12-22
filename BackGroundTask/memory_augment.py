"""
@author: Gonghf
@date: 2025/12/7
@description: 
"""
from Ku import *

async def retrieve(agent:XiaoKu):

    if agent.events.current_event is not None:
        result = await agent.memory.get_event_memory(agent.events.current_event)

        if len(result) > 0:

            logger.info(f"检索之后得到的结果为：{result}")

            message = SingleContext(create_time=time.time(), role='outer', content=f"[历史]{result}")

            await agent.context.append_message(message)
            await agent.events.current_event.insert_message(message)

        return None



#
#
#
#
#
# async def main():







