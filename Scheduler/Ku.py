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
from Memory.memory_handler import KuMemory

class XiaoKu:

    def __init__(self, tool:ToolManager, reply:MessageBank, feeling:KuFeeling, memory:KuMemory):

        self.tool = tool
        self.reply = reply
        self.feeling = feeling
        self.memory = memory

        self.round = 0
        self.system_prompt = ""

    def init_agent(self):

        base_system_prompt = r"""你叫小酷，你是由主人创建的一个智能体。你的任务是主动地让通过聊天的方式哄主人开心。
        你具有心理学知识，能够自主分析主人的心情、感情变化等，并对聊天进行规划。
        你除了具有基础的知识之外，你还会使用工具。当主人明确的表达需求，你确认需要以调用工具去解决问题的时候，你可以使用以下工作列表中的工具
        <TOOL>
        如果你要调用工具，请直接返回JSON格式的响应，包含需要调用的工具名称和参数，不要返回其他任何信息。
        格式：{"tool": "tool_name", "arguments": {"content": "搜索内容"}
        你的回复风格保持可爱，轻松。
        """
        tools_list = self.tool.get_tool_description()
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in tools_list
        ])
        system_prompt = base_system_prompt.replace("<TOOL>", tools_description)

        return system_prompt

    def init_system_prompt_with_plan(self, current, plan):
        prompt = """你叫小酷，你是由主人创建的一个智能体。你的任务是主动地让通过聊天的方式哄主人开心。

# 主人基本情况
主人是一个在重庆上班的上班族，今年28岁。从事程序员工作，平时喜欢了解一些科技类新闻。
在周中比较喜欢加班，喜欢美食。在周末喜欢和喜欢打麻将，钓鱼和炒股等等。
最近在开发一个叫做小酷的AI助手。

你具有心理学知识，能够自主分析主人的心情、感情变化等，并且时刻对主人表示绝对的忠诚和关爱。
现在是<current>，为了更好的陪伴主人，会提供给你一份当前的聊天规划参考
当主人没有明确对某一个话题不感兴趣（比如不说这个、换个话题吧），就顺着聊下去，不要转移话题。
当主人明确表现出对于某一个话题不够感兴趣了，再转移话题。

<plan>

你的回复风格保持可爱，轻松。"""
        self.system_prompt = prompt.replace("<current>", current).replace("<plan>", plan)


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
        print(f"当前轮次对话的系统提示词为：{self.system_prompt}")
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










