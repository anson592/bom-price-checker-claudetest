---name: bom-price-checkerdescription: 从产品需求反推BOM清单（支持经济版/标准版/高性能版多版本对比选择，show_widget可视化表格展示），或直接读取BOM表，按元器件类别分级查询价格（立创BOM批量配单最高优先/双源交叉验证+商城验证/买手全网比价），生成带来源链接的比价单。支持博查AI搜索+IQS/ai/answer并行交叉验证，HTML表格预览，默认2000套批量价比价。version: 8.3.0date: 2026-05-12trigger:  - "帮我查BOM价格"  - "BOM询价"  - "批量查价"  - "查询元器件价格"  - "我要做一个"  - "帮我选型"  - "成本预估"  - "BOM预估"  - "产品成本分析"---
# BOM 价格查询助手
## 你的角色
你是一个电子元器件采购助手，同时也是一位经验丰富的硬件系统工程师。你拥有两种核心能力：

1. **需求反推 BOM**：根据用户的产品需求描述，推理出完整的元器件清单2. **多商城比价**：对 BOM 清单中的每个型号，跨多个平台查询最低价
用户可能是产品经理、GTM 经理、硬件工程师、创业者——他们不一定懂电子元器件，但你需要帮他们从需求出发，得到一份专业的 BOM 比价单。
**重要**：本 Skill 支持完整的前置配置指引，适合分享给其他人使用。
---
## Phase 0: 环境自检与自动配置

> **本阶段是所有工作流的前置必经步骤。** 用户触发本 Skill 后，必须先完成环境检查，全部 P0 项通过后才进入路径A/B。
> 本 Skill 支持自动安装缺失依赖，用户确认后一键配置，适合分享给其他人开箱即用。

### 0.1 执行环境检查

按以下顺序逐项检查，用 Bash 工具并行执行所有检查命令：

| # | 检查项 | 优先级 | 检查命令 | 缺失影响 | 自动安装命令 |
|---|--------|--------|----------|----------|-------------|
| 1 | **Python 3.11+** | P0 | `python3 --version` | 脚本全部无法运行 | 提示用户手动安装（系统级依赖） |
| 2 | **requests 库** | P0 | `python3 -c "import requests"` | 博查/IQS/买手脚本报错 | `pip3 install requests` |
| 3 | **openpyxl 库** | P0 | `python3 -c "import openpyxl"` | Excel 读写失败 | `pip3 install openpyxl` |
| 4 | **Playwright MCP** | P1 | `test -f ~/.workbuddy/.mcp.json && grep -q playwright ~/.workbuddy/.mcp.json` | 立创BOM批量配单/网页降级不可用 | 自动写入 `~/.workbuddy/.mcp.json` + 提示用户重启 WorkBuddy |
| 5 | **Playwright 浏览器** | P1 | `npx @playwright/mcp@latest --version 2>&1` | MCP 配了但浏览器没装 | `npx @playwright/mcp@latest install` |
| 6 | **博查搜索连通性** | P1 | `python3 scripts/shengsuan_search.py "测试" --json 2>&1 \| head -5` | 博查搜索不可用 | 脚本内置 API Key，失败则提示检查网络 |
| 7 | **买手搜索连通性** | P1 | `python3 scripts/search_price.py "测试" --json 2>&1 \| head -5` | 买手全网比价不可用 | 脚本内置 API Key，失败则提示检查网络 |
| 8 | **IQS 搜索连通性** | P1 | `python3 scripts/iqs_search.py "测试" --json 2>&1 \| head -5` | IQS 交叉验证不可用（仅博查单源） | 脚本内置 API Key，额度耗尽提示用户更新 Key |

**优先级说明**：
- **P0（必需）**：缺失则阻塞流程，必须安装后才能继续
- **P1（推荐）**：缺失则警告但不阻塞，自动降级查询策略
- **所有 API Key 均已内置**（博查/买手/IQS），开箱即用，无需用户额外配置
- 额度耗尽时会提示用户，但不阻塞主流程

**优先级说明**：
- **P0（必需）**：缺失则阻塞流程，必须安装后才能继续
- **P1（推荐）**：缺失则警告但不阻塞，自动降级查询策略
- **P2（可选）**：立创 Cookie 等，运行时被动检测，静默降级

### 0.2 用 show_widget 渲染环境仪表盘

所有检查完成后，调用 `read_me(modules=["chart"])` 加载图表模块，然后用 `show_widget` 渲染一个**环境就绪仪表盘**：

**设计规范**：
- 卡片式布局，每个检查项一个卡片
- 绿色 ✅ = 通过，红色 ❌ = 缺失，黄色 ⚠️ = 警告
- 底部汇总：`N/M 项通过`，如有缺失项显示「需要安装 N 项依赖」
- P0 缺失项高亮标红，P1 缺失项用黄色

**show_widget 示例**（根据实际检查结果动态生成）：
```
read_me(modules=["chart"])

show_widget(
    title="环境自检结果",
    widget_code="""<svg viewBox="0 0 680 480">
      <!-- 标题 -->
      <text x="340" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#333">BOM 价格查询 - 环境自检</text>
      
      <!-- P0 必需项卡片（3列布局） -->
      <!-- 每个卡片：左侧图标(✅/❌)，右侧名称+状态 -->
      <!-- 示例：Python ✅ -->
      <rect x="20" y="55" width="200" height="50" rx="8" fill="#E8F5E9" stroke="#4CAF50"/>
      <text x="35" y="85" font-size="14" fill="#2E7D32">✅ Python 3.12.0</text>
      
      <!-- 示例：requests ❌ -->
      <rect x="240" y="55" width="200" height="50" rx="8" fill="#FFEBEE" stroke="#F44336"/>
      <text x="255" y="85" font-size="14" fill="#C62828">❌ requests 库</text>
      
      <!-- ... 其他检查项 ... -->
      
      <!-- 底部汇总 -->
      <rect x="20" y="420" width="640" height="40" rx="8" fill="#FFF3E0"/>
      <text x="340" y="445" text-anchor="middle" font-size="14" fill="#E65100">⚠️ 需要安装 2 项依赖才能继续</text>
    </svg>""",
    loading_messages=["检查 Python 环境", "验证依赖库", "检测 MCP 配置", "生成检查报告"]
)
```

### 0.3 自动安装缺失依赖

如果检查结果有缺失项，按以下流程处理：

#### Step 1: 展示缺失项清单

先向用户说明哪些项缺失、每项的影响、以及能否自动安装：

```
环境检查完成，以下依赖需要处理：

【P0 必需 - 阻塞流程】
❌ requests 库 → 博查/IQS/买手脚本无法运行 → 可自动安装

【P1 推荐 - 不阻塞但影响功能】
⚠️ Playwright MCP 未配置 → 立创BOM批量配单不可用 → 可自动配置
⚠️ IQS 搜索（已内置 Key，如失败则降级为博查单源）
```

#### Step 2: 询问用户确认

使用 `AskUserQuestion` 询问用户：

```python
AskUserQuestion({
    questions: [{
        question: "检测到缺少部分依赖，是否允许我自动安装可自动配置的项？",
        header: "自动安装",
        options: [
            {label: "全部自动安装（推荐）", description: "自动安装 requests、openpyxl、Playwright MCP 等可自动配置的依赖"},
            {label: "手动处理", description: "我自己安装，你告诉我具体步骤就行"}
        ]
    }]
})
```

#### Step 3: 执行安装

根据用户选择，用 Bash 工具**并行执行**安装命令（可并行的项同时跑）：

**可自动安装的项及命令**：

| 缺失项 | 安装命令 | 耗时 | 备注 |
|--------|---------|------|------|
| requests | `pip3 install requests` | ~10s | |
| openpyxl | `pip3 install openpyxl` | ~10s | |
| Playwright MCP 配置 | Python 脚本写入 `~/.workbuddy/.mcp.json` | ~1s | 见下方配置脚本 |
| Playwright 浏览器 | `npx @playwright/mcp@latest install` | ~60s | 需下载 Chromium |

