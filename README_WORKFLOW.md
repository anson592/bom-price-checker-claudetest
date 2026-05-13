# BOM 询价→报告 标准工作流

## 整体流程

```
询价完成
  ↓
填写输入 JSON（包含商城价/电商价原始数据）
  ↓
python3 build_bom_json.py data/xxx-query.json
  ↓
输出标准 JSON（直接给 generate_report.py 用）
  ↓
python3 generate_report.py data/xxx_2026-05-13.json
  ↓
生成 HTML 报告（可预览/分享）
```

---

## 第一步：填写输入 JSON

询价完成后，填写以下格式的输入文件（参考 `schema/bom-input-example.json`）：

```json
{
  "project": "项目名称",
  "date": "2026-05-13",
  "quantity": "2000套",
  "total_quantity": "100000",
  "batch_quantity": "5000",
  "versions": ["经济版", "标准版", "高性能版"],
  "selected_version": "高性能版",
  "ai_suggestion": "AI推荐建议",
  "risk_tags": [
    {"tag": "风险描述", "level": "high", "desc": "详细说明"}
  ],
  "items": [
    {
      "id": 1,
      "category": "MCU",
      "is_variant": true,
      "func_impact": "...",
      "exp_impact": "...",
      "user_value": 5,
      "note": "...",
      "variants": [
        {
          "version": "经济版",
          "brand": "Espressif",
          "package": "SMD-18",
          "part_number": "ESP32-C3-MINI-1-N4",
          "description": "...",
          "price_market": 8.5,           // ← 询价填写
          "market_source": "立创商城",      // ← 询价填写
          "market_url": "https://...",      // ← 询价填写（仅确认商城才有）
          "price_ecommerce": 12,            // ← 询价填写
          "found": true,                   // ← 询价填写
          "func_impact_score": 50,
          "exp_impact_score": 50
        }
      ]
    },
    {
      "id": 7,
      "category": "接口",
      "is_variant": false,
      "brand": "-",
      "package": "SMD",
      "part_number": "USB-C 插座 16P",
      "description": "...",
      "price_market": 1.5,
      "market_source": "经验估算",
      "market_url": "",
      "price_ecommerce": 2.5,
      "found": false,
      "note": "经验估算",
      "price_estimated_experience": 1.27
    }
  ]
}
```

### 字段说明

| 字段 | 填写人 | 说明 |
|------|--------|------|
| `price_market` | 询价 | 商城价（立创/华秋/云汉/LCSC 最低） |
| `market_source` | 询价 | 商城价来源描述，如"立创商城"、"华秋商城" |
| `market_url` | 询价 | 商城确认链接，**仅确认商城来源才填** |
| `price_ecommerce` | 询价 | 电商价（买手全网最低含券） |
| `found` | 询价 | `true`=搜到真实价格，`false`=只有经验估算 |
| `price_estimated_experience` | 询价 | 经验估算价（无搜索价时使用） |

---

## 第二步：生成标准 JSON

```bash
cd /Users/lizhengan/Desktop/赢他
python3 build_bom_json.py data/xxx-query.json
```

**自动计算字段：**
- `price_estimated` = `min(price_market, price_ecommerce) × 0.85`（有搜索价时）
- `price_estimated` = `price_estimated_experience`（无搜索价时）
- `source` / `source_url` = 仅当 `market_source` 含"立创/华秋/云汉/LCSC"才保留
- `cost_ratio` = 在所有 item 处理完后自动计算

输出文件：`data/<项目名>_<日期>.json`

---

## 第三步：生成 HTML 报告

```bash
cd /Users/lizhengan/Desktop/赢他
python3 generate_report.py data/<项目名>_<日期>.json
```

输出文件：`data/<项目名>_<日期>_report.html`

在 WorkBuddy 中用 `preview_url` 预览。

---

## 文件清单

| 文件 | 作用 |
|------|------|
| `schema/bom-output-schema.json` | 标准输出 JSON Schema（对接模板） |
| `schema/bom-input-example.json` | 输入 JSON 示例（询价填写） |
| `build_bom_json.py` | 输入→标准输出 转换脚本 |
| `generate_report.py` | 标准 JSON→HTML 报告 生成脚本 |
| `report-template.html` | HTML 报告模板 |
