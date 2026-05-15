# BOM Price Checker

> WorkBuddy Skill · 电子元器件 BOM 比价助手

从产品需求反推 BOM 清单（支持经济版/标准版/高性能版多版本对比），或直接读取 BOM 表，跨多个平台查询最低价，生成带来源链接的比价单。

**版本**: 9.0.1 | **更新**: 2026-05-14

## 功能特性

- **需求反推 BOM**：描述产品需求 → 自动推理完整元器件清单（多版本可选）
- **4 大价格来源**：立创/华秋商城直搜、博查 AI 搜索、IQS 交叉验证、Playwright 实时点验
- **双源交叉验证**：立创 + 华秋商城并行查询，博查 + IQS 并行查询
- **可视化输出**：show_widget 表格预览 + HTML 导出
- **环境自检**：Phase 0 自动检测依赖，一键安装配置

## 依赖

| 依赖 | 必须 | 说明 |
|------|------|------|
| Python 3.11+ | 是 | 脚本运行环境 |
| requests | 是 | `pip3 install requests` |
| openpyxl | 是 | `pip3 install openpyxl` |
| playwright | 推荐 | 立创商城直搜 |
| 博查 API Key | 推荐 | 已内置，开箱即用 |
| IQS API Key | 推荐 | 已内置，开箱即用 |

> API Key 已内置，缺失时自动降级但不阻塞流程。

## 安装到 WorkBuddy

### 方式一：直接克隆（推荐）

```bash
# 克隆到 WorkBuddy skills 目录
git clone https://github.com/anson592/bom-price-checker-claudetest.git ~/.workbuddy/skills/bom-price-checker-claudetest
```

### 方式二：手动下载

1. 从 GitHub 下载 ZIP 并解压
2. 将文件夹重命名为 `bom-price-checker-claudetest`
3. 放入 `~/.workbuddy/skills/` 目录

## 项目结构

```
bom-price-checker-claudetest/
├── SKILL.md                    # Skill 定义文件（核心）
├── README.md                   # 说明文档
├── README_WORKFLOW.md          # 工作流文档
├── report-template.html        # HTML 报告模板
├── generate_report.py           # 报告生成脚本
├── scripts/
│   ├── shengsuan_search.py     # 博查 AI 搜索
│   ├── iqs_search.py           # 阿里云 IQS 搜索
│   ├── hqchip_search.py        # 华秋商城搜索
│   ├── lcsc_szlcsc_search.py  # 立创商城搜索
│   ├── lcsc_playwright_verify.py # Playwright 实时点验
│   └── generate_bom_comparison.py # BOM 对比表格生成
├── schema/                     # JSON Schema
└── data/                       # 数据目录
```

## 使用示例

在 WorkBuddy 对话中直接说：

- 「帮我做一个智能台灯，查一下 BOM 成本」
- 「帮我查 BOM 价格」，然后上传 BOM 表
- 「STM32F103C8T6 2000套多少钱」

## License

MIT
