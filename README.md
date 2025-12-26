
<h1 align="center">陪伴机器人小酷</h1>

<p align="center">
  <img src="https://img.shields.io/badge/XiaoKu-小酷机器人-36CFC9?style=for-the-badge&logo=github&logoColor=white" alt="小酷机器人" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/LLM-大语言模型-ff69b4?style=for-the-badge&logo=semantic-release&logoColor=white" alt="LLM" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License" />
</p>

## ✨ 项目概述

**小酷**是一个拥有独特“人格”与“意识”的AI伴侣机器人。本项目的核心愿景是将个体的记忆与思考持久化保存，使其能够被随时感知与珍视，构建一个承载人类思维的数字存在。

当前版本（V1）探索了一种无需微调模型的对话系统架构，通过**多级快慢思考流水线**，显著提升对话系统的情境感知能力。

在未来迭代中，小酷将演进为用户与多个AI智能体（Agent）交互的统一代理入口，加速信息交换效率，并在现有的人与人社交网络之上，构建一层**Agent-to-Agent的社交网络**。

## 🚀 核心特性

### 🧠 人格与启动
- **冷启动支持**：每次对话都从一个预设的“有状态”人格开始，保证体验的连贯性。
- **人格一致性**：核心系统提示词仅包含人格定义与回复逻辑，确保人格的纯粹与稳定。结合对话感知模块，提供三类基础回复模式指导，提升交互自然度。

### 🧩 对话管理
- **Ku Event 事件单元**：在传统上下文窗口之上，构建以“事件”为粒度的对话管理单元。支持按事件控制对话流程，并可对单个事件片段进行独立存档与管理。
- **动态上下文管理**：采用可折叠的上下文标签与上下文压缩技术，在保证对话质量的同时，精确控制Token消耗与响应延迟。

### 📚 记忆与知识
- **Agentic RAG 记忆增强**：通过主动感知对话意图，提前检索相关历史记忆或补充外部知识，从而提升对话的真实感与信息深度。

## 技术实现

### 实现思路

小酷主要依靠Ku Event事件管理器 和 上下文窗口维护对话。当用户创建连接之后，系统会调用小酷的事件感知系统，推荐当前用户可能会感兴趣的事件以及事件的相关背景，同时传入最近的对话信息，作为历史对话的快速启动。当用户传入消息的时候，小酷会预先判断该内容是否属于当前事件，如果是，则将当前消息加入到当前事件的对话列表中，如果不是（或者是用户对当前话题感兴趣程度较低），则进行事件的切换。与此同时将当前消息插入到上下文窗口中，传入给大模型获取回复。小酷充分利用了对话过程中的时间隙，通过创建后台任务，实现“边说边想”的能力。具体的，在进行回复的过程中还同时进行以下三个后台任务：
1、记忆召回。当触发记忆召回任务时，根据指定事件在数据库中召回历史聊天片段。并将召回之后的结果以外部信息“历史”的形式传入到对话中。
2、对话指引。当触发对话指引任务时，小酷在指定时间下调用带有思考能力的大模型，通过传入当前事件，使用大模型判断对话中是否出现幻觉，用户感兴趣的程度，以及后续聊天的规划。这类信息以“背景”的形式传入到对话中。
3、上下文压缩。当触发上下文压缩任务时，小酷会将指定位置的内容进行总结，同时保留最近的消息，减轻用户的隔阂感。在事件维度进行上下文压缩会同步的在上下文窗口中进行更新。
4

### 技术栈

- 前端：如 React、Vue、HTML/CSS/JavaScript 等
- 后端：如 Node.js、Python、Java、Go 等
- 数据库：如 MySQL、MongoDB、Redis 等
- 其他依赖：第三方库/服务



## 安装与部署

### 环境要求

- 操作系统要求
- 所需依赖（Node、Python、Java 等及其版本）
- 其他特殊要求

### 安装步骤

```bash
git clone <仓库地址>
cd <项目目录>
<安装依赖相关命令，如 npm install、pip install -r requirements.txt 等>
```

### 配置说明

- 配置项1：如何配置及其说明
- 配置项2：如何配置及其说明

### 启动项目

```bash
<启动命令，如 npm start、python main.py 等>
```

## 使用说明

项目的基础用法介绍、常用操作演示等。

## 目录结构

```text
项目根目录
│
├── src/                # 源代码目录
├── docs/               # 文档目录
├── scripts/            # 工具/脚本
├── tests/              # 测试代码
├── README.md           # 项目说明
├── package.json        # Node 项目依赖文件
├── requirements.txt    # Python 依赖清单 (如适用)
└── ...
```

## 常见问题

- 问题1：解决方法
- 问题2：解决方法

## 贡献指南

1. Fork 本仓库
2. 创建 feature 分支 (`git checkout -b feature/foo`)
3. 提交你的更改 (`git commit -am 'Add new feature'`)
4. 推送到分支 (`git push origin feature/foo`)
5. 提交 Pull Request

## 许可证

[MIT](LICENSE) 或其它协议

## 联系方式

- 作者：GongHaofeng
- 邮箱：1530383208@qq.com
- 更多联系方式...
