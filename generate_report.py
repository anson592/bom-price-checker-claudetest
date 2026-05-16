#!/usr/bin/env python3
"""
BOM 报告生成器 —— 将 JSON 数据注入模板，生成独立可分享的 HTML 报告。

用法:
  python3 generate_report.py <data.json> [output.html]
  python3 generate_report.py data/智能台灯_20260512.json

默认输出到同目录下: <项目名>_<日期>_report.html

normalize_data 阶段做四件事：
  1. 字段兼容层：旧字段名 (price_market/price_ecommerce/...) 自动迁移到新字段名
  2. 自动计算 price_unit（小计 = price_mall 优先；mall 空则取 price_ai）
  3. 自动计算 cost_ratio（每颗占单套总成本百分比，按 selected_version）
  4. 轻量校验，违规打 stderr 警告但不阻塞
"""

import json
import sys
import os
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
TEMPLATE_PATH = SCRIPT_DIR / "report-template.html"
INJECTION_MARKER = "// __BOM_DATA_INJECTION_POINT__"

FIELD_ALIASES = {
    "price_market": "price_mall",
    "market_source": "mall_source",
    "market_url": "mall_url",
    "price_ecommerce": "price_ai",
    "ecommerce_source": "ai_source",
    "price_estimated": "price_unit",
    "price_estimated_experience": "price_unit",
    "source": "mall_source",
    "source_url": "mall_url",
}


def _apply_aliases(node: dict) -> None:
    for old, new in FIELD_ALIASES.items():
        if old in node:
            if new not in node or node.get(new) in (None, ""):
                node[new] = node.pop(old)
            else:
                del node[old]


def _compute_price_unit(node: dict) -> None:
    """计算 price_unit（小计）：mall 优先，mall 空则取 ai；PCB 特殊处理"""
    mall = node.get("price_mall")
    ai = node.get("price_ai")
    existing = node.get("price_unit")
    category = node.get("category", "")

    # PCB 特殊处理：如果 mall 和 ai 都为 null，用公式计算
    if category == "PCB" and mall is None and ai is None:
        computed = _compute_pcb_price(node)
        if computed is not None:
            node["price_unit"] = computed
            node["ai_source"] = f"脚本公式（{node.get('description', 'PCB')}）"
            return

    if mall is not None:
        computed = mall
    elif ai is not None:
        computed = ai
    else:
        computed = existing

    if (
        existing is not None
        and computed is not None
        and isinstance(existing, (int, float))
        and isinstance(computed, (int, float))
        and abs(existing - computed) > 0.001
    ):
        print(
            f"⚠️  price_unit 覆盖：原 {existing} → 重算 {computed} "
            f"(part_number={node.get('part_number','?')})",
            file=sys.stderr,
        )
    node["price_unit"] = computed


def _compute_pcb_price(node: dict) -> float:
    """PCB 价格经验公式（v9.3 新增）"""
    desc = node.get("description", "")

    # 从 description 提取层数、尺寸
    layers_match = re.search(r'(\d+)层', desc)
    size_match = re.search(r'(\d+)[×x](\d+)\s*mm', desc)

    layers = int(layers_match.group(1)) if layers_match else 4
    if size_match:
        w, h = int(size_match.group(1)), int(size_match.group(2))
        size_mm2 = w * h
    else:
        size_mm2 = 10000  # 默认 100×100mm

    # 从全局数据获取产量（这里简化为默认 2000）
    qty = 2000

    # 公式
    base_price_map = {2: 5, 4: 12, 6: 22, 8: 35}
    base = base_price_map.get(layers, 12)
    size_factor = max(1.0, size_mm2 / 10000)

    qty_discount_map = {100: 1.5, 500: 1.2, 1000: 1.05, 2000: 1.0, 5000: 0.9, 10000: 0.85}
    qty_key = min(qty_discount_map.keys(), key=lambda k: abs(k - qty))
    qty_discount = qty_discount_map[qty_key]

    return round(base * size_factor * qty_discount, 2)


def _validate_node(node: dict, ctx: str) -> None:
    if (
        node.get("found") is True
        and node.get("price_mall") is None
        and node.get("price_ai") is None
    ):
        print(
            f"⚠️  {ctx}: found=true 但 price_mall 和 price_ai 都为 null",
            file=sys.stderr,
        )


