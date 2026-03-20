# 🔮 PromptVault - Prompt 版本管理工具

> 开源的、Git-like 的 AI Prompt 版本管理系统

## ✨ 特性

- 📝 **Prompt CRUD** - 创建、读取、更新、删除 Prompt
- 🔄 **版本控制** - 自动记录每次修改，支持回滚
- 🔀 **Diff 对比** - 可视化对比两个版本的差异
- 🏷️ **标签分类** - 按场景、模型、用途分类管理
- 🌐 **API 服务** - 提供 REST API 供 Agent 调用
- 📦 **变量插值** - 支持 `{{variable}}` 语法
- 🚀 **一键部署** - Docker 一键启动

## 🚀 快速开始

### Docker 启动

```bash
docker run -p 8000:8000 -v ./data:/app/data promptvault/prompt-vault
```

### 本地开发

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## 📚 API 文档

启动后访问: http://localhost:8000/docs

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /prompts | 获取所有 Prompt |
| POST | /prompts | 创建新 Prompt |
| GET | /prompts/{id} | 获取单个 Prompt |
| PUT | /prompts/{id} | 更新 Prompt（自动创建版本） |
| GET | /prompts/{id}/versions | 获取版本历史 |
| POST | /prompts/{id}/rollback/{version} | 回滚到指定版本 |
| POST | /prompts/{id}/render | 渲染 Prompt（替换变量） |
| GET | /prompts/{id}/diff | 对比两个版本 |
