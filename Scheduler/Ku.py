"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
from Tool.manager import ToolManager
from typing import Dict
from Awareness.awareness_handler import *
from Memory.memory_handler import KuMemory
from Tool.Agents.awareness import *
from cozepy import  ChatEventType
from Events.EventManager import *
import random

class SystemPrompt:

    def __init__(self):

        self.role = """你叫小酷，你是由主人创建的一个智能体。你的任务是围绕主人当前的讨论话题，帮助主人解决问题，并且在沟通的过程中能够让主人高兴。
你具有心理学知识，能够自主的分析主人的心情、情感变化等，并对聊天进行规划。
请你注意输出的内容要以对话的口吻进行呈现，这要求你不要输出结构化和报告格式的内容。"""  # 小酷的基础角色
        self.tool = """"""
        self.user_profile = """主人是一个在重庆上班的上班族，今年28岁。从事程序员工作，平时喜欢了解一些科技类新闻。
周末喜欢和喜欢打麻将，美食，钓鱼和炒股等等。
主人最近上班比较忙碌，不仅在完成工作相关的内容，还在开发一个叫做小酷的智能聊天机器人。"""
        self.history = """"""

        self.recommend = r""""""
        self.bg = r""""""

    def init_tool_prompt(self, tools_list):
        tool_prompt = r"""你会使用工具。仅当主人的对话当中明确的提及工具调用的时候才能够调用工具
<TOOL>
如果你要调用工具，请直接返回JSON格式的响应，包含需要调用的工具名称和参数，不要返回其他任何信息。
格式：{"tool": "tool_name", "arguments": {"content": "搜索内容"}"""
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in tools_list
        ])

        self.tool = tool_prompt.replace("<TOOL>", tools_description)

    def init_history_prompt(self, history):

        if len(history) != 0:

            self.history = f"""在当前对话之前，小酷和主人进行了多轮的对话，历史对话的总结如下：
{history}
"""

    def init_recommend(self, recommend):

        self.recommend = f"""你需要根据用户当前的对话，引导用户讨论话题：{recommend}。
需要注意这个过程要保证用户对话的连贯性，除非用户提及，不要随机切换话题。"""

    def system_prompt_str(self): # 以字符串的形式返回系统提示词

        prompt = f"""# 角色
{self.role}
# 历史信息
{self.history}
# 聊天话题
{self.recommend}
# 聊天话题相关的背景
当涉及到不知道知识的时候，优先选择话题背景相关的内容进行回答。如果不存在，再考虑调用工具。
{self.bg}
"""
        return prompt


class XiaoKu:

    def __init__(self, tool:ToolManager, reply:MessageBank, feeling:KuFeeling, memory:KuMemory, events:EventBank=None):

        self.tool = tool
        self.reply = reply
        self.feeling = feeling
        self.memory = memory
        self.events = events

        self.round = 0
        self.system_prompt = SystemPrompt()  # 创建一个system_prompt

    def init_agent(self):

        tools_list = self.tool.get_tool_description()

        self.system_prompt.init_tool_prompt(tools_list)
        self.system_prompt.recommend = self.events.current_event.name
        self.system_prompt.bg = self.events.current_event.back_ground


    def init_task(self):

        if self.events.current_event is not None:
            self.system_prompt.current = f"话题名称：{self.events.current_event.name} \n 话题背景知识：{self.events.current_event.back_ground}"

    def init_system_prompt_with_plan(self, current, plan):
        self.system_prompt.init_recommend(recommend=f"现在是：{current} {plan}")


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

        new_msg = Msg(role="user", content=message, is_send=True)
        self.reply.message_list_dict["is_send"].append(new_msg)  # 将当前事件插入到回复列表当中

        for m in self.reply.message_list_dict["is_send"]:
            print(f"{m.role}:{m.content}")

        self.round += 1

        self.events.check_current_conversation(conversations=[new_msg])  # 确定当前话题
        self.events.current_event.history.append(new_msg)  # 更新事件列表

        flag = random.randint(1, 2)

        if flag == 2:
            print("使用主动询问逻辑")
            await self.ask()
        else:
            print("使用被动响应逻辑")
            await self.response()

    async def response(self):

        self.init_agent()  # 需要获取当前的话题以及背景
        messages = ([{"role": "system","content": self.system_prompt.system_prompt_str()}]
                    + [{"role": info.role, "content": info.content} for info in self.reply.message_list_dict["is_send"]])
        print(messages)

        response = get_deepseek_answer(messages)

        if self._is_tool_call(response):
            # 提取工具调用信息
            tool_call = self._parse_tool_call(response)
            if tool_call:
                # 调用工具
                tool_results = self.tool.call_tool(
                    tool_call["tool"],
                    tool_call["arguments"]
                )

                if isinstance(tool_results, str):

                    response = f"抱歉主人，小酷没有找到可执行的工具呢"

                    self.reply.append(Msg(role='assistant', content=response, is_send=False))
                    self.events.current_event.history.append(Msg(role='assistant', content=response, is_send=False))

                else:

                    try:

                        msg = ""
                        for event in tool_results:
                            if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                                msg += event.message.content
                                if event.message.content in "。！" and event.message.content!="\n":

                                    self.reply.append(Msg(role='assistant', content=msg, is_send=False))
                                    self.events.current_event.history.append(Msg(role='assistant', content=msg, is_send=False))
                                    msg = ""
                        if len(msg) != 0:

                            self.reply.append(Msg(role='assistant', content=msg, is_send=False))
                            self.events.current_event.history.append(Msg(role='assistant', content=msg, is_send=False))
                            self.reply.append(Msg(role='assistant', content="这是小酷知道的所有内容了", is_send=False))
                            self.events.current_event.history.append(Msg(role='assistant', content="这是小酷知道的所有内容了", is_send=False))

                    except Exception as e:
                        response  = f"哎呀，小酷在执行工具的时候出错了呢，出错原因：{e}"
                        self.reply.append(Msg(role='assistant', content=response, is_send=False))
                        self.events.current_event.history.append(Msg(role='assistant', content=response, is_send=False))

        else:
            self.reply.append(Msg(role='assistant', content=response, is_send=False))
            self.events.current_event.history.append(Msg(role='assistant', content=response, is_send=False))

    async def ask(self):

        try:
            contents = await self.events.generate_conversation()
            for content in contents:
                self.reply.append(Msg(role='assistant', content=content, is_send=False))
                self.events.current_event.history.append(Msg(role='assistant', content=content, is_send=False))

        except Exception as e:

            await self.response()
            print(f"主动问询时出错：{e}")


async def main():
    reply = MessageBank()
    tools = ToolManager()
    memory = KuMemory()
    feeling = KuFeeling(reply=reply)

    agent = XiaoKu(tools, reply, feeling, memory)
    await agent.chat(message="你好呀")

if __name__=="__main__":
    asyncio.run(main())








