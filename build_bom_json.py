#!/usr/bin/env python3
"""
BOM 询价结果汇总脚本
=================================
输入：BOM 清单 JSON（询价人员填写价格）
输出：标准 BOM JSON（直接给 generate_report.py 用）

用法:
  python3 build_bom_json.py data/my-query.json
  python3 build_bom_json.py --test   # 用示例数据测试

输入 JSON 格式（v9.0.0 新版）：
{
  "project": "项目名称",
  "items": [
    {
      "is_variant": true,
      "variants": [
        {
          "version": "经济版",
          "price_mall": 8.5,          // 商城价（立创/华秋取最低，查不到留空）
          "mall_source": "立创商城",    // 商城来源（立创/华秋/云汉/LCSC）
          "mall_url": "https://...",   // 商城链接（可点击）
          "price_ai": 12,              // AI价（博查/IQS）
          "ai_source": "博查",         // AI来源：博查/iqs/经验预估（无链接）
          "found": true
        }
      ]
    }
  ]
}

输出 JSON 自动计算：
  - 小计价 = price_mall（优先）；price_mall 为空则用 price_ai
  - mall_source / mall_url = 仅当商城来源是确认商城才有可点击链接
  - ai_source = 文本描述，无链接
  - cost_ratio = 在所有 item 处理完后计算
"""

import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.resolve()

# 确认商城白名单（含这些关键词的 source 才有可点击链接）
CONFIRMED_SHOP_KEYWORDS = ["立创", "华秋", "云汉", "LCSC", "lcsc"]


def is_confirmed_shop(source: str) -> bool:
    if not source:
        return False
    return any(kw in source for kw in CONFIRMED_SHOP_KEYWORDS)


def calc_unit_price(mall_price, ai_price):
    """计算小计价：优先商城价，没有才用AI价"""
    if mall_price is not None:
        return round(mall_price, 2)
    elif ai_price is not None:
        return round(ai_price, 2)
    return None


def process_item(in_item: dict) -> dict:
    """处理单个 item（shared 或 variant parent），返回输出格式"""
    # 过滤掉不需要透传的字段
    out = {k: v for k, v in in_item.items()
            if k not in ("mall_source", "mall_url", "ai_source",
                         "price_estimated_experience", "variants")}

    if in_item.get("is_variant"):
        # 处理 variants
        new_variants = []
        for v in in_item.get("variants", []):
            nv = {k: val for k, val in v.items()
                   if k not in ("mall_source", "mall_url", "ai_source",
                                "price_estimated_experience")}

            mall = v.get("price_mall")
            ai = v.get("price_ai")
            nv["price_unit"] = calc_unit_price(mall, ai)

            # mall_source / mall_url：仅确认商城才有可点击链接
            ms = v.get("mall_source")
            mu = v.get("mall_url")
            if is_confirmed_shop(ms) and mu:
                nv["mall_source"] = ms
                nv["mall_url"] = mu
            else:
                nv["mall_source"] = None
                nv["mall_url"] = None

            # ai_source：AI来源描述，无链接
            nv["ai_source"] = v.get("ai_source")

            nv.setdefault("found", mall is not None or ai is not None)
            new_variants.append(nv)

        out["variants"] = new_variants
    else:
        # shared item
        mall = in_item.get("price_mall")
        ai = in_item.get("price_ai")
        out["price_unit"] = calc_unit_price(mall, ai)

        # mall_source / mall_url：仅确认商城才有可点击链接
        ms = in_item.get("mall_source")
        mu = in_item.get("mall_url")
        if is_confirmed_shop(ms) and mu:
            out["mall_source"] = ms
            out["mall_url"] = mu
        else:
            out["mall_source"] = None
            out["mall_url"] = None

        # ai_source：AI来源描述，无链接
        out["ai_source"] = in_item.get("ai_source")

        out.setdefault("found", mall is not None or ai is not None)

    return out


def calc_cost_ratios(items: list) -> list:
    """计算 cost_ratio（需要全部 price_unit 都就绪）"""
    total = sum(
        (v.get("price_unit") or 0)
        for item in items
        for v in ([item] if not item.get("is_variant") else item.get("variants", []))
    )
    if total == 0:
        return items

    results = []
    for item in items:
        out = dict(item)
        if item.get("is_variant"):
            new_variants = []
            for v in item["variants"]:
                nv = dict(v)
                ratio = (nv.get("price_unit") or 0) / total * 100
                nv["cost_ratio"] = round(ratio, 1)
                new_variants.append(nv)
            out["variants"] = new_variants
        else:
            ratio = (item.get("price_unit") or 0) / total * 100
            out["cost_ratio"] = round(ratio, 1)
        results.append(out)
    return results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n示例输入: schema/bom-input-example.json")
        sys.exit(0)

    input_path = sys.argv[1]
    if not Path(input_path).exists():
        print(f"错误: 文件不存在: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📥 读取: {input_path}")
    print(f"   项目: {data.get('project', '?')}")
    print(f"   器件: {len(data.get('items', []))} 项")

    # 处理 items
    items_out = [process_item(it) for it in data["items"]]
    items_out = calc_cost_ratios(items_out)

    # 组装输出
    out_data = {
        "project":         data.get("project", ""),
        "date":            data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "query_time":      datetime.now().strftime("%H:%M"),
        "quantity":        data.get("quantity", ""),
        "total_quantity":  data.get("total_quantity", ""),
        "batch_quantity":  data.get("batch_quantity", ""),
        "versions":        data.get("versions", []),
        "selected_version": data.get("selected_version", ""),
        "ai_suggestion":  data.get("ai_suggestion", ""),
        "risk_tags":       data.get("risk_tags", []),
        "items":           items_out,
    }

    # 输出路径
    out_name = f"{out_data['project']}_{out_data['date']}.json"
    out_name = re.sub(r'[\\/:*?"<>|]', '_', out_name)
    out_path = SCRIPT_DIR / "data" / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 输出: {out_path}")

    # 顺便生成报告
    report_script = SCRIPT_DIR / "generate_report.py"
    if report_script.exists():
        import subprocess
        result = subprocess.run(
            ["python3", str(report_script), str(out_path)],
            capture_output=True, text=True, cwd=str(SCRIPT_DIR)
        )
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                print(f"   {line}")
        if result.stderr:
            print("   警告:", result.stderr[:300])


if __name__ == "__main__":
    main()
