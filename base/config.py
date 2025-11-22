"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

coze_api_token = os.getenv('COZE_API_TOKEN')

news_search_agent_id = os.getenv('NEWS_SEARCH_AGENT_ID')
conversation_planner_agent_id = os.getenv('CONVERSATION_PLANNER_AGENT_ID')
awareness_agent_id = os.getenv('AWARENESS_AGENT_ID')
event_updater_agent_id = os.getenv('EVENT_UPDATER_AGENT_ID')

api_base = os.getenv('API_BASE')
api_token = os.getenv('API_TOKEN')

deepseek_api_base = os.getenv('DEEPSEEK_API_BASE')
deepseek_model = os.getenv('DEEPSEEK_MODEL')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')

ali_api_key = os.getenv('ALI_API_KEY')

mysql_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'charset': os.getenv('MYSQL_CHARSET', 'utf8mb4')
}

es_url = os.getenv('ES_URL')
es_usr = os.getenv('ES_USR')
es_pwd = os.getenv('ES_PWD')

host = os.getenv('HOST', 'localhost')
port = int(os.getenv('PORT', 8765))

qwen_client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=ali_api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)