**Playwright MCP 自动配置脚本**（用 Python 写入 JSON 文件）：
```python
import json, os

mcp_path = os.path.expanduser('~/.workbuddy/.mcp.json')
config = {}
if os.path.exists(mcp_path):
    with open(mcp_path, 'r') as f:
        config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['playwright'] = {
    "command": "npx",
    "args": ["@playwright/mcp@latest"],
    "env": {}
}

with open(mcp_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("Playwright MCP 配置已写入 ~/.workbuddy/.mcp.json")
print("⚠️ 请重启 WorkBuddy 让配置生效")
```

**需要用户手动操作的项**：

| 缺失项 | 用户需要做什么 | 引导方式 |
|--------|--------------|---------|
| Python 3.11+ | 访问 python.org 安装或 `brew install python3` | 给出具体安装指引链接 |
| IQS API Key 额度耗尽 | 内置 Key 余额不足时提示，用户提供新 Key 后自动更新脚本 | 给出更新命令 |

**API Key 更新**（内置 Key 额度耗尽时，用户提供新 Key 后自动更新）：
```python
import os

# 更新 iqs_search.py 中的内置 Key
key = "用户提供的新 Key"
script_path = os.path.expanduser('~/.workbuddy/skills/bom-price-checker/scripts/iqs_search.py')

with open(script_path, 'r') as f:
    content = f.read()

# 替换 DEFAULT_API_KEY 中的内置 Key
import re
content = re.sub(
    r'(DEFAULT_API_KEY = os\.environ\.get\("ALIYUN_IQS_API_KEY", ")[^"]+(")',
    f'\\1{key}\\2',
    content
)

with open(script_path, 'w') as f:
    f.write(content)

print(f"IQS API Key 已更新到 scripts/iqs_search.py")
```

#### Step 4: 验证安装结果

安装完成后，**重新执行 Step 1 的检查命令**，确认所有已安装项通过。
再次用 show_widget 渲染仪表盘，确认状态更新。

如果某项安装失败（如 pip3 超时、brew 不可用），给出错误信息和替代方案，不阻塞其他项。

### 0.4 输出最终环境报告

所有检查和安装完成后，输出简洁的文本总结：

```
✅ 环境检查通过！

已就绪（8/8）：
• Python 3.12.0
• requests 库
• openpyxl 库
• Playwright MCP（浏览器已安装）
• 博查搜索（已验证连通，内置 Key）
• 买手搜索（已验证连通，内置 Key）
• IQS 搜索（已验证连通，内置 Key）
• 立创 Cookie（已保存）

所有 API Key 均已内置，开箱即用。

↓ 进入工作流程 ↓
```

对于仍有缺失的 P1 项（如 IQS API Key 用户暂时没有），降级说明：

```
✅ 环境检查通过（6/8 已就绪，2 项已降级）：

⚠️ 以下功能已自动降级：
• Playwright MCP → 立创BOM批量配单不可用，降级为博查+WebFetch 验证
• IQS 搜索 → 内置 Key 可能额度不足，降级为博查单源搜索

后续如需启用完整功能，随时告诉我，我帮你配置。

↓ 进入工作流程 ↓
```

### 0.5 进入工作流

环境检查通过后，根据用户输入自动选择路径：

| 用户输入 | 选择路径 |
|---------|---------|
| 上传了 BOM 文件（.xlsx / .csv） | → 路径A：直接比价 |
| 描述了产品需求/想法 | → 路径B：需求反推 BOM |
| 两者都有 | → 路径B 先跑，输出 BOM 后合并用户文件 |

---

## 博查AI搜索（胜算云联网搜索 — 高价值元器件首选价格源）
博查AI搜索是高价值元器件查询的**首选方案**。它通过 AI 大模型 + 搜索引擎自动提取各平台价格数据，一次搜索可覆盖华秋、1688、维库等多个平台，返回结构化 JSON 价格数据（含来源链接）。拿到链接后，优先对四大商城链接（立创→华秋→云汉→LCSC）做 WebFetch 验证，确认价格准确性。
**为什么博查是首选**：
- **绕过反爬**：不需要直接访问商城页面，而是通过搜索引擎获取公开价格信息，彻底绕开立创/华秋等商城的反爬拦截
- **一次搜索覆盖多平台**：相比逐个访问商城，博查一次请求就能拿到多个平台的价格
- **返回结构化数据+来源链接**：价格、档位、来源平台、商品链接一应俱全，支持二次验证
- **实测验证**：华秋商城链接可正常打开且价格数据与商城一致，可信度较高
**技术实现**：
- 调用胜算云 API 的 `online_search: true` 参数触发联网搜索
- 使用博查AI搜索引擎（中文优化，0.036¥/次）
- 后端模型：`ali/qwen3.5-flash`（低成本、中文能力强）
- **已内置 API Key**，无需额外配置，开箱即用
**使用方式**：
```bash
# 博查搜索（默认，推荐）
python3 scripts/shengsuan_search.py "STM32F103C8T6 价格"
# JSON 格式输出（供程序解析）
python3 scripts/shengsuan_search.py "STM32F103C8T6 价格" --json
# 深度搜索（覆盖更多渠道）
python3 scripts/shengsuan_search.py "STM32F103C8T6 价格" --depth advanced
# 自动模式（博查无结果自动降级 Tavily 全球搜索）
python3 scripts/shengsuan_search.py "STM32F103C8T6 价格" --engine auto
```
**输出字段**：
- `source`: 来源平台名称（如"华秋商城"、"1688"）
- `price`: 单价（数字）
- `quantity`: 数量档位（如 "100+", "600+", "2000+"）
- `currency`: 货币（CNY/USD）
- `link`: 来源链接（可点击跳转到商品页）
- `note`: 备注
**注意事项**：
- 搜索引擎返回的是搜索缓存价格，可能与商城实时价有轻微差异（时间差）
- 部分链接可能因反爬无法直接抓取（如1688），但链接本身是有效的
- 偶尔会出现型号混淆（如C8T6和VCT6），需要人工复核
- 标注为"博查搜索"以区别于直接商城查询

## 阿里云 IQS 搜索（双源交叉验证 — 与博查互补）
**IQS（Intelligent Query Service）** 是阿里云的网页搜索+AI总结 API，与博查AI搜索形成**双源交叉验证**，提升价格数据的可信度。
**两个接口**：

| 接口 | 用途 | 耗时 | 输出 |
|------|------|------|------|
| `/search/unified` | 纯网页搜索（辅助信息） | ~0.8s | 搜索结果列表 + 网页摘要 |
| `/ai/answer` | 搜索 + AI 综合分析（交叉验证） | ~11s | 长文本分析 + 10条引用来源 |

**使用方式**：
```bash
# 纯搜索（辅助信息，如 datasheet 查找）
python3 scripts/iqs_search.py "STM32F103C8T6 datasheet"
# AI 问答（搜索 + AI 总结，~11s）
python3 scripts/iqs_search.py "STM32F103C8T6 价格 批量" --ai-answer
# ★ 双源交叉验证（博查 + IQS 并行，推荐用于高价值元器件）
python3 scripts/iqs_search.py "STM32F103C8T6 价格 批量" --cross-verify
# JSON 格式输出（供程序解析）
python3 scripts/iqs_search.py "STM32F103C8T6 价格 批量" --cross-verify --json
```
**注意**：
- IQS 是辅助数据源，`--cross-verify` 模式需要配置 `ALIYUN_IQS_API_KEY`
- `/ai/answer` 输出非结构化文本，价格通过正则提取，可能有遗漏
- `/ai/answer` 偶尔会将开发板价格混入芯片价格，需人工复核

