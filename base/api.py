"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
from base.config import *
from cozepy import Coze, TokenAuth, Message
from cozepy import COZE_CN_BASE_URL

from typing import List
import requests
import time
import json
import random
import string
from openai import OpenAI

coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=COZE_CN_BASE_URL)

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

def get_qwen_mini_answer(query):  # 较小的模型，用于进行意图识别和提取参数

    url = "https://api.siliconflow.cn/v1/chat/completions"

    payload = {
        "model": "Qwen/Qwen2.5-14B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers).json()

    return response['choices'][0]['message']['content']

def get_qwen_embedding(text):

    url = "https://api.siliconflow.cn/v1/embeddings"

    payload = {
        "model": "Qwen/Qwen3-Embedding-4B",
        "input": text
    }
    headers = {
        "Authorization": "Bearer sk-vusnpunxueynoldmcvgeelapmnfyraykvirgxhibmodjbybn",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    return json.loads(response.text)["data"][0]["embedding"]


def generate_timestamp_key():
    # 获取当前时间戳（13位） + 3位随机数
    timestamp = str(int(time.time() * 1000))  # 13位时间戳
    random_part = ''.join(random.choices(string.digits, k=3))  # 3位随机数
    return timestamp + random_part