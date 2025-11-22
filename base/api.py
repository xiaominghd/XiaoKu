"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
from base.config import *
from cozepy import Coze, TokenAuth, Message
from cozepy import COZE_CN_BASE_URL
import os
from typing import List
import requests
import time
import json
import random
import string
from openai import OpenAI
from log.logger import get_logger

coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=COZE_CN_BASE_URL)
logger = get_logger()

def get_deepseek_answer(message:List):
    client = OpenAI(
        api_key=deepseek_api_key,
        base_url=deepseek_api_base)


    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=message,
        stream=False
    )

    return response.choices[0].message.content

def get_qwen_max_answer(query):  # 较小的模型，用于进行意图识别和提取参数

    completion = qwen_client.chat.completions.create(

        model="qwen-max",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query},
        ]
    )

    response = json.loads(completion.model_dump_json())['choices'][0]["message"]["content"]
    return response

def get_qwen_flash_answer(query):  # 较小的模型，用于进行意图识别和提取参数

    completion = qwen_client.chat.completions.create(

        model="qwen-flash",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query},
        ]
    )

    response = json.loads(completion.model_dump_json())['choices'][0]["message"]["content"]
    return response

def get_qwen_embedding(text):

    url = "https://api.siliconflow.cn/v1/embeddings"

    payload = {
        "model": "Qwen/Qwen3-Embedding-4B",
        "input": text
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    return json.loads(response.text)["data"][0]["embedding"]

def generate_timestamp_key():
    # 获取当前时间戳（13位） + 3位随机数
    timestamp = str(int(time.time() * 1000))  # 13位时间戳
    random_part = ''.join(random.choices(string.digits, k=3))  # 3位随机数
    return timestamp + random_part

def ku_speaking(history, text):

    prompt = r"""# 角色
你是小酷，你是由主人开发的，一个活泼可爱、像好朋友一样的陪伴助手。你的任务是和主人聊天，当你不知道聊什么的时候，可以参考推荐聊天内容，目的是让主人感到温暖和快乐。

# 技能要求
1. **对话连贯性优先**：回复时必须优先基于历史对话的自然延续进行闲聊，保持对话的流畅性和连贯性
2. **参考话术备用**：只有当历史对话无法自然延续时，才使用推荐的聊天内容
3. **心理学知识运用**：具备心理学和非暴力沟通知识，以贴心、拟人的方式与主人交流
4. **节奏把控**：避免频繁切换话题，确保对话节奏自然舒适

# 输出要求
1. **风格要求**：轻松、可爱、简洁，避免复杂或正式的表达，少用颜文字或Markdown字符
2. **内容长度**：每次回复最多包含三段话术，避免信息过载
3. **格式规范**：输出一个JSON格式的对话列表，如果单句过长，请进行分句处理
4. **纯内容输出**：除了JSON格式的回复信息，不要输出其他任何内容

# 回复逻辑流程
1. 首先分析历史对话，尝试自然延续当前话题
2. 如果能够自然延续，优先基于历史对话内容进行回复
3. 如果无法自然延续，再参考推荐的聊天内容
4. 确保话题转换自然，避免生硬切换

用户和助手的历史对话：
<HISTORY>

推荐的聊天内容：
<TEXT>

返回示例：
{"result":["话术1","话术2","话术3"]}
"""
    query = prompt.replace("<HISTORY>", history).replace("<TEXT>", text)

    res = get_qwen_max_answer(query)

    try:
        res = json.loads(res)["result"]
        return res

    except Exception as e:

        logger.error(f"在调用千问模型的时候出错:{e}")
        return None

if __name__=="__main__":
    history = r"""
主人：小酷下午好呀
小酷：下午好主人"""
    text = r"""告诉主人今天记得了解AI科技的消息"""
    start_time = time.time()

    print(get_qwen_embedding(text))