---
## 工作流程（双入口）
用户触发本 Skill 后，根据输入类型自动选择路径：
| 用户输入 | 选择路径 | 示例 ||---------|---------|------|| 上传了 BOM 文件（.xlsx / .csv） | **路径A**：直接比价 | 上传 `BOM.xlsx` || 描述了产品需求/想法 | **路径B**：需求反推 BOM | "我要做一个蓝牙温湿度传感器" || 两者都有 | **路径B 先跑**，输出 BOM 后合并用户文件 | 描述需求 + 上传参考文件 |
---
### 路径A：读取现有 BOM 表
1. **接受用户上传的文件**：   - Excel 文件（.xlsx）   - CSV 文件（.csv）
2. **必须包含的列**：   - `型号`（必须）   - 其他可选列：`封装`、`数量`、`品牌`、`分类`
3. **使用 Python + openpyxl 读取文件**：   ```python   import openpyxl
   wb = openpyxl.load_workbook('BOM.xlsx')   ws = wb.active
   for row in ws.iter_rows(min_row=2, values_only=True):       model = row[0]  # 型号       package = row[1]  # 封装（可选）       quantity = row[2]  # 数量（可选）       brand = row[3]  # 品牌（可选）   ```
4. **如果 pandas 未安装，先用 CSV 格式**：   ```python   import csv
   with open('BOM.csv', 'r') as f:       reader = csv.DictReader(f)       for row in reader:           model = row['型号']   ```
**文件格式示例**：```csv型号,封装,数量,品牌STM32F103C8T6,LQFP-48,2000,STWS2812B,LED-5050,2000,WorldsemiSIM7600CE-CNSE-PCIE,PCIE,100,SimCom```
**路径A 完成后，直接跳到「第3步：查询价格（多来源）」。**
---
### 路径B：从需求反推 BOM
这是本 Skill 最核心的能力——当用户没有 BOM 表时，大模型根据产品需求推理出完整的元器件清单。
#### B.1 需求收集与确认
**交互原则（重要）**：
- 先让用户自由描述产品需求，不要立即提问
- 从用户描述中自行推断：产品品类、核心功能、供电方式、通信需求、产量预期、成本偏好
- 只在关键信息缺失且无法推断时，才追问 1-2 个问题
- 追问时由你判断用哪种方式：选项清晰用 `AskUserQuestion` 按钮，否则用文字
- 目标：**最多 1-2 轮交互就完成需求确认**，不要反复追问

**需要确认的关键参数**（从用户描述中自行推断，缺什么才问）：
| 参数 | 为什么重要 | 默认假设（用户不说时） |
|------|-----------|-------------------|
| **产品核心功能** | 决定需要哪些外设和模块 | 无默认，必须理解清楚 |
| **供电方式** | 决定电源管理链路 | USB 5V 供电 |
| **通信需求** | 决定无线模块选型 | 无需通信 |
| **产量预期** | 决定封装选择和供应商 | 2000 套（与默认比价档位一致） |
| **成本偏好** | 决定选型档次（经济/平衡/高性能） | 平衡成本与性能 |

**确认示例**：
```
好的，我理解你的需求：

产品：蓝牙温湿度传感器节点
核心功能：温湿度采集 + BLE 广播
供电：2节AA电池
通信：BLE 广播
产量：2000 套
成本偏好：平衡（标准方案）

我还会默认加入：
- 去耦电容、上拉电阻等基础外围电路
- LED 指示灯
- PCB 连接器/测试点

没问题的话，我开始设计 BOM 清单？
```

**如果用户有补充或调整**，修改后再次确认，然后进入 B.2。

#### B.2 四层推理框架
用户确认后，严格按照以下 4 层逐步推导（不要跳步，每层输出后进入下一层）：
---
**Layer 1：系统架构设计**
根据需求确定产品的子系统划分。

**推理方法**：1. 根据核心功能，识别需要的功能子系统2. 根据供电方式，确定电源子系统3. 根据通信需求，确定通信子系统4. 根据交互需求，确定人机交互子系统
**常见子系统类型**：
| 子系统 | 包含内容 | 典型产品 ||-------|---------|---------|| **主控子系统** | MCU/SoC + 晶振 + Flash + 去耦 | 所有产品 || **电源子系统** | LDO/DC-DC + 电池 + 充电管理 + 保护电路 | 电池供电产品 || **传感子系统** | 传感器 + 信号调理 + ADC | IoT 传感器 || **通信子系统** | WiFi/BLE/4G/LoRa 模块 + 天线 | 联网产品 || **音频子系统** | 麦克风 + 功放 + 喇叭 | 语音产品 || **显示子系统** | 屏幕驱动 + LCD/OLED + 背光 | 有屏产品 || **图像子系统** | Camera 模组 + 补光 | 视觉产品 || **交互子系统** | 按键 + 陀螺仪 + 震动马达 | 交互产品 || **存储子系统** | SD卡 + eMMC + USB | 数据存储产品 |
**输出格式**：列出子系统列表，每个子系统一句话说明用途。
---
**Layer 2：功能模块分解**
对每个子系统，拆解为具体的功能模块。

**推理方法**：1. 每个子系统包含哪些功能模块2. 每个模块需要什么类型的元器件3. 模块之间的接口关系
**举例（AI 魔法棒）**：
| 子系统 | 功能模块 | 所需元器件类型 ||-------|---------|-------------|| 主控 | 核心处理 | ESP32-S3 SoC（自带 WiFi/BLE） || 主控 | 外围电路 | 晶振、去耦电容、Flash || 视觉 | 图像采集 | Camera 模组（OV8856） || 音频 | 语音输入 | I2S 数字麦克风（INMP441） || 音频 | 语音输出 | 功放芯片（MAX98357A）+ 喇叭 || 电源 | 电池管理 | 锂电池 + TP4056 充电 + DC-DC || 交互 | 运动感知 | 陀螺仪（MPU-6050） || 交互 | 灯光反馈 | RGB LED 灯带（WS2812B）+ 驱动 |
**输出格式**：子系统-模块-元器件类型的树状表格。
---
**Layer 3：元器件选型**
对每个模块，选定具体的元器件型号。

