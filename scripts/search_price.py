#!/usr/bin/env python3
"""
买手全网比价脚本 - bom-price-checker 内置
直接调用买手 API 搜索淘宝/京东/拼多多/1688 等平台价格，无需依赖外部 skill。

用法:
  python3 search_price.py "STM32F103C8T6"
  python3 search_price.py "STM32F103C8T6" --source 0       # 全部平台（默认）
  python3 search_price.py "STM32F103C8T6" --source 1       # 仅淘宝
  python3 search_price.py "STM32F103C8T6" --source 10      # 仅1688
  python3 search_price.py "STM32F103C8T6" --json            # JSON 输出
  python3 search_price.py "STM32F103C8T6 ESP32-S3" --batch  # 批量搜索（空格分隔）
"""

import argparse
import json
import sys
import requests

MAISHOU_API = "https://appapi.maishou88.com/api/v1/homepage/searchList"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}

# 平台映射
SOURCE_MAP = {
    0: "全部",
    1: "淘宝",
    2: "京东",
    3: "拼多多",
    7: "抖音",
    10: "1688",
}


def search(keyword: str, source_type: int = 0) -> list:
    """
    搜索指定关键词在各平台的商品价格

    :param keyword: 搜索关键词（型号、名称等）
    :param source_type: 平台类型 0=全部 1=淘宝 2=京东 3=拼多多 7=抖音 10=1688
    :return: 商品列表，每个元素包含 price/title/source/actualPrice 等字段
    """
    try:
        resp = requests.post(
            MAISHOU_API,
            data={
                "keyword": keyword,
                "openid": "564bdce0fa408fc9e1d5d42fd022ef0b",
                "sourceType": source_type,
                "page": 1,
                "order": "asc",      # 按价格升序
                "isCoupon": 0
            },
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        # API 返回 {"status": "success", "data": [...]}
        # data 直接就是商品列表
        raw = data.get("data", [])
        if isinstance(raw, list):
            return raw
        # 兼容可能的嵌套结构
        return raw.get("list", []) if isinstance(raw, dict) else []
    except requests.exceptions.Timeout:
        print(f"[搜索超时] {keyword}", file=sys.stderr)
        return []
    except requests.exceptions.RequestException as e:
        print(f"[搜索失败] {keyword}: {e}", file=sys.stderr)
        return []
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[解析失败] {keyword}: {e}", file=sys.stderr)
        return []


def get_best_price(keyword: str, source_type: int = 0) -> dict:
    """
    搜索并返回最低价商品

    :return: {
        "keyword": 搜索词,
        "price": 最低价格,
        "actual_price": 实际价格（含优惠券）,
        "platform": 平台名称,
        "title": 商品标题,
        "shop": 店铺名称,
        "sales": 销量,
        "link": 商品链接（如有）
    }
    """
    hits = search(keyword, source_type)

    if not hits:
        return {
            "keyword": keyword,
            "price": None,
            "actual_price": None,
            "platform": None,
            "title": None,
            "shop": None,
            "sales": None,
            "link": None,
        }

    # 按 actualPrice（含优惠券价）排序，取最低
    valid = [h for h in hits if h.get("actualPrice")]
    # 过滤掉无效价格
    valid = [h for h in valid if isinstance(h["actualPrice"], (int, float)) or (isinstance(h["actualPrice"], str) and h["actualPrice"].replace(".", "", 1).isdigit())]
    if not valid:
        return {
            "keyword": keyword,
            "price": None,
            "actual_price": None,
            "platform": None,
            "title": None,
            "shop": None,
            "sales": None,
            "link": None,
        }

    best = min(valid, key=lambda x: float(x.get("actualPrice", 9999)))
    source_id = best.get("sourceType", 0)
    platform_name = best.get("platformName", SOURCE_MAP.get(source_id, f"平台{source_id}"))

    return {
        "keyword": keyword,
        "price": float(best.get("originalPrice", 0)),
        "actual_price": float(best.get("actualPrice", 0)),
        "platform": platform_name,
        "title": best.get("title", ""),
        "shop": best.get("shopName", ""),
        "sales": best.get("monthSales", ""),
        "link": best.get("superSubsidyLink", best.get("url", "")),
    }


def batch_search(bom_list: list, source_type: int = 0) -> dict:
    """
    批量搜索多个元器件的最低价

    :param bom_list: [{"model": "STM32F103C8T6", "name": "STM32F103C8T6"}, ...]
    :param source_type: 平台类型
    :return: {型号: 最低价信息}
    """
    results = {}
    for item in bom_list:
        model = item.get("model", "")
        name = item.get("name", model)
        if not model:
            continue

        # 搜索关键词 = 型号 + 名称（如果不同）
        kw = f"{model} {name}" if name and name != model else model
        best = get_best_price(kw, source_type)
        results[model] = best

    return results


def format_result(result: dict, json_output: bool = False) -> str:
    """格式化单条搜索结果"""
    if json_output:
        return json.dumps(result, ensure_ascii=False, indent=2)

    if result.get("price") is None:
        return f"[{result.get('keyword', '?')}] 未获取到价格"

    lines = []
    lines.append(f"[{result.get('keyword', '?')}]")
    lines.append(f"  最低价: ¥{result['actual_price']:.2f}" if result.get("actual_price") else f"  价格: ¥{result['price']:.2f}")
    lines.append(f"  平台: {result.get('platform', '?')}")
    if result.get("title"):
        lines.append(f"  商品: {result['title'][:80]}")
    if result.get("shop"):
        lines.append(f"  店铺: {result.get('shop')}")
    if result.get("sales"):
        lines.append(f"  销量: {result.get('sales')}")
    if result.get("link"):
        lines.append(f"  链接: {result['link']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="买手全网比价 - bom-price-checker 内置",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 search_price.py "STM32F103C8T6"
  python3 search_price.py "STM32F103C8T6" --source 0
  python3 search_price.py "STM32F103C8T6" --json
  python3 search_price.py "ESP32-S3 STM32F103C8T6" --batch
"""
    )

    parser.add_argument("keyword", help="搜索关键词（型号/名称），批量模式用空格分隔多个型号")
    parser.add_argument("--source", type=int, default=0,
                        choices=[0, 1, 2, 3, 7, 10],
                        help="平台类型: 0=全部 1=淘宝 2=京东 3=拼多多 7=抖音 10=1688（默认0）")
    parser.add_argument("--batch", action="store_true",
                        help="批量模式：keyword 中的每个空格分隔项作为独立型号搜索")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="JSON 格式输出")

    args = parser.parse_args()

    if args.batch:
        # 批量模式
        models = args.keyword.split()
        bom_list = [{"model": m, "name": m} for m in models]
        results = batch_search(bom_list, source_type=args.source)
        if args.json_output:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for model, result in results.items():
                print(format_result(result))
                print()
    else:
        # 单条模式
        best = get_best_price(args.keyword, source_type=args.source)
        print(format_result(best, json_output=args.json_output))


if __name__ == "__main__":
    main()