def normalize_data(data: dict) -> dict:
    versions = data.get("versions") or []
    selected = data.get("selected_version") or (versions[0] if versions else None)

    for item in data.get("items") or []:
        _apply_aliases(item)
        if item.get("is_variant"):
            for v in item.get("variants") or []:
                _apply_aliases(v)
                _compute_price_unit(v)
                _validate_node(
                    v, f"{item.get('category','?')}/{v.get('version','?')}"
                )
                if versions and v.get("version") not in versions:
                    print(
                        f"⚠️  version '{v.get('version')}' 不在 versions {versions} "
                        f"(item id={item.get('id')})",
                        file=sys.stderr,
                    )
            if not (item.get("variants") or []):
                print(
                    f"⚠️  item id={item.get('id')} is_variant=true 但 variants 为空",
                    file=sys.stderr,
                )
        else:
            _compute_price_unit(item)
            _validate_node(
                item, f"{item.get('category','?')}/{item.get('part_number','?')}"
            )

    total = 0.0
    for item in data.get("items") or []:
        if item.get("is_variant"):
            v = next(
                (
                    x
                    for x in (item.get("variants") or [])
                    if x.get("version") == selected
                ),
                None,
            )
            if v and isinstance(v.get("price_unit"), (int, float)):
                total += v["price_unit"]
        else:
            if isinstance(item.get("price_unit"), (int, float)):
                total += item["price_unit"]

    if total > 0:
        for item in data.get("items") or []:
            if item.get("is_variant"):
                for v in item.get("variants") or []:
                    if isinstance(v.get("price_unit"), (int, float)):
                        v["cost_ratio"] = round(v["price_unit"] / total * 100, 1)
            else:
                if isinstance(item.get("price_unit"), (int, float)):
                    item["cost_ratio"] = round(item["price_unit"] / total * 100, 1)

    return data


def load_template() -> str:
    """读取模板 HTML"""
    if not TEMPLATE_PATH.exists():
        print(f"错误: 模板文件不存在: {TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def load_data(json_path: str) -> dict:
    """读取 JSON 数据"""
    path = Path(json_path)
    if not path.exists():
        # 尝试相对于脚本目录
        path = SCRIPT_DIR / json_path
    if not path.exists():
        print(f"错误: 数据文件不存在: {json_path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def inject_data(template: str, data: dict) -> str:
    """将 JSON 数据注入模板的标记位置"""
    marker_pos = template.find(INJECTION_MARKER)
    if marker_pos == -1:
        print("错误: 模板中未找到数据注入标记", file=sys.stderr)
        sys.exit(1)

    # 找到标记所在 <script> 块的结束位置（替换整个 IIFE 内容）
    # 从标记开始往后找到对应的 })(); 和 </script>
    # 更精确的做法: 替换从标记到下一个 </script> 之间的内容

    # 简单策略: 把整个 data loader script 块替换为内嵌数据
    # 找到包含标记的 <script> 开始位置
    script_start = template.rfind("<script>", 0, marker_pos)
    if script_start == -1:
        script_start = template.rfind("<script ", 0, marker_pos)

    # 找到对应的 </script>
    script_end = template.find("</script>", marker_pos)
    if script_end == -1:
        print("错误: 未找到脚本结束标记", file=sys.stderr)
        sys.exit(1)
    script_end += len("</script>")

    # 生成内嵌数据的 script 块（仅设置数据，不触发事件）
    # 事件触发必须在 main script 的 addEventListener 注册之后
    data_json = json.dumps(data, ensure_ascii=False, indent=2)
    new_script = f"""<!-- ── Data (injected by generate_report.py) ─────────────── -->
<script>
// __BOM_DATA_INJECTION_POINT__
// 此数据由 generate_report.py 自动注入，源文件: {Path(json_path).name if 'json_path' in dir() else 'unknown'}
window.BOM_DATA = {data_json};
</script>"""

    result = template[:script_start] + new_script + template[script_end:]

    # 在 </body> 前注入事件触发脚本（确保在 main script 的 addEventListener 之后）
    trigger_script = """<script>
// 在所有脚本加载完毕后触发渲染
window.dispatchEvent(new Event('bom-data-ready'));
</script>"""
    result = result.replace("</body>", trigger_script + "\n</body>")

    return result


def generate_output_name(data: dict, json_path: str) -> str:
    """根据项目名和日期生成输出文件名"""
    project = data.get("project", "BOM")
    date = data.get("date", "")
    # 清理文件名中的特殊字符
    safe_project = re.sub(r'[\\/:*?"<>|]', '_', project)
    if date:
        return f"{safe_project}_{date}_report.html"
    # 从 JSON 文件名提取日期
    base = Path(json_path).stem
    return f"{base}_report.html"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("可用数据文件:")
        data_dir = SCRIPT_DIR / "data"
        if data_dir.exists():
            for f in sorted(data_dir.glob("*.json")):
                print(f"  data/{f.name}")
        sys.exit(0)

    json_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # 加载
    template = load_template()
    data = load_data(json_path)
    data = normalize_data(data)

    # 注入
    result = inject_data(template, data)

    # 输出
    if output_path is None:
        json_dir = Path(json_path).parent
        output_path = str(json_dir / generate_output_name(data, json_path))

    Path(output_path).write_text(result, encoding="utf-8")
    print(f"✅ 报告已生成: {output_path}")
    print(f"   项目: {data.get('project', '?')}")
    print(f"   器件: {len(data.get('items', []))} 项")
    print(f"   版本: {', '.join(data.get('versions', []))}")


if __name__ == "__main__":
    main()