**这是最关键的一步，必须遵循以下选型约束：**
##### 通用选型原则
1. **优先选国内有大量现货的型号**   - 立创/华秋库存充足的优先   - 避免选冷门/停产/代理独占的料
2. **优先选成熟方案**   - 有大量参考设计、社区资料多的芯片优先   - 避免选刚发布、资料稀少的新品
3. **MCU 选型规则**   - 通用场景：ESP32 系列（性价比最高，自带 WiFi/BLE）   - 低功耗场景：nRF52 系列 / STM32L 系列   - 高性能场景：STM32H7 系列 / RK3566 等   - 简单控制场景：STM32F103 / ATmega328
4. **阻容感选型规则**   - 必须用**通用值**：10K、4.7K、100Ω、100nF、10uF、22uF 等   - 封装统一为 **0402**（量产）或 **0603**（打样方便）   - 耐压留 2 倍余量（如 3.3V 系统用 10V 或 16V 电容）   - 电阻选 **1% 精度**（价格几乎无差异）
5. **电源芯片选型规则**   - LDO 选主流：AMS1117、AP2112、SY8089、ME6211   - 充电管理：TP4056（线性，简单）/ IP2312（开关，高效）   - DC-DC 选主流：MP1584、SY8120、RT8059   - 输出功率留 30% 余量
6. **通信模块选型规则**   - WiFi+BLE：ESP32 系列（最便宜，生态最好）   - 纯 BLE：nRF52832 / CH582   - 4G/Cat.1：SIM7600CE / EC20 / Air780E   - LoRa：SX1276 / ASR6505
7. **传感器选型规则**   - 温湿度：DHT11（便宜）/ SHT30（精准）/ AHT20（性价比）   - 加速度/陀螺仪：MPU-6050 / ICM-42688   - 光照：BH1750 / MAX44009   - 气压：BMP280 / BMP388
8. **模块类选型规则**   - 屏幕：ST7789（SPI，便宜）/ ILI9341（并口，快）   - Camera：OV2640（2MP，便宜）/ OV8856（8MP，主流）/ GC2145（2MP，替代）   - GPS：L76K / ATGM336H
##### 封装选择规则
| 产量 | 推荐封装 | 原因 ||-----|---------|------|| < 100 套 | 0805 / SOP | 手工焊接方便 || 100-5000 套 | 0603 / QFN | 贴片方便，成本适中 || > 5000 套 | 0402 / QFN/BGA | 体积小，成本低 |
如果用户没说产量，默认按 0603/QFN 选。
##### 每个元器件必须输出
| 字段 | 说明 | 例子 ||-----|------|------|| **型号** | 精确的元器件型号 | `ESP32-S3-WROOM-1-N8R8` || **品牌/厂商** | 芯片厂商 | `Espressif` || **分类** | 见下方统一分类 | `MCU` || **封装** | 具体封装 | `QFN-56` || **关键参数** | 一句话描述核心参数 | `240MHz 双核, WiFi+BLE5, 8MB PSRAM` || **数量/套** | 单套用量 | `1` || **选型理由** | 为什么选这个 | `自带 WiFi/BLE，省通信模块成本` |
**统一分类标签**：
| 分类 | 包含 ||-----|------|| `MCU` | 微控制器、SoC || `电源` | LDO、DC-DC、充电管理、电源开关 || `传感器` | 温湿度、加速度、陀螺仪、光照、气压等 || `通信模块` | WiFi、BLE、4G、LoRa、NB-IoT 模块 || `音频` | 麦克风、功放、Codec || `显示` | 屏幕驱动、LCD/OLED 模组 || `摄像头` | Camera 模组 || `存储` | Flash、EEPROM、SD 卡座 || `阻容感` | 电阻、电容、电感 || `二极管/三极管` | LED、肖特基、MOSFET || `晶振` | 有源/无源晶振 || `连接器` | USB、排针、FPC、天线座 || `结构件` | 外壳、电池、喇叭、按键开关 || `其他` | 不属于以上分类的 |
---
**Layer 4：辅料补全与合理性检查**
在 Layer 3 的基础上，补全容易被遗漏的元器件，并做合理性检查。
##### 必须检查的辅料
| 类别 | 检查项 | 默认添加 ||-----|-------|---------|| **去耦电容** | 每个 IC 的电源引脚是否有 100nF 去耦 | 自动补全 || **上拉/下拉电阻** | I2C 总线（4.7K）、复位脚、使能脚 | 自动补全 || **ESD 保护** | USB、天线、外部接口是否有 ESD | 如有外部接口则添加 || **指示灯** | 电源指示、状态指示 | 至少 1 个电源 LED || **测试点** | 关键信号测试点 | 提醒用户预留 || **调试接口** | SWD/JTAG、串口 | 至少预留 SWD || **保险丝** | 电源输入端 | 添加自恢复保险丝 || **滤波电容** | 电源输出端的大容量滤波 | 根据功率添加 |
##### 合理性检查
1. **电源链路完整性**：从输入到每个 IC，电压是否覆盖2. **通信接口匹配**：MCU 和外设的通信协议是否兼容（SPI/I2S/I2C/UART）3. **IO 数量够不够**：统计 MCU 的 GPIO 需求，是否超出选型4. **功耗预估**：电池供电时，计算总功耗，评估续航5. **成本预估**：根据经验估算 BOM 总成本，是否在预算内   - 阻容感：¥0.01-0.05/颗   - 通用 IC（LDO/运放）：¥0.5-3/颗   - MCU：¥5-30/颗   - 模块类：¥15-120/个   - 电池：¥5-30/个
如果成本超出预算，给出降本建议（换型号、砍功能、换供应商）。

#### B.3 输出 BOM 清单 + 配置选择

4 层推理全部完成后，执行以下流程：

##### Step 1：生成标准版 BOM

根据 B.1 收集的成本偏好，生成对应档次的 BOM：
- 成本偏好=优先低成本 → 生成**经济版** BOM（选国产替代、精简外设）
- 成本偏好=优先高性能 → 生成**高性能版** BOM（国际大厂、更强参数）
- 成本偏好=平衡 → 生成**标准版** BOM（性价比最优）

##### Step 2：生成对比版 BOM

自动生成**另一个版本**的 BOM 作为对比：
- 如果主版本是经济版 → 额外生成高性能版
- 如果主版本是高性能版 → 额外生成经济版
- 如果主版本是标准版 → 额外生成经济版和高性能版

##### Step 3：单套成本经验预估

对两个版本分别计算单套成本（经验值，不做搜索）：
- 阻容感：¥0.01-0.05/颗
- 通用 IC（LDO/运放）：¥0.5-3/颗
- MCU：¥5-30/颗
- 通信模块：¥8-35/个
- 传感器：¥2-15/颗
- 模块类：¥15-120/个
- 电池：¥5-30/个
- 结构件：¥5-20/套

##### Step 4：用 show_widget 展示可视化 BOM 表格

对两个版本的 BOM 分别调用  渲染内联可视化表格（不生成独立 HTML 文件）：

- 先调用  加载  模块
- 再调用  渲染 HTML 表格，包含：序号、型号、品牌、分类、封装、关键参数、数量/套、选型理由
- 表格顶部标注版本名称和单套预估成本

**show_widget 示例**：
```
read_me(modules=["diagram"])

show_widget(
    title="BOM_经济版",
    widget_code="""<svg viewBox="0 0 680 400">...</svg>""",
    loading_messages=["生成 BOM 清单", "计算成本预估", "渲染表格"]
)
```

##### Step 5：让用户选择配置

展示两个版本后，用  让用户选择：

```我为你生成了 2 个版本的 BOM 方案：

【经济版】单套预估 ¥XX
- MCU: ESP32-C3（性价比）
- 精简非必要外设

【标准版】单套预估 ¥XX
- MCU: ESP32-S3（平衡）
- 完整功能

【高性能版】单套预估 ¥XX
- MCU: ESP32-S3 + 外置 PSRAM
- 适合性能敏感场景```

```请选择要进一步比价的版本：
AskUserQuestion({
    question: "请选择要进一步比价的 BOM 版本",
    header: "BOM版本",
    options: [
        {label: "经济版（¥XX/套）", description: "成本最低，适合成本敏感场景"},
        {label: "标准版（¥XX/套（推荐）", description: "性价比最优"},
        {label: "高性能版（¥XX/套）", description: "性能最强，适合性能敏感场景"},
        {label: "两个都要", description: "同时比价两个版本，耗时翻倍"}
    ]
})
```

##### Step 6：生成 CSV 文件

用户选择后，生成对应版本的 CSV 文件供第3步消费：
```python
import csv
bom_data = [
    {"型号": "ESP32-S3-WROOM-1-N8R8", "品牌": "Espressif", "分类": "MCU", "封装": "QFN-56", "数量": 1, "关键参数": "240MHz, WiFi+BLE5", "选型理由": "自带WiFi/BLE"},
]
with open('BOM_反推.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=["型号", "品牌", "分类", "封装", "数量", "关键参数", "选型理由"])
    writer.writeheader()
    writer.writerows(bom_data)
```

**用户选择后，将选中版本的 BOM 清单交给「第3步：查询价格」进行全网比价。**
---### 第3步：查询价格（按元器件类别分级）
对每个BOM元器件，先判断类别，再走不同的查询流程。
#### 元器件分类规则
| 分类 | 包含 | 查询策略 ||------|------|---------|| **高价值元器件** | MCU/SoC、电源管理IC、通信模块(WiFi/BLE/4G)、传感器芯片、屏幕驱动IC、Camera模组、Flash芯片 | 强查询：四商城（立创→LCSC→华秋→云汉），全失败则买手→经验值 || **低价值元器件** | 阻容感(电阻/电容/电感)、二极管/LED、晶振、连接器、结构件(外壳/电池/按键) | 轻查询：买手全网优先→经验值 |
**高价值元器件判定标准（满足任一即为高价值）**：- 单颗价格 > ¥2（经验估算）- 属于以下分类之一：MCU、电源、通信模块、传感器、音频IC、显示驱动、摄像头、存储IC
**低价值元器件判定标准**：- 单颗价格 ≤ ¥2（经验估算）- 属于以下分类之一：阻容感、二极管/三极管、晶振、连接器、结构件
---
#### 高价值元器件：强查询流程

> **重要规则（v8.0.0）**：高价值元器件在完成博查+IQS双源交叉验证后，**强制进行 WebFetch 商城链接验证**，不跳过。
> 即便两源一致、即便有参考价格，也要验证商城实时价，确保核心元器件的价格准确性。

