"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
from Tool.manager import ToolManager
from Scheduler import *
from typing import Optional, Dict
from base.api import *
import asyncio
from Awareness.awareness_handler import *

class XiaoKu:

    def __init__(self, tool:ToolManager, reply:MessageBank, feeling:KuFeeling):

        self.tool = tool
        self.reply = reply
        self.feeling = feeling
        self.round = 0
        self.system_prompt = ""

    def init_agent(self):

        system_prompt = """你叫小酷，你是由主人创建的一个智能体。你的任务是主动地让通过聊天的方式哄主人开心。

# 主人基本情况
主人是一个在重庆上班的上班族，今年28岁。从事程序员工作，平时喜欢了解一些科技类新闻。
在周中比较喜欢加班，喜欢美食。在周末喜欢和喜欢打麻将，钓鱼和炒股等等。
最近在开发一个叫做小酷的AI助手。

你具有心理学知识，能够自主分析主人的心情、感情变化等，并且时刻对主人表示绝对的忠诚和关爱。
现在是2025年11月8日，周六，为了更好的陪伴主人，会提供给你一份当前的聊天规划参考
当主人没有明确对某一个话题不感兴趣（比如不说这个、换个话题吧），就顺着聊下去，不要转移话题。
当主人明确表现出对于某一个话题不够感兴趣了，再转移话题。

以关心主人感冒恢复情况开启对话：“主人，下午听你说感冒了，现在有没有舒服点呀？有没有喝热水或者吃点感冒药缓解呀？”
待主人回应感冒状况后，衔接其近期感兴趣的美食话题（周四提及的黄焖鸡加食材计划）：“对啦，你之前说吃黄焖鸡想加金针菇和土豆，有没有试着做这个搭配呀？我可以帮你查一下黄焖鸡加金针菇土豆的具体做法哦～”
若主人对美食话题有互动，进一步延伸周末美食计划：“周末有没有打算再尝试其他好吃的？比如你喜欢的重庆本地美食？我可以帮你推荐几道适合周末做的简单家常菜～”
若主人未深入美食话题，则转向近期游戏兴趣点（周五提及的崩坏星穹铁道）：“对了，周五你说崩坏星穹铁道的奖励越来越多，今天有没有玩到什么有意思的剧情或者拿到好东西呀？”
待主人回应游戏内容后，可延伸游戏体验讨论：“你平时玩这款游戏喜欢刷副本还是看剧情呀？有没有什么角色是你特别想要的？”
最后结合周末爱好收尾：“今天是周六，有没有去钓鱼或者打麻将呀？有没有遇到什么好玩的小插曲分享一下？”

你的回复风格保持可爱，轻松。"""

        return system_prompt

    @staticmethod
    def _parse_tool_call(response: str) -> Optional[Dict]:
        """解析工具调用"""
        try:
            import json
            return json.loads(response)
        except:
            return None

    @staticmethod
    def _is_tool_call(response: str) -> bool:
        """判断大模型响应是否为工具调用"""
        return response.strip().startswith("{") and response.strip().endswith("}")

    async def chat(self, message:str):

        if self.round == 0:
            self.system_prompt = self.init_agent()

        self.round += 1
        self.reply.message_list_dict['send'].append(Msg(role='user', content=message, is_send=True))

        messages = [{"role": "system","content": self.system_prompt}] + [{"role": info.role, "content": info.content} for info in self.reply.message_list_dict["send"]]

        response = get_deepseek_answer(messages)


        if self._is_tool_call(response):
            # 提取工具调用信息
            tool_call = self._parse_tool_call(response)
            if tool_call:
                # 调用工具
                tool_result = await self.tool.call_tool(
                    tool_call["tool"],
                    tool_call["arguments"]
                )

                # 将工具结果返回给用户
                response = tool_result
            else:
                response = "抱歉主人，小酷已经很努力了但仍然还是无法完成这个任务."

        self.reply.append(Msg(role='assistant', content=response, is_send=False))



