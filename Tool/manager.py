"""
@author: Gonghf
@date: 2025/11/6
@description: 通过传入历史对话信息进行工具搜索
"""
from Tool.Agents.news_search import NewsSearchAgent
from typing import Dict
import asyncio

class ToolManager:

    def __init__(self):

        self.tools = {
            'news_search':NewsSearchAgent()
        }

    def get_tool_description(self):

        return [
            {
                "name":tool.name,
                "description":tool.describe,
                "parameters":
                    {
                        "type":"object",
                        "properties":{
                            "content":
                                {
                                    "type":"string",
                                    "description":tool.input
                                }
                        },
                        "required":["content"]
                    }
            }
            for tool in self.tools.values()
        ]

    async def call_tool(self, tool_name:str, arguments:Dict):
        if tool_name not in self.tools:
            return f"未知工具：{tool_name}"

        tool = self.tools[tool_name]

        await tool.execute(arguments["content"])

        max_wait = 120
        waited = 0
        while not tool.status.startswith("执行完成") and waited < max_wait:
            if tool.status.startswith("执行错误"):
                return f"工具执行错误: {tool.status}"
            await asyncio.sleep(0.5)
            waited += 1

        if tool.status.startswith("执行完成"):
            return tool.result
        else:
            return "小酷在执行这个任务的时候花费了太多的时间呢~"

async def main():

    manager = ToolManager()

    result = await manager.call_tool(tool_name="news_search",arguments={'content':"国内热点新闻"})
    print(result)


if __name__=="__main__":
    asyncio.run(main())