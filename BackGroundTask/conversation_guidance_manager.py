"""
@author: Gonghf
@date: 2025/12/6
@description: 
"""
from Event import *
from Ku import *

async def get_conversation_guidance(agent:XiaoKu):



    if len(agent.context.tail) == 0 or agent.context.tail[-1].role == "outer":  # 防止没有消息的时候反复初始化outer
        return None

    info = await agent.events.get_conversation_guide()


    if info is not None:
        logger.info(f"Qwen思考之后返回结果为：{info}")
        info = json.loads(info)
        content = SingleContext(create_time=datetime.now(),role="outer",content=f'[背景]{info["目标"]}[背景]{info["评价"]}')
        await agent.context.append_message(content)

    return None


