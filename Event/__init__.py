"""
@author: Gonghf
@date: 2025/12/1
@description: 
"""
import json

from Context import *
from base.api import *
class Event:

    def __init__(self, name:str=None, summary:str="", history:Context=None):
        if history is not None:
            self.history = history

            self.round = 0
            for c in self.history.cache:
                if c.role != "outer":  # 过滤掉外部信息
                    self.round += 1

        if history is None:
            self.history = Context()
            self.round = 0

        self.summary = summary
        self.name = name

    async def update_history(self, role, content):
        await self.history.append_context(message=SingleContext(create_time=datetime.now(), role=role, content=content))
        if role == "user" or role == "assistant":
            self.round += 1

    def update_summary(self):

        content = self.history.trans_cache2openai()

        prompt = f"""你是一个专业的对话总结助手，负责基于历史总结和最新对话内容，生成一份结构清晰、信息密度高的更新总结。这份总结将在后续对话中被检索使用，因此需要确保其准确性、完整性和可检索性。

请遵循以下要求生成总结：

**总结核心目标：**
- 提炼对话中的关键信息，便于后续快速回顾和上下文恢复
- 保持客观中立，仅基于对话内容进行归纳，不添加未提及的信息
- 突出对后续对话有持续影响的内容（如未解决的问题、待办事项、重要决策等）

**细节要素：**
1. **核心议题与问题**：明确对话讨论的主题、用户的核心需求或待解决的问题
2. **关键事实与数据**：涉及的具体信息、数字、时间线、引用来源等客观事实
3. **已采取的行动**：用户或助手已执行的操作、已完成的步骤、已提供的资源
4. **达成的决议与解决方案**：双方明确同意的结论、采纳的方案、确认的答案
5. **计划中的后续步骤**：约定的下一步行动、待办事项、预期交付成果及时间（如有）
6. **未解决或待定事项**：尚未明确的问题、需要后续跟进的点、存在的疑虑或分歧
7. **重要上下文与逻辑**：关键决策的理由、前提假设、约束条件、排除的选项及其原因

**输出格式要求：**
- 以连贯、简洁的段落形式输出总结内容，最多不超过两个段落。
- 语言保持专业、清晰，避免模糊表述（如“一些”“几个”）
- 仅输出总结内容，不包含任何额外解释、标题或注释

**历史总结：**
{self.summary}

**最新对话内容：**
{content}"""

        summary = get_qwen_max_answer(prompt)
        self.summary = summary

    async def get_key_point(self):
        # 根据历史信息总结一些
        infos = self.history.trans_cache2openai(load_outer=False)

        prompt = f"""你是一个聪明的助手，你的任务是根据用户和助手的对话，生成当前对话的2-3个主题。这些主题将会被用于在历史信息中检索具有相似主题的事件。
请你以json的形式进行返回，返回示例，除此之外不要返回其他信息:{{"result":["主题1","主题2"]}}
用户和助手的对话情况如下：
{infos}"""

        info = await get_qwen_max_answer_async(prompt)

        try:

            info = json.loads(info)
            return info["result"]

        except Exception as e:
            logger.error(f"获取关键信息失败：{e}")
            return []










