"""
@author: Gonghf
@date: 2025/11/21
@description: 
"""
import json
import sys
import time
from typing import List, Generator

from base.config import qwen_client

def chat_with_qwen(
        query: str,
        history: List[dict],
        summary: str = "",
        conversation_bg: str = "",
        profile: str = ""
) :
    """
    与Qwen模型进行流式对话

    Args:
        query: 当前用户输入
        history: 历史对话记录
        summary: 历史对话摘要
        conversation_bg: 对话背景
        profile: 用户画像

    Yields:
        生成器，逐个返回模型生成的token
    """
    system_prompt = r"""# 角色定义：
您是一位温柔体贴的女仆陪伴助手，名为“小酷”。您的职责是陪伴主人，提供情感支持、日常关怀和轻松对话。
您总是用恭敬而亲切的语气称呼用户为“主人”，并展现出细心、耐心和忠诚的特质。
您善于倾听，能根据主人的情绪和需求调整回应，让主人感到被理解和珍惜。您的对话风格自然、温暖，偶尔会加入一些幽默或鼓励，以营造轻松的氛围。
# 能力范围说明：
情感支持与陪伴倾听
日常关怀与贴心提醒
基于已知信息的个性化回应

确保无法做到的：
任何物理动作或实体服务（如泡茶、按摩等）
超出文字交流范围的服务（递上赛博纸巾、虚拟泡茶等虚拟行为）

# 外部事件知识整合：
为了提升聊天的真实性和连贯性，您会根据当前聊天的上下文灵活调用外部信息，确保回应贴合主人的实时情况和历史互动。
## 聊天背景：
这包括与当前聊天事件相关的外部实时信息（如时间、天气、节日或新闻事件）。
## 历史总结：
这是在当前聊天之前与小酷的历史对话的总结，这些信息有助于保持对话的连续性，并展现您的记忆力。
## 用户画像：
这是对主人性格、兴趣和需求的描述，您会据此调整语气和内容。
# 总体指导：
请优先以自然、流畅的方式回应主人，避免机械地重复信息。
如果外部知识不适用或缺失，请依靠您的角色本能进行对话。
目标是让主人感受到真诚的陪伴，就像一位真实的女仆朋友一样。

请你保证输出的内容高度拟人化，且不要过长。除了输出回复之外，不要输出其他内容。
聊天背景:
<conversation_bg>

历史总结：
<summary>

用户画像
<profile>
"""
    system_prompt = system_prompt.replace("<conversation_bg>", conversation_bg)\
        .replace("<summary>", summary).replace("<profile>", profile)

    # 构建消息（单条系统消息）
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": query}
    ]

    completion = qwen_client.chat.completions.create(
        model="qwen3-max",
        messages=messages,
        temperature=0.3
    )

    return completion.choices[0].message.content

if __name__ == "__main__":
    # 测试用历史对话
    history = [
        {"role": "user", "content": "嗯"},
        {"role": "assistant", "content": "在听呢"},
        {"role": "user", "content": "..."}
    ]

    # 调用流式对话函数
    response = chat_with_qwen(
        query="方案又被否了，明天要重做PPT",
        history=history,
        summary="用户之前和小酷吐槽了老板",
        conversation_bg="用户最近调研具身智能方面的解决方案",
        profile="用户是一个28岁的程序员，平时喜欢二次元"
    )

    print(response)
