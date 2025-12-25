
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

### 技术栈

- 前端：如 React、Vue、HTML/CSS/JavaScript 等
- 后端：如 Node.js、Python、Java、Go 等
- 数据库：如 MySQL、MongoDB、Redis 等
- 其他依赖：第三方库/服务

### 主要实现思路

简要描述整体架构、关键流程，或用简单流程图/架构图展示。

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