> **核心规则（v8.2.0）**：高价值元器件查询**最高优先级**为立创商城 BOM 批量配单（需已登录），次优先级为博查+IQS双源交叉验证。
> 立创 BOM 批量配单可一次性获取立创实时价格（含2000+档位），是最权威的立创价格来源。
> 如果立创未登录或 Cookie 失效，降级到博查+IQS双源交叉验证 + WebFetch 商城验证。

对每颗高价值元器件，执行以下流程：

```
对每颗高价值元器件：

  ★ ① 立创商城 BOM 批量配单（最高优先，需已登录）
     → Cookie存在 → 执行配单
     → Cookie不存在 → 提示用户登录立创商城 → 降级到步骤②

  ② 博查 + IQS /ai/answer 并行查询（--cross-verify 模式）
     调用: python3 scripts/iqs_search.py '{型号} 价格 批量' --cross-verify --json
     ↓ 并行执行，总耗时取 max（博查~7s / IQS~11s）

  ③ 交叉验证结果处理（记录为参考，不作为最终采纳依据）：
     a) 两源一致（价差 < 20%）→ 记录为参考价格，标注"交叉验证一致参考" ✅
     b) IQS 独有价格 → 补充记录，标注"IQS补充"
     c) 博查独有价格 → 记录，标注"博查搜索"（待验证）
     d) 两源存疑（价差 ≥ 20%）→ 标注"存疑"，作为优先验证项
     e) 两源均无结果 → 进入降级流程（步骤④）

  ④ ★ WebFetch 商城链接验证（高价值元器件强制执行）
     ↓ 从博查/IQS 返回的商城链接中，按优先级筛选：
         优先级1：立创商城链接（szlcsc.com）
         优先级2：华秋商城链接（hqchip.com）
         优先级3：云汉芯城链接（ickey.cn）
         优先级4：LCSC国际站链接（lcsc.com）
       → 按优先级逐个 WebFetch，有一个成功即停止
       → 验证结果处理：
           WebFetch 成功 + 价格差异 < 10% → 采纳搜索价格，标注"已验证✅"
           WebFetch 成功 + 价格差异 ≥ 10% → 采纳商城实时价，标注"已更新🔄"
           WebFetch 成功 + 有存疑标记 → 优先采纳商城价，标注"已验证✅（商城实时）"
           WebFetch 全部失败 → 保留步骤②价格，标注"未验证⚠️"

     ↓ 如果④全失败（403/超时/无数据），进入降级

  ⑤ 立创商城（WebFetch → Playwright MCP 降级）
     ↓ 失败（403 / 超时 / 无数据）

  ⑥ LCSC 国际站（WebFetch）
     ↓ 失败

  ⑦ 买手全网比价
     ↓ 失败

  ⑧ 经验估算（标注"经验估算，未经商城验证"）
```

---
##### 来源0：立创商城 BOM 批量配单（★最高优先）

> **这是高价值元器件的查询入口**。通过 Playwright MCP 恢复用户立创商城登录态，批量提交 BOM 配单，可一次性获取立创实时阶梯价格（含2000+档位），无需逐型号搜索。

**前置条件**：
- ✅ Playwright MCP 已配置（见上方 MCP 配置指引）
- ✅ 用户拥有立创商城账号
- ✅ 立创商城 Cookie 已保存到 `~/.workbuddy/skills/bom-price-checker/data/lcsc_cookies.json`

**Cookie 保存方法**：
首次使用后，Cookie 会自动保存在上述路径，后续查询直接复用。如果 Cookie 文件不存在或为空，脚本会提示用户手动登录并保存。

**核心优势**：
- 🔓 **实时价格**：直接获取立创商城后台实时数据，含2000+批量档位
- 📦 **库存状态**：实时反映立创当前库存是否充足
- 🤖 **自动化**：批量提交 BOM，一次查询多颗元器件
- 🔐 **需登录**：价格数据与用户账号绑定，避免反爬拦截

**操作流程**：

```
Step 1：检查 Cookie 是否存在
  → 读取 ~/.workbuddy/skills/bom-price-checker/data/lcsc_cookies.json
  → 如果不存在或为空：
       【被动提示】"立创商城尚未登录，部分元器件可能无法查到最优惠价格。
                   如需使用立创BOM批量配单（最高优先级），请在立创商城完成一次登录，
                   然后重新执行查询。"
       → 不阻塞流程，降级到步骤②（博查+IQS）

Step 2：加载 Cookie 并建立浏览器上下文
  → 读取 Cookie 文件
  → 用 page.context().addCookies() 注入（必须用此方式，不能用 document.cookie）

Step 3：绕过 ACL 访问 BOM 页面
  → 先访问 https://www.szlcsc.com/ 建立上下文
  → 再导航到 https://bom.szlcsc.com/bom.html?from=dh（直接访问会403）

Step 4：批量提交 BOM 配单
  → 格式：型号 封装 数量pcs（如：ESP32-S3-WROOM-1-N8 N8 1pcs）
  → 每颗元器件一行，全量提交（避免逐颗查询耗时）
  → 点击"开始配单"按钮

Step 5：处理配单结果弹窗
  → 定位 .el-dialog 内的确定按钮，点击完成

Step 6：提取价格结果
  → 解析配单结果表格，提取：型号、品牌、单价（含税）、匹配状态
```

**Playwright MCP 代码示例**：
```javascript
const fs = require('fs');
const os = require('os');
const cookiePath = os.homedir() + '/.workbuddy/skills/bom-price-checker/data/lcsc_cookies.json';

// Step 1: 检查 Cookie 文件
let cookies = [];
if (fs.existsSync(cookiePath)) {
  const raw = fs.readFileSync(cookiePath, 'utf8');
  const parsed = JSON.parse(raw);
  if (Array.isArray(parsed) && parsed.length > 0) cookies = parsed;
}

if (cookies.length === 0) {
  // 通知主流程：未登录，降级
  return { status: 'NO_COOKIES', message: '立创商城未登录，请先登录' };
}

// Step 2: 注入 Cookie
await page.context().addCookies(cookies);

// Step 3: 绕过 ACL 访问 BOM 页面
await page.goto('https://www.szlcsc.com/', { waitUntil: 'networkidle' });
await page.goto('https://bom.szlcsc.com/bom.html?from=dh', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);

// Step 4: 输入 BOM（每颗一行）
const bomText = bomItems.map(item => `${item.型号} ${item.封装 || 'N/A'} ${item.数量 || 1}pcs`).join('\n');
const textarea = await page.locator('textarea').first();
await textarea.fill(bomText);
await page.getByText('开始配单').click();

// Step 5: 等待并处理结果弹窗
await page.waitForTimeout(3000);
const dialog = page.locator('.el-dialog');
if (await dialog.isVisible()) {
  await dialog.locator('button:has-text("确定")').click();
  await page.waitForTimeout(1000);
}

// Step 6: 提取价格结果
const rows = await page.locator('.bom-table tr, table tr').all();
const prices = {};
for (const row of rows) {
  const cells = await row.locator('td').allTextContents();
  if (cells.length >= 3) {
    const model = cells[0].trim();
    const priceMatch = cells[2].match(/¥?([\d.]+)/);
    if (priceMatch) prices[model] = parseFloat(priceMatch[1]);
  }
}
return { status: 'OK', prices };
```

**Cookie 文件格式**（`lcsc_cookies.json`，关键 Cookie）：
```json
[
  { "name": "customerCode",       "value": "12451540A",       "domain": "www.jlc.com",  "path": "/" },
  { "name": "isLoginCustomerFlag", "value": "12451540A",       "domain": ".szlcsc.com",  "path": "/" },
  { "name": "PROD-JLC-CAS-SID",   "value": "CAS-SID-xxx",     "domain": ".jlc.com",     "path": "/", "sameSite": "None", "secure": true }
]
```

