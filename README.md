<h1 align="center">XiaoKu：智能陪伴Agent</h1>

<p align="center">
  <img src="https://img.shields.io/badge/XiaoKu-小酷机器人-36CFC9?style=for-the-badge&logo=github&logoColor=white" alt="小酷机器人" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/LLM-大语言模型-ff69b4?style=for-the-badge&logo=semantic-release&logoColor=white" alt="LLM" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License" />
</p>

## ✨ 项目概述

**小酷**是一个拥有独特"人格"与"意识"的AI陪伴Agent。本项目的核心愿景是将个体的记忆与思考持久化保存，使其能够被随时感知与珍视，构建承载人类思维的数字存在。

当前版本（V2）探索了一种无需微调模型的对话系统架构，通过**多级快慢思考流水线**，显著提升对话系统的情境感知能力。小酷不仅能够进行自然流畅的对话，还能主动感知用户兴趣变化，自动切换话题，形成连续的记忆管理。

在未来迭代中，小酷将演进为用户与多个AI智能体（Agent）交互的统一代理入口，加速信息交换效率，并在现有的人与人社交网络之上，构建一层**Agent-to-Agent的社交网络**。

## 🚀 核心特性

### 🧠 人格与启动
- **冷启动支持**：每次对话都从一个预设的"有状态"人格开始，保证体验的连贯性。
- **人格一致性**：核心系统提示词仅包含人格定义与回复逻辑，确保人格的纯粹与稳定。结合对话感知模块，提供三类基础回复模式指导，提升交互自然度。

### 🧩 对话管理
- **Ku Event 事件单元**：在传统上下文窗口之上，构建以"事件"为粒度的对话管理单元。支持按事件控制对话流程，并可对单个事件片段进行独立存档与管理。
- **动态上下文管理**：采用可折叠的上下文标签与上下文压缩技术，在保证对话质量的同时，精确控制Token消耗与响应延迟。
- **话题自动检测与切换**：基于大语言模型自动识别话题转换时机，保持对话的自然性和连贯性。

### 📚 记忆与知识
- **Agentic RAG 记忆增强**：通过主动感知对话意图，提前检索相关历史记忆或补充外部知识，从而提升对话的真实感与信息深度。
- **事件驱动的记忆存储**：以事件为单位对对话历史进行切片存储，支持高效的检索与召回。
- **背景信息注入**：智能向对话中注入相关背景信息，增强上下文连贯性。

### 🔄 三线程架构
- **感知-反应线程**：负责接收用户输入并生成即时回复
- **后台思考线程**：持续监控对话质量，提供改进意见
- **记忆管理线程**：负责历史数据的存储、检索和更新

## 🤖 工作流程概述

小酷的对话流程模拟了人类对话中的"感知-反应"过程，并在全程保持后台"思考"，以提供连贯、智能的交互体验。

### 🔄 流程概览

1. **连接建立**：用户创建连接后，系统立即调用事件感知系统，推荐潜在感兴趣的事件及相关背景信息，同时注入近期对话历史作为上下文感知，避免冷启动。
2. **对话循环**：每轮用户输入都会触发"感知-反应"链，并在后台异步执行"思考"任务，以优化对话质量。

### 👁️ 感知模块
当用户消息到达时，小酷快速判断其是否属于当前事件讨论范围：
- **若属于当前事件**：将消息追加至该事件的对话列表，更新事件状态。
- **若不属当前事件（或用户兴趣转移）**：触发事件切换或创建新事件。

**技术实现**：基于 Qwen Flash 模型构建，侧重低时延意图识别，以保障对话流畅性。

### ⚡ 反应模块
小酷依据当前事件，以 O(1) 时间复杂度构建大模型历史上下文，并传入大模型生成回复。为提升多样性，在保持基础人格的前提下动态选择三种回复逻辑。

**技术实现**：基于 Qwen Max（非思考模式）模型，确保回复质量与一致性。

### 💭 思考模块（后台任务）
在生成回复的同时，小酷异步执行以下任务以提升长期对话质量：

#### 📚 1. 记忆召回
采用 Agentic RAG 思路，根据当前事件召回历史聊天片段，并预测未来可能涉及的话题进行扩展召回。

#### 🧭 2. 对话指引
调用 Qwen Max（思考模式）模型进行实时监测：
- 检测幻觉或人格偏移
- 根据事件走向主动规划后续聊天方向

#### ✂️ 3. 上下文压缩
当触发压缩条件时，对当前事件的上下文窗口进行拆分：
- 总结远期信息
- 保留近期消息
- 仅压缩当前事件上下文，不直接修改对话窗口，以提升效率并减少用户感知落差

#### 💾 4. 事件存储
对话结束后，以事件为单位对聊天记录进行切片存储，确保话题相似的数据能被高效召回。

#### 📝 外部信息注入格式
思考模块的输出会作为外部信息注入到大模型历史对话中。为保持严格的 role 交替结构（user/assistant），注入信息采用以下格式：
```python
{"role":"user","content":"[系统提示信息开始]"}
{"role":"assistant","content":"外部信息[系统提示信息结束]"}
```

## 🛠️ 技术栈

### 后端
- **Python 3.10+**: 主要开发语言
- **websockets**: WebSocket通信
- **asyncio**: 异步编程框架
- **OpenAI SDK**: 与大语言模型交互

