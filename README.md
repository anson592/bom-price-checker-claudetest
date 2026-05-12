# BOM Price Checker

> WorkBuddy Skill · 电子元器件 BOM 比价助手

从产品需求反推 BOM 清单（支持经济版/标准版/高性能版多版本对比），或直接读取 BOM 表，跨多个平台查询最低价，生成带来源链接的比价单。

**版本**: 8.3.0 | **更新**: 2026-05-12

## 功能特性

- **需求反推 BOM**：描述产品需求 → 自动推理完整元器件清单（多版本可选）
- **5 大价格来源**：立创 BOM 批量配单、博查 AI 搜索、IQS 交叉验证、买手全网比价、商城 WebFetch 验证
- **双源交叉验证**：博查 + IQS 并行查询，交叉比对确保价格准确
- **可视化输出**：show_widget 表格预览 + HTML/Excel 导出
- **环境自检**：Phase 0 自动检测依赖，一键安装配置

## 依赖

| 依赖 | 必须 | 说明 |
|------|------|------|
| Python 3.11+ | 是 | 脚本运行环境 |
| requests | 是 | `pip3 install requests` |
| openpyxl | 是 | `pip3 install openpyxl` |
| Playwright MCP | 推荐 | 立创 BOM 批量配单需要 |
| 博查 API Key | 推荐 | 环境变量 `SHENGSUAN_API_KEY` |
| IQS API Key | 推荐 | 环境变量 `ALIYUN_IQS_API_KEY` |

> Playwright 和 API Key 为可选，缺失时自动降级但不阻塞流程。

## 安装到 WorkBuddy

### 方式一：直接克隆（推荐）

```bash
# 克隆到 WorkBuddy skills 目录
git clone https://github.com/YOUR_USERNAME/bom-price-checker.git ~/.workbuddy/skills/bom-price-checker
```

### 方式二：手动下载

1. 从 GitHub 下载 ZIP 并解压
2. 将文件夹重命名为 `bom-price-checker`
3. 放入 `~/.workbuddy/skills/` 目录

### 配置 API Key（可选但推荐）

将你的 API Key 添加到 `~/.zshrc`：

```bash
export SHENGSUAN_API_KEY="你的博查API Key"
export ALIYUN_IQS_API_KEY="你的IQS API Key"
```

然后执行 `source ~/.zshrc` 或重启终端。

> 不配置 API Key 也能使用，博查和 IQS 查询会跳过，自动降级为单源查询。

### 首次使用

在 WorkBuddy 中触发任意关键词（如「帮我查BOM价格」），Skill 会自动执行 Phase 0 环境检查，引导你完成所有配置。

## 项目结构

```
bom-price-checker/
├── SKILL.md                    # Skill 定义文件（核心）
├── scripts/
│   ├── shengsuan_search.py     # 博查 AI 搜索
│   ├── iqs_search.py           # 阿里云 IQS 搜索
│   ├── search_price.py         # 买手全网比价
│   └── generate_bom_comparison.py  # BOM 对比表格生成
├── data/
│   └── lcsc_cookies.json       # 立创 Cookie（用户自行配置，不入库）
├── .env.example                # 环境变量示例
└── .gitignore
```

## 使用示例

在 WorkBuddy 对话中直接说：

- 「帮我做一个智能台灯，查一下 BOM 成本」
- 「帮我查 BOM 价格」，然后上传 BOM 表
- 「ESP32-S3-WROOM-1-N8R8 2000套多少钱」

## License

MIT