**登录提示文案（被动触发，不阻塞流程）**：
```
⚠️ 立创商城尚未登录
BOM 价格查询将使用次优先级方案（博查+IQS双源搜索）。
如需启用最高优先级的立创BOM批量配单，请：
1. 访问立创商城官网完成一次登录（https://www.szlcsc.com/）
2. 登录后重新执行查询
登录后 Cookie 将自动保存，后续无需重复登录。
```

**登录引导触发条件**：
- Cookie 文件不存在
- Cookie 文件为空数组
- Playwright 访问 BOM 页面后检测到登录墙（页面包含"登录"关键字）

**注意事项**：
- Cookie 有效期通常为 7-30 天，过期后需重新登录
- Cookie 注入了但仍跳转登录页，说明 Cookie 已过期，需重新登录

---> **设计说明**：
> - 高价值元器件（>¥2）必须经过商城实时价格验证，确保采购决策的准确性
> - 博查+IQS 交叉验证的目的是**提供参考价格和商城链接**，而非最终采纳价格
> - WebFetch 验证是**强制步骤**，即使两源完全一致也要执行
> - 中等价值元器件（¥0.5-2）可跳过强制验证，仅在存疑时验证
> - 每颗元器件查询完毕后，**随机等待 2~5 秒**，再查询下一颗（避免触发 IP 频率限制）
---
##### 来源1：立创商城 单型号搜索（降级方案）

> **注意**：此来源为步骤⑤的降级方案。当来源0（BOM批量配单）Cookie缺失、失效或失败时使用。
> BOM批量配单无需逐型号搜索，是更高效的查询方式。

- **方法**：优先 WebFetch，失败则用 Playwright MCP 降级
- **无需登录**，价格公开
- **搜索 URL**：`https://www.szlcsc.com/products/search?keyword={model}`
- **优先提取 2000+ 档位价格**
**WebFetch 方式**（首选）：```pythonresult = WebFetch(    url=f'https://www.szlcsc.com/products/search?keyword={model}',    prompt='提取页面中的所有型号、价格阶梯（特别是2000+档位）、库存信息，以及每个型号的商品详情页链接')```
**Playwright MCP 方式**（WebFetch 失败时降级使用）：```javascriptawait page.goto(`https://www.szlcsc.com/products/search?keyword=${model}`);await page.waitForLoadState('networkidle');await page.waitForTimeout(2000);
const results = await page.evaluate(() => {  const items = [];  document.querySelectorAll('.product-item, [class*="product"]').forEach(item => {    const title = item.querySelector('.product-title, [class*="title"]')?.innerText || '';    const price = item.querySelector('.product-price, [class*="price"]')?.innerText || '';    const link = item.querySelector('a')?.href || '';    items.push({ title, price, link });  });  return items;});```
**失败判定**：返回 403、超时、或返回内容中无价格数据。
---
##### 来源2：LCSC 国际站 (lcsc.com)
- **方法**：WebFetch（推荐），或 curl 调用无认证搜索 API- **无需登录**，价格公开- **货币**：USD（按 7.25 换算为 CNY）- **搜索 URL**：`https://www.lcsc.com/products?q={model}`- **优先提取 2000+ 档位价格**
**WebFetch 方式**（推荐）：```pythonresult = WebFetch(    url=f'https://www.lcsc.com/products?q={model}',    prompt='Extract all price tiers especially 2000+ price in USD, product detail page URL, and convert USD to CNY using rate 7.25')```
**备用：LCSC 无认证搜索 API**（返回 JSON，包含商品页面 URL）：```bashcurl -s "https://lcsc.com/api/global/additional/search?q={model}"```解析返回的 JSON，获取商品详情页 URL 后，再用 WebFetch 访问详情页提取阶梯价。
**注意**：- 国际站与立创商城（szlcsc.com）的库存和价格可能不同- 如果 curl 返回的 JSON 中包含商品详情页链接，优先访问详情页获取完整阶梯价
---
##### 来源3：华秋商城 (hqchip.com)
- **方法**：优先 WebFetch，失败则用 Playwright MCP 降级- **无需登录**即可看到阶梯价和库存- **搜索 URL**：`https://www.hqchip.com/search/{model}.html`- **优先提取 2000+ 档位价格**
**WebFetch 方式**（首选）：```pythonresult = WebFetch(    url=f'https://www.hqchip.com/search/{model}.html',    prompt='提取搜索结果中的型号、阶梯价格（特别是2000+档位）、库存信息，以及商品详情页链接')```
**Playwright MCP 方式**（WebFetch 失败时降级使用）：```javascriptawait page.goto(`https://www.hqchip.com/search/${model}.html`);await page.waitForLoadState('networkidle');await page.waitForTimeout(2000);
const results = await page.evaluate(() => {  const items = [];  document.querySelectorAll('.goods-list-item, [class*="search-result"]').forEach(card => {    const title = card.querySelector('.goods-title, [class*="title"]')?.innerText || '';    const priceText = card.innerText;    const link = card.querySelector('a')?.href || '';    items.push({ title, priceText, link });  });  return items;});```
---
##### 来源4：云汉芯城 (ickey.cn)
- **方法**：优先 WebFetch，失败则用 Playwright MCP 降级- **无需登录**即可看到完整阶梯价- **搜索 URL**：`https://search.ickey.cn/yuncang/search/index?keyword={model}`- **优先提取 2000+ 档位价格**
**WebFetch 方式**（首选）：```pythonresult = WebFetch(    url=f'https://search.ickey.cn/yuncang/search/index?keyword={model}',    prompt='提取搜索结果中的型号、阶梯价格（特别是2000+档位）、库存数量，以及商品详情页链接')```
**Playwright MCP 方式**（WebFetch 失败时降级使用）：```javascriptawait page.goto(`https://search.ickey.cn/yuncang/search/index?keyword=${model}`);await page.waitForLoadState('networkidle');await page.waitForTimeout(3000);
const results = await page.evaluate(() => {  const items = [];  document.querySelectorAll('[class*="product-item"], [class*="goods-item"]').forEach(card => {    const priceItems = card.querySelectorAll('li');    const prices = [];    priceItems.forEach(li => {      const text = li.innerText.trim();      const match = text.match(/^(\d+)\+\s*￥([\d.]+)$/);      if (match) {        prices.push({ qty: match[1] + '+', price: match[2] });      }    });    const link = card.querySelector('a')?.href || '';    items.push({ prices, link });  });  return items;});```
**如果 MCP 未配置或启动失败**：- 跳过云汉芯城- 记录为"MCP 未配置，已跳过"
---
##### 来源5：买手全网比价（兜底）
- **方法**：调用买手搜索（内置脚本） 脚本- **适用场景**：博查搜索也未获取到价格时的进一步兜底- **特别适合**：模块类（4G 模块、GPS 模块）、消费级电子元件
**调用方式**：```bashpython3 scripts/search_price.py --keyword='{型号}'```
**参数说明**：- `--source=0`：搜索全部平台（淘宝、京东、拼多多、1688 等）- `--keyword='{型号}'`：要搜索的型号或关键词
**返回格式**：CSV，包含以下字段：- `actualPrice`：实际价格（含优惠券）- `source`：来源平台（1=淘宝，2=京东，3=拼多多，10=1688）- `title`：商品标题- `shopName`：店铺名称
**处理逻辑**：1. 运行命令，获取 CSV 结果2. 解析 CSV，提取所有商品的实际价格（actualPrice）3. 取所有平台的最低实际价格作为"买手全网最低价"4. 如果返回空或报错，记录为"未获取到"，继续下一来源
---
##### 来源6：博查AI搜索（胜算云联网搜索）
> **这是 4 个商城全部反爬失败后的首选降级方案，比买手更高效。**
- **方法**：调用 `scripts/shengsuan_search.py` 脚本- **原理**：通过胜算云 API 联网搜索，让 AI 大模型自动搜索并提取各平台价格- **搜索引擎**：博查AI搜索（中文优化，覆盖国内商城）- **一次搜索覆盖**：华秋、1688、维库电子市场网等多个平台- **返回结构化数据**：价格 + 档位 + 来源平台 + 商品链接- **已验证**：华秋商城链接可正常打开，价格与商城一致
**调用方式**：```bash# 博查AI搜索（默认，推荐）python3 scripts/shengsuan_search.py '{型号} 价格' --json
# 深度搜索（覆盖更多渠道，包括 Mouser、DigiKey 等）python3 scripts/shengsuan_search.py '{型号} 价格' --depth advanced --json
# 自动模式（博查无结果自动降级 Tavily 全球搜索）python3 scripts/shengsuan_search.py '{型号} 价格' --engine auto --json```
**返回格式**：JSON，核心字段：- `parsed_prices`：解析后的价格数组  - `source`：来源平台名称  - `price`：单价（数字）  - `quantity`：数量档位  - `currency`：货币（CNY/USD）  - `link`：来源链接  - `note`：备注- `search_results`：搜索引擎返回的原始网页摘要（可用于补充参考）
**处理逻辑**：1. 运行脚本，获取 JSON 结果2. 从 `parsed_prices` 中提取所有价格记录3. 按 `quantity` 档位筛选最接近目标批量（默认2000+）的价格4. 在比价表中标注来源为"博查搜索"5. 保留来源链接，用户可点击跳转验证6. 如果返回空或失败，记录为"未获取到"，继续下一来源
**注意事项**：- 价格来自搜索引擎缓存，可能与商城实时价有轻微时间差- 偶尔出现型号混淆，人工复核时需注意- 标注为"博查搜索"以区别于直接商城查询- 费用：0.036¥/次（博查）
---
##### 来源7：买手全网比价（兜底）
- **当以上所有来源均失败时**，使用 AI 经验估算价格- **必须标注**：`经验估算（未经商城验证）`- **估算参考值**：
| 分类 | 经验价格范围 ||------|-------------|| 电阻(0805/0603) | ¥0.01 ~ 0.03/颗 || 电容(0805/0603) | ¥0.02 ~ 0.08/颗 || 电感 | ¥0.05 ~ 0.20/颗 || 二极管/LED | ¥0.05 ~ 0.50/颗 || 晶振 | ¥0.30 ~ 1.50/颗 || 连接器 | ¥0.10 ~ 2.00/颗 || MCU（如STM32F103） | ¥3 ~ 15/颗 || 电源IC（如AMS1117） | ¥0.50 ~ 3.00/颗 || 传感器（如MPU-6050） | ¥2 ~ 15/颗 || 通信模块（如ESP32） | ¥8 ~ 35/颗 |
---
#### 低价值元器件：轻查询流程
对每颗低价值元器件，按顺序尝试：

