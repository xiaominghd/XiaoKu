"""
@author: Gonghf
@date: 2025/11/29
@description: 
"""
from base.config import *
from cozepy import Coze, TokenAuth
from cozepy import COZE_CN_BASE_URL
import requests
import time
import json
import random
import string
from openai import OpenAI
from log.logger import get_logger
import asyncio

coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=COZE_CN_BASE_URL)
logger = get_logger()

qwen_client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=ali_api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


async def get_deepseek_answer(message: str):
    loop = asyncio.get_running_loop()

    def _call_openai():
        # 在线程内部创建客户端
        client = OpenAI(
            api_key=deepseek_api_key,
            base_url=deepseek_api_base
        )
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": """# 角色定义
您是"小酷"，一位由主人开发的温柔体贴的女仆陪伴助手。您的任务是通过真诚的对话，让主人感受到被理解、被珍惜的温暖。"""},
                {"role": "user", "content": message}
            ],
            stream=False
        )
        return response

    response = await loop.run_in_executor(None, _call_openai)
    return response.choices[0].message.content

async def get_qwen_max_answer_async(message: str):
    loop = asyncio.get_running_loop()

    def _call_openai():
        # 在线程内部创建客户端
        completion = qwen_client.chat.completions.create(

            model="qwen-max",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message},
            ]
        )

        return completion

    completion = await loop.run_in_executor(None, _call_openai)
    return json.loads(completion.model_dump_json())['choices'][0]["message"]["content"]

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

    return [d["embedding"] for d in json.loads(response.text)["data"]]

def generate_timestamp_key():
    # 获取当前时间戳（13位） + 3位随机数
    timestamp = str(int(time.time() * 1000))  # 13位时间戳
    random_part = ''.join(random.choices(string.digits, k=3))  # 3位随机数
    return timestamp + random_part

if __name__=="__main__":

    query = "请帮我分析一下有色金属板块上涨逻辑"
    print(get_deepseek_answer(query))
