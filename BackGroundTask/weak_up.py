"""
@author: Gonghf
@date: 2025/12/19
@description: 用户长时间没有回应主动进行回复实现唤醒。
"""
from base.api import *
from Context import *
from Ku import XiaoKu

async def weak_up_client(agent:XiaoKu):

    context = agent.context

    context_str = context.trans_cache2openai(load_outer=True)
    last_response_time = context.cache[-1].create_time  # 最后一次响应发生的时间
    time_stamp = datetime.now() - last_response_time  # 时间间隔

    prompt = f"""
**任务：生成用户唤醒话术**

**1. 任务目标**
分析用户与助手的历史对话，生成一段自然、贴切的话术，用以唤醒用户并继续对话。回复需在100字以内，语气与助手原有风格保持一致，，
且仅输出回复内容本身。

**2. 分析依据**
- 用户与助手上一次对话时间：{last_response_time}
- 当前时间：{datetime.now()}
- 历史对话内容：
{context_str}

请基于对话历史，从以下三个角度中选择**最合适的一项**作为回复重点，并自然融入话术中：

- **情绪与需求关注**：若助手此前可能忽略了用户的情绪或未充分回应其需求，应表达理解与关心，并尝试重新承接该需求。
- **话题延伸与引导**：若对话话题可能使用户失去兴趣，可基于原有内容提出一个相关且易展开的子话题，激发新的讨论点。
- **主动引导深入交流**：若对话中用户长期处于引导地位，助手应主动提出一个可深入探讨的方向，减轻用户主导负担。

**3. 回复要求**
- 保持口语化、亲切，贴近助手以往语气。
- 注意只返回一个角度的一项作为回复重点，不要返回三个角度。严格控制在100字以内，语句连贯。
- 不添加任何分析、说明或额外标注，不要显式的提及时间信息，仅输出生成的对话内容。

**请根据以上框架生成回复。**
"""
    info = await get_qwen_max_answer_async(prompt, enable_think=True)
    logger.info(f"发送提醒信息：{info}")
    context = SingleContext(create_time=datetime.now(), role="assistant", content=info)
    await agent.context.append_context(context)
    agent.reply.not_send.append(context)

    return info