### AI/ML
- **通义千问 (Qwen)**: 核心对话引擎（qwen3-max）
- **Coze平台**: 智能体工作流
- **多种模型策略**: 包括快速响应、深度思考等不同模式

### 数据存储
- **MySQL**: 历史数据存储
- **Elasticsearch**: 快速检索引擎
- **内存缓存**: 实时数据管理


## 安装与部署

### 环境要求

- Python 3.10 或更高版本
- MySQL 5.7+ 数据库
- Elasticsearch (可选，用于高级检索)
- 有效的API密钥（阿里云通义千问、Coze等）

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/xiaominghd/XiaoKu.git
cd XiaoKu_v2

# 2. 安装Python依赖（推荐使用虚拟环境）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

pip install websockets python-dotenv openai pymysql elasticsearch

# 3. 配置环境变量（复制.env.example并修改相应值）
cp .env.example .env
```

### 配置说明

需要在 `.env` 文件中配置以下参数：

```bash
# Coze API 配置
COZE_API_TOKEN=your_coze_token_here
NEWS_SEARCH_AGENT_ID=your_news_agent_id
CONVERSATION_PLANNER_AGENT_ID=your_conversation_planner_id
AWARENESS_AGENT_ID=your_awareness_agent_id
EVENT_UPDATER_AGENT_ID=your_event_updater_id

# 通义千问 API 配置
ALI_API_KEY=your_ali_api_key

# MySQL 数据库配置
MYSQL_HOST=127.0.0.1
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=history
MYSQL_PORT=3306

# Elasticsearch 配置
ES_URL=https://127.0.0.1:9200
ES_USR=elastic
ES_PWD=your_elasticsearch_password

# 应用服务器配置
HOST=0.0.0.0
PORT=8765
```

### 数据库初始化

需要创建MySQL数据库表结构：


### 启动项目

```bash
# 启动服务器
python main.py
```

服务器将在指定的端口上运行（默认为8765）。

## 使用说明

### 基础使用

1. 启动服务器后，通过WebSocket客户端连接到指定地址（如ws://localhost:8765）
2. 服务器会自动初始化并显示欢迎消息
3. 发送消息与小酷进行对话

### 对话特点

- **话题感知**: 小酷能自动识别话题变化并相应调整回复策略
- **记忆管理**: 历史对话会被自动归档到相关事件中
- **个性化**: 基于用户档案提供个性化回复
- **多风格回复**: 根据对话内容自动调整共情、幽默或引导等不同回复风格

### 消息处理

- **消息缓冲**: 支持短时间内连续消息的合并处理
- **自动补全**: 后台持续监控对话质量并提供改进建议
- **提醒功能**: 长时间无活动时会自动提醒用户

## 目录结构

```
XiaoKu_v2/
│
├── main.py                 # 主程序入口
├── Ku.py                   # 小酷核心类
├── send.py                 # 消息发送工具
├── .env                    # 环境变量配置
├── .env.example            # 环境变量模板
├── README.md               # 项目说明文档
│
├── Agents/                 # 智能体相关模块
│   └── awareness.py        # 意识/感知模块
│
├── BackGroundTask/         # 后台任务模块
│   ├── memory_augment.py   # 记忆增强
│   ├── conversation_guidance_manager.py # 对话指引管理
│   └── weak_up.py          # 用户唤醒提醒
│
├── Context/                # 上下文管理模块
│
├── Event/                  # 事件管理模块
│   └── EventManager.py     # 事件管理器
│
├── Memory/                 # 记忆存储模块
│   ├── memory_es_v1.py     # Elasticsearch记忆存储
│   ├── memory_manager.py   # 记忆管理器
│   └── memory_mysql_v1.py  # MySQL记忆存储
│
├── base/                   # 基础设施
│   ├── api.py              # API接口
│   ├── config.py           # 配置管理
│   └── qwen_chat.py        # 通义千问接口
│
├── Assets/                 # 静态资源
│
├── logs/                   # 日志文件
└── log/                    # 旧日志文件
```

## API接口

### WebSocket接口
- **地址**: ws://localhost:8765 (可通过配置修改)
- **消息格式**:
  - 客户端发送: 纯文本消息
  - 服务端返回: JSON格式
    ```json
    {
      "type": "user|assistant",
      "message": "消息内容",
      "timestamp": "ISO时间戳"
    }
    ```

## 常见问题

- **Q: 为什么启动时出现API密钥错误？**
  A: 检查`.env`文件中是否正确配置了相应的API密钥

- **Q: 如何处理数据库连接失败？**
  A: 检查MySQL服务是否正常运行，以及`.env`中的数据库配置是否正确

- **Q: 为什么有时候对话突然切换话题？**
  A: 这是小酷的智能话题切换功能，如果需要禁用可在EventManager中调整策略

## 扩展与定制

### 自定义人格
可以通过修改`base/qwen_chat.py`中的system_prompt来自定义小酷的人格特质。

### 新增功能模块
- **事件管理**: 修改`Event/`目录下的模块
- **记忆系统**: 扩展`Memory/`目录下的模块
- **后台任务**: 添加到`BackGroundTask/`目录

### 开发规范
- 代码风格遵循PEP8标准
- 函数和类需添加适当的文档字符串
- 关键业务逻辑需提供测试用例

## 许可证

[MIT License](LICENSE)

## 联系方式

- 作者：GongHaofeng
- 邮箱：1530383208@qq.com
