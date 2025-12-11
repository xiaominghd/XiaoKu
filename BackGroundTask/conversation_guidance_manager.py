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
        return SingleContext(create_time=datetime.now(),role="user",content=f'[指引信息开始]对当前对话的评价：{info["需求"]}远期目标：{info["目标"]}[指引信息结束]')

    return None