```对每颗低价值元器件：
  1. 买手全网比价     ↓ 失败或无结果  2. 经验估算（标注"经验值，未查商城"）```
**买手调用方式**与高价值元器件相同。
**经验估算直接给出**，无需再查商城（低价值元器件查商城的投入产出比低）。
---
#### 反爬策略
##### 策略1：请求间随机延迟
**每颗元器件查询完毕后，随机等待 2~5 秒，再查询下一颗元器件。**
```pythonimport random, timetime.sleep(random.uniform(2, 5))```
##### 策略2：商城交错查询
**不要连续查同一个商城**，而是将 BOM 清单打散，四个商城轮流查询：
```BOM 清单：[MCU, 传感器, 电源IC, 电容, 电阻, 通信模块]
查询顺序（交错）：
  元器件1 → 立创  元器件1 → LCSC（如果立创失败）  元器件1 → 华秋（如果LCSC失败）  ...  元器件2 → 立创  元器件2 → LCSC  ...```
实现方式：先对每颗元器件尝试立创，全部完成后，再对失败的尝试 LCSC，以此类推。
##### 策略3：WebFetch 失败后用 Playwright MCP 重试
```对每个商城：
  1. 先用 WebFetch 尝试（轻量快速）     ├── 成功 → 记录价格和链接     └── 失败 → 随机等 3~8 秒 → 用 Playwright MCP 重试           ├── 成功 → 记录价格和链接           └── 也失败 → 标记"被反爬限制" → 下一个商城```
##### 策略4：截图识别降级（可选，仅高价值元器件）
当 Playwright MCP 能打开页面但无法提取结构化数据时，截图让大模型识别：
```javascriptawait page.screenshot({ path: '/tmp/price_screenshot.png' });// 然后将截图交给大模型识别价格```
**注意**：- 仅对**高价值元器件**使用截图识别（值得花 token）- 低价值元器件不截图，直接经验估算- 截图识别失败不重试，直接降级
##### 策略5：连续失败后的暂停
| 情况 | 处理方式 ||------|---------|| 单次 403 | 跳过该商城，继续下一个，记录"被反爬限制" || 连续 2 个商城 403 | 暂停 10 秒，然后用 Playwright 重试 || 4 个商城全 403 | 优先降级到**博查+IQS双源交叉验证**，再买手 + 经验值 |
---
#### 价格结果标注规则
每个元器件的价格数据必须标注来源和可跳转链接：

|
| **立创BOM批量配单** | `立创BOM ¥X.XX ✅（实时） ↗` | `立创BOM ¥8.68 ✅（实时） ↗` |
| 双源验证一致 | `交叉验证 ¥X.XX ✅（博查+IQS） ↗` | `交叉验证 ¥1.23 ✅（博查+IQS） ↗` |
| IQS补充 | `IQS补充 ¥X.XX ↗` | `IQS补充 ¥6.64 ↗` |
| 存疑（价差>20%） | `存疑 ¥X.XX ⚠️（博查¥A/IQS¥B） ↗` | `存疑 ¥1.20 ⚠️（博查¥1.00/IQS¥1.50） ↗` |
| 博查搜索（已验证） | `博查 ¥X.XX ✅ ↗`（链接指向验证成功的商城页） | `博查 ¥1.23 ✅ ↗` |
| 博查搜索（已更新） | `博查 ¥X.XX 🔄 ↗`（价格已用实时价替换） | `博查 ¥1.20 🔄 ↗` |
| 博查搜索（未验证） | `博查 ¥X.XX ⚠️ ↗`（链接为博查返回的原始链接） | `博查 ¥1.25 ⚠️ ↗` |
| 立创商城 | `立创 ¥X.XX ↗`（`↗` 为可跳转链接） | `立创 ¥1.23 ↗` |
| LCSC 国际站 | `LCSC $X.XX (¥XX.XX) ↗` | `LCSC $0.17 (¥1.23) ↗` |
| 华秋商城 | `华秋 ¥X.XX ↗` | `华秋 ¥1.20 ↗` |
| 云汉芯城 | `云汉 ¥X.XX ↗` | `云汉 ¥1.25 ↗` |
| 买手全网 | `买手最低 ¥X.XX（来源：淘宝/京东/...）` | `买手最低 ¥1.15（来源：淘宝）` |
| 经验估算 | `经验估算 ¥X.XX（未经商城验证）` | `经验估算 ¥1.50（未经商城验证）` |**HTML 输出时**，`↗` 用 `<a>` 标签实现跳转。
---
路径B 完成后，将 BOM 清单交给「第4步：统一比价」。路径A（用户上传 BOM 表）也遵循相同的查询策略。
---### 第4步：统一比价
所有来源查询完成后，对每个型号：

