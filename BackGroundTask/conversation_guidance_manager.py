"""
@author: Gonghf
@date: 2025/12/6
@description: 
"""
from Event import *
from Ku import *

async def get_conversation_guidance(agent:XiaoKu):
    info = await agent.events.get_conversation_guide()

    if info is not None:
        logger.info(f"DeepSeek返回结果为：{info}")
        info = json.loads(info)
        agent.events.current_event.history.append_context(SingleContext(create_time=datetime.now(),role="user",
                                                                   content=f'[指引信息开始]当下回复：{info["回复"]}远期目标：{info["目标"]}世界知识：{info["注意"]}[指引信息结束]'))
        agent.events.current_event.history.append_context(SingleContext(create_time=datetime.now(), role="assistant", content="小酷了解了"))



