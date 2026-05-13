#!/usr/bin/env python3
"""
BOM 报告生成器 —— 将 JSON 数据注入模板，生成独立可分享的 HTML 报告。

用法:
  python3 generate_report.py <data.json> [output.html]
  python3 generate_report.py data/智能台灯_20260512.json

默认输出到同目录下: <项目名>_<日期>_report.html
"""

import json
import sys
import os
import re
from pathlib import Path

# 模板路径（与脚本同目录或上级目录）
SCRIPT_DIR = Path(__file__).parent.resolve()
TEMPLATE_PATH = SCRIPT_DIR / "report-template.html"

# 标记: 数据注入点
INJECTION_MARKER = "// __BOM_DATA_INJECTION_POINT__"


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
