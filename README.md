# BOM Price Checker

> WorkBuddy Skill · 电子元器件 BOM 比价助手

从产品需求反推 BOM 清单（支持经济版/标准版/高性能版多版本对比），或直接读取 BOM 表，跨多个平台查询最低价，生成带来源链接的比价单。

**版本**: 9.3.0 | **更新**: 2026-05-16

## 功能特性

- **需求反推 BOM**：描述产品需求 → 五层推理（Layer 0 约束矩阵 → Layer 1 子系统 → Layer 2 模块槽位 → Layer 3 选型 → Layer 4 辅料补全）→ 完整元器件清单
- **版本数量用户自选**：B.1 需求确认后立刻问 1-3 个版本，按选定数量推理（不浪费 token）
- **4 大价格来源**：立创/华秋商城直搜、博查 AI 搜索、IQS 交叉验证、Playwright 实时点验
- **AI 价强制查询**：所有元器件强制走博查 + IQS 并行（不论商城价是否查到），获取电商对比维度
- **双源交叉验证**：立创 + 华秋商城并行查询
- **可视化输出**：show_widget 表格预览 + HTML 报告（generate_report.py 自动算 price_unit / cost_ratio）
- **环境自检**：Phase 0 自动检测依赖，一键安装配置

## 关键约束（v9.3 起）

- **基础参数必问**：B.1 交互时产品核心功能、供电方式、通信需求、屏幕大小、产量、成本偏好、版本数量必须确认，不允许"自行推断跳过"
- **可选外设多选**：B.1.4 新增 10 类外设多选询问（显示屏/摄像头/4G_5G/WiFi_BLE/GPS/NFC/麦克风/IMU/马达/LED），用户决定而非模型预判
- **防凑齐幻觉**：标准分类扩展为 22+ 类词典，每类标注取舍依据；用户没说且 B.1.4 没勾的分类严禁出现在 BOM（与 v9.1 防 ESP32 幻觉同源约束）
- **核心元件强制具体品牌**：MCU、传感器、电池、电源 IC、显示模组、Camera、通信模组、Flash、内存——`brand` 不允许为空 / "混用" / "通用" / "-"
- **散装件允许 brand="混用"**：阻容感、轻触开关、喇叭、连接器、PCB、外壳——但 description 必须列 ≥ 1 个候选品牌
- **存储分两行**：eMMC（`存储-Flash`）和 LPDDR（`存储-内存`）独立分行查询，不合并
- **模组类走成品**：屏幕、Camera、GPS 等模组的 part_number 写"模组型号"+ brand 写"模组厂家"，driver IC 仅写 description（不当作 part_number）
- **查价失败汇总**：系统性失败（连续 ≥3 次/失败率 >80%/完全无结果）才反馈，偶发单次失败静默降级

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

## 版本历史

- **9.3.0** (2026-05-16)
  - **交互流程优化**：B.1 改为基础参数必问；新增 B.1.4 可选外设多选询问（10 类）；B.1.5 改为 multiSelect 支持 1-3 版本多选
  - **查价失败反馈**：新增失败汇总规则，系统性失败（连续 ≥3 次/失败率 >80%/完全无结果）才反馈，偶发单次失败静默降级
  - **分类扩展 + 防幻觉**：标准分类从 15 类扩展为 22+ 类词典（LED/4G_5G/GPS/NFC/麦克风/扬声器/IMU/马达/按键独立），每类标注取舍依据；Layer 1 新增"按需展开"硬约束，用户没说且 B.1.4 没勾的分类严禁出现
  - **HTML 报告 UI 优化**：ver-tab 卡片改为单价"小计合计"；成本分布图改用 price_unit；表格去内嵌滚动改 sticky 表头；表头重设计（14px/primary 色/渐变背景）；备注自动换行
  - **PCB 价格公式**：generate_report.py 新增 compute_pcb_price() 经验公式，PCB 类别且 mall+ai 都为 null 时自动调用
- **9.2.0** (2026-05-15)
  - 修复屏幕选型走 driver IC 而非成品模组
  - 修复核心元件品牌丢失（电池、合并存储退化为"混用"）
  - 拆分 `存储` 分类为 `存储-Flash` + `存储-内存`，BOM 必须分两行
  - 版本数量改为用户在 B.1 后自选（1-3 个），不再固定 2-3 个
  - AI 价改为强制查询（所有元器件，不论商城价是否查到）
- **9.1.0** (2026-05-15)
  - 解决 ESP32 幻觉（候选清单 ≥ 3 + 必写排除理由）
  - 字段名统一到 `price_mall` / `price_ai` / `price_unit`，generate_report.py 加字段兼容层
  - `price_unit` 和 `cost_ratio` 由生成脚本自动计算
- **9.0.1** (2026-05-14)
  - 移除 build_bom_json.py，简化管线流程

## License

MIT