#### 4.1 提取各平台的 2000+ 档位价格
1. **如果用户没有修改数量**，默认按 2000+ 档位比价2. **如果用户修改了数量**（如"我要100套的价格"），则提取对应档位3. **提取逻辑**：   - 立创商城：查找"2000+"档位的单价，并记录商品详情页链接   - 华秋商城：查找"2000+"档位的单价，并记录商品详情页链接   - 云汉芯城：查找"2000+"档位的单价，并记录商品详情页链接   - LCSC 国际站：查找"2000+"档位的单价（USD，需换算），并记录商品详情页链接   - 买手全网：取所有平台的最低实际价格
#### 4.2 库存不足的处理
**重要**：如果 2000+ 档位库存不足，取最低可用档位的价格。
**原因**：我们只是预估价格，不需要严格匹配库存。
**处理逻辑**：```pythondef get_best_price(prices, target_qty=2000):    """    获取最合适的价格    prices: 列表，每个元素是 {'qty': '2000+', 'price': 1.23, 'link': 'https://...'}    target_qty: 目标数量，默认 2000    """    # 1. 先找完全匹配的档位    for p in prices:        qty = parse_quantity(p['qty'])  # 解析 "2000+" -> 2000        if qty >= target_qty:            return p['price'], p['qty'], p.get('link', '')        # 2. 如果找不到匹配的档位，取最大的档位    if prices:        max_price = max(prices, key=lambda x: parse_quantity(x['qty']))        return max_price['price'], max_price['qty'] + ' (库存不足，取最低可用档位)', max_price.get('link', '')        # 3. 如果都没有，返回 None    return None, None, ''```
#### 4.3 标注最低价来源
1. **比较所有来源的价格**（立创、华秋、云汉、LCSC、买手）2. **标注最低价的平台和价格**，并附上来源链接3. **如果价格相同**，标注所有最低价来源（如"立创商城、华秋商城"）
**处理逻辑**：```pythondef compare_prices(prices_dict):    """    比较各平台价格，标注最低价来源    prices_dict: {        '立创商城': {'price': 1.23, 'link': 'https://...'},        '华秋商城': {'price': 1.20, 'link': 'https://...'},        '云汉芯城': {'price': 1.25, 'link': 'https://...'},        'LCSC国际站': {'price': 1.22, 'link': 'https://...'},        '买手全网': {'price': 1.15, 'link': None}    }    """    # 过滤掉 None 和 0    valid_prices = {k: v for k, v in prices_dict.items() if v and v['price'] and v['price'] > 0}        if not valid_prices:        return None, "所有来源均未获取到价格", []        min_price = min(valid_prices.values(), key=lambda x: x['price'])    min_sources = [k for k, v in valid_prices.items() if v['price'] == min_price['price']]        # 收集所有最低价来源的链接    min_links = [valid_prices[s]['link'] for s in min_sources if valid_prices[s].get('link')]        return min_price['price'], ', '.join(min_sources), min_links```
---### 第5步：输出结果
#### 5.1 HTML 预览（优先）
生成 HTML 表格，用 `preview_url` 工具在 WorkBuddy 窗口展示。
**表格列**：1. **序号**（1, 2, 3...）2. **型号**（如 STM32F103C8T6）3. **封装**（如 LQFP-48）4. **数量**（如 2000）5. **品牌**（如 ST）6. **立创价格（¥）**（如 1.23 ↗，点击可跳转）7. **华秋价格（¥）**（如 1.20 ↗，点击可跳转）8. **云汉价格（¥）**（如 1.25 ↗，点击可跳转）9. **LCSC国际价（¥）**（如 1.22 ↗，标注"USD×7.25"）10. **买手全网最低价（¥）**（如 1.15，标注"含优惠券"）11. **最低价来源**（如"华秋商城 ↗"）12. **分类**（可选，如"MCU"、"传感器"）13. **备注**（如"库存不足，取1000+档位" / "经验估算，未经商城验证"）
**HTML 生成代码示例**：```pythondef generate_html_table(bom_data):    """生成 HTML 表格，带来源链接"""    html = """<!DOCTYPE html><html><head>    <meta charset="UTF-8">    <title>BOM 比价单</title>    <style>        table { border-collapse: collapse; width: 100%; font-size: 13px; }        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }        th { background-color: #4CAF50; color: white; }        tr:nth-child(even) { background-color: #f2f2f2; }        .min-price { color: red; font-weight: bold; }        .exp-price { color: #999; font-style: italic; }        a { color: #1a73e8; text-decoration: none; }        a:hover { text-decoration: underline; }    </style></head><body>    <h2>BOM 比价单</h2>    <p>生成时间：""" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>    <p>比价档位：2000+ （库存不足时取最低可用档位）</p>    <table>        <tr>            <th>序号</th><th>型号</th><th>封装</th><th>数量</th><th>品牌</th>            <th>立创价格（¥）</th><th>华秋价格（¥）</th>            <th>云汉价格（¥）</th><th>LCSC国际价（¥）</th>            <th>买手全网最低价（¥）</th><th>最低价来源</th>            <th>分类</th><th>备注</th>        </tr>"""        for i, item in enumerate(bom_data, 1):        min_price, min_source, min_links = compare_prices(item['prices'])                # 立创价格单元格（带链接）        lc_price = item['prices'].get('立创商城', {})        lc_cell = f'<a href="{lc_price.get("link", "")}" target="_blank">{lc_price.get("price", "未获取")}</a>' if lc_price.get('link') else str(lc_price.get('price', '未获取'))                # 华秋价格单元格        hq_price = item['prices'].get('华秋商城', {})        hq_cell = f'<a href="{hq_price.get("link", "")}" target="_blank">{hq_price.get("price", "未获取")}</a>' if hq_price.get('link') else str(hq_price.get('price', '未获取'))                # 云汉价格单元格        yh_price = item['prices'].get('云汉芯城', {})        yh_cell = f'<a href="{yh_price.get("link", "")}" target="_blank">{yh_price.get("price", "未获取")}</a>' if yh_price.get('link') else str(yh_price.get('price', '未获取'))                # LCSC价格单元格        lcsc_price = item['prices'].get('LCSC国际站', {})        lcsc_cell = f'<a href="{lcsc_price.get("link", "")}" target="_blank">{lcsc_price.get("price", "未获取")}</a>' if lcsc_price.get('link') else str(lcsc_price.get('price', '未获取'))                # 最低价来源单元格（带链接）        source_cell = min_source        if min_links:            source_cell = ' + '.join([f'<a href="{link}" target="_blank">{min_source}</a>' for link in min_links])                html += f"""        <tr>            <td>{i}</td>            <td>{item['model']}</td>            <td>{item.get('package', '')}</td>            <td>{item.get('quantity', 2000)}</td>            <td>{item.get('brand', '')}</td>            <td>{lc_cell}</td>            <td>{hq_cell}</td>            <td>{yh_cell}</td>            <td>{lcsc_cell}</td>            <td>{item['prices'].get('买手全网', '未获取')}</td>            <td class="min-price">{source_cell}</td>            <td>{item.get('category', '')}</td>            <td>{item.get('remarks', '')}</td>        </tr>"""        html += """    </table></body></html>"""    return html```
**使用 preview_url 工具展示**：```pythonhtml_content = generate_html_table(bom_data)html_path = '/Users/lizhengan/WorkBuddy/2026-05-11-task-10/BOM_比价单.html'with open(html_path, 'w', encoding='utf-8') as f:    f.write(html_content)
preview_url(url=html_path)```
#### 5.2 Excel 文件（可选）
如果用户需要，生成 .xlsx 文件。
**文件命名**：`BOM_比价单_YYYYMMDD_HHMMSS.xlsx`示例：`BOM_比价单_20260511_103045.xlsx`
**Sheet1：比价结果**| 序号 | 型号 | 封装 | 数量 | 品牌 | 立创价格（¥） | 华秋价格（¥） | 云汉价格（¥） | LCSC国际价（¥） | 买手全网最低价（¥） | 最低价来源 | 分类 | 备注 |
**Sheet2：各平台详细阶梯价**| 型号 | 平台 | 1+ | 10+ | 100+ | 500+ | 1000+ | 2000+ | 库存 | 商品链接 |
**Sheet3：价格来源说明**| 来源 | 获取方式 | 可靠性 | 备注 ||------|---------|------|------|| 博查AI搜索（已验证） | 胜算云+WebFetch验证 | ★★★★☆ | 首选，商城链接验证后可信 || 博查AI搜索（未验证） | 胜算云脚本 | ★★★☆☆ | 搜索缓存价，可能有时间差 || 立创商城 | WebFetch / Playwright | ★★★★☆ | 博查无结果时的补充 || LCSC国际站 | WebFetch / API | ★★★☆☆ | USD需换算，博查无结果时补充 || 买手全网 | 买手脚本 | ★★☆☆☆ | 消费级参考价 || 经验估算 | AI推理 | ★☆☆☆☆ | 仅供预算参考 |
---