#!/usr/bin/env python3
"""
BOM 询价结果汇总脚本
=================================
输入：BOM 清单 JSON（询价人员填写价格）
输出：标准 BOM JSON（直接给 generate_report.py 用）

用法:
  python3 build_bom_json.py data/my-query.json
  python3 build_bom_json.py --test   # 用示例数据测试

输入 JSON 格式：
{
  "project": "项目名称",
  "items": [
    {
      "is_variant": true,
      "variants": [
        {
          "version": "经济版",
          "price_market": 8.5,          // 商城价（立创/华秋/云汉/LCSC 最低）
          "market_source": "立创商城",    // 商城价来源（含商城名才有链接）
          "market_url": "https://...",    // 商城确认链接（仅确认商城才有）
          "price_ecommerce": 12,          // 电商价（买手全网最低含券）
          "found": true
        }
      ]
    }
  ]
}

输出 JSON 自动计算：
  - price_estimated = min(price_market, price_ecommerce) * 0.85（有搜索价）
  - price_estimated = price_estimated_experience（无搜索价时，经验值）
  - source / source_url = 仅当 market_source 含"立创/华秋/云汉/LCSC"才保留
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


def calc_estimated(pm, pe, exp=None):
    """计算预估价"""
    candidates = [v for v in (pm, pe) if v is not None]
    if candidates:
        return round(min(candidates) * 0.85, 2)
    return round(exp, 2) if exp is not None else None


def process_item(in_item: dict) -> dict:
    """处理单个 item（shared 或 variant parent），返回输出格式"""
    out = {k: v for k, v in in_item.items()
            if k not in ("market_source", "market_url", "ecommerce_source",
                         "price_estimated_experience", "variants")}

    if in_item.get("is_variant"):
        # 处理 variants
        new_variants = []
        for v in in_item.get("variants", []):
            nv = {k: val for k, val in v.items()
                   if k not in ("market_source", "market_url",
                                "ecommerce_source", "price_estimated_experience")}

            pm = v.get("price_market")
            pe = v.get("price_ecommerce")
            exp = v.get("price_estimated_experience")
            nv["price_estimated"] = calc_estimated(pm, pe, exp)

            # source / source_url：仅确认商城才有
            ms = v.get("market_source", "")
            mu = v.get("market_url", "")
            if is_confirmed_shop(ms) and mu:
                nv["source"] = ms
                nv["source_url"] = mu
            else:
                nv["source"] = ""
                nv["source_url"] = ""

            nv.setdefault("found", pm is not None or pe is not None)
            new_variants.append(nv)

        out["variants"] = new_variants
    else:
        # shared item
        pm = in_item.get("price_market")
        pe = in_item.get("price_ecommerce")
        exp = in_item.get("price_estimated_experience")
        out["price_estimated"] = calc_estimated(pm, pe, exp)

        ms = in_item.get("market_source", "")
        mu = in_item.get("market_url", "")
        if is_confirmed_shop(ms) and mu:
            out["source"] = ms
            out["source_url"] = mu
        else:
            out["source"] = ""
            out["source_url"] = ""

        out.setdefault("found", pm is not None or pe is not None)

    return out


def calc_cost_ratios(items: list) -> list:
    """计算 cost_ratio（需要全部 price_estimated 都就绪）"""
    total = sum(
        (v.get("price_estimated") or 0)
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
                ratio = (nv.get("price_estimated") or 0) / total * 100
                nv["cost_ratio"] = round(ratio, 1)
                new_variants.append(nv)
            out["variants"] = new_variants
        else:
            ratio = (item.get("price_estimated") or 0) / total * 100
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
