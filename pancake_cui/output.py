"""快捷输出函数 — 一行代码完成复杂输出

提供 print_table / print_panel / print_json / print_tree 等快捷函数，
内部使用 Rich 渲染，无需手动创建组件。

使用方法:
    print_table(["ID", "Name"], [[1, "Alice"], [2, "Bob"]], title="Users")
    print_panel("Hello", title="Greeting")
    print_json({"key": "value"})
    print_tree({"db": {"host": "localhost", "port": 5432}})
    print_dict({"name": "Alice", "age": 18})
    print_objects([User(1, "Alice"), User(2, "Bob")], ["id", "name"])
"""

import json
import logging
from dataclasses import is_dataclass
from typing import Any

from rich.syntax import Syntax
from rich.text import Text

from pancake_cui.console import get_console
from pancake_cui.display import (
    make_table, make_objects_table, make_panel, make_tree, make_markdown,
)

logger = logging.getLogger(__name__)


def print_table(
    headers: list[str],
    rows: list[list[Any]] = None,
    title: str = None,
    show_lines: bool = False,
    styles: list[str] = None,
):
    """打印表格

    Args:
        headers:     表头列表
        rows:        数据行列表
        title:       表格标题
        show_lines:  是否显示行线
        styles:      每列的样式列表

    用法:
        print_table(
            ["ID", "姓名", "年龄"],
            [[1, "Alice", 18], [2, "Bob", 20]],
            title="用户列表"
        )
    """
    console = get_console()

    # 构建列定义
    columns = []
    for i, header in enumerate(headers):
        style = styles[i] if styles and i < len(styles) else "cyan"
        columns.append((header, style))

    table = make_table(title=title, columns=columns, show_lines=show_lines)

    if rows:
        for row in rows:
            table.add_row(*[str(v) if v is not None else "" for v in row])

    console.print(table)


def print_panel(
    content: Any,
    title: str = None,
    subtitle: str = None,
    style: str = None,
    border_style: str = "blue",
    width: int = None,
):
    """打印面板

    Args:
        content:      内容（字符串、dict 或 Rich 对象）
        title:        标题
        subtitle:     副标题
        style:        内容样式
        border_style: 边框颜色
        width:        宽度

    用法:
        print_panel("服务已启动", title="启动成功", border_style="green")
        print_panel({"host": "localhost", "port": 8080}, title="配置")
    """
    console = get_console()

    if isinstance(content, str):
        if style:
            content = Text(content, style=style)
    elif isinstance(content, dict):
        content = _format_dict(content)

    panel = make_panel(
        content, title=title, subtitle=subtitle,
        border_style=border_style, width=width,
    )
    console.print(panel)


def print_json(data: Any, indent: int = 2, title: str = None):
    """打印 JSON（语法高亮）

    Args:
        data:   要打印的数据
        indent: 缩进空格数
        title:  可选标题面板

    用法:
        print_json({"name": "Alice", "scores": [90, 85]})
    """
    console = get_console()
    json_str = json.dumps(data, indent=indent, ensure_ascii=False, default=str)

    if title:
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        console.print(make_panel(syntax, title=title, border_style="yellow"))
    else:
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        console.print(syntax)


def print_tree(
    data: dict,
    root_label: str = "root",
    guide_style: str = "dim",
):
    """打印树形结构

    Args:
        data:        嵌套 dict
        root_label:  根节点标签
        guide_style: 引导线样式

    用法:
        print_tree({"db": {"host": "localhost", "port": 5432}}, root_label="配置")
    """
    console = get_console()
    tree = make_tree(root_label, data=data, guide_style=guide_style)
    console.print(tree)


def print_dict(data: dict, title: str = None, key_style: str = "bold cyan"):
    """打印 dict（表格形式）

    Args:
        data:       dict 数据
        title:      标题
        key_style:  key 列样式

    用法:
        print_dict({"name": "Alice", "age": 18, "city": "Beijing"}, title="用户信息")
    """
    headers = ["Key", "Value"]
    rows = [[k, v] for k, v in data.items()]
    print_table(headers, rows, title=title, styles=[key_style, ""])


def print_objects(
    objects: list,
    fields: list[str] = None,
    title: str = None,
    show_lines: bool = False,
):
    """打印 dataclass/Struct 对象列表（表格形式）

    Args:
        objects:     dataclass 实例列表
        fields:      要显示的字段名列表（None 则显示全部）
        title:       表格标题
        show_lines:  是否显示行线

    用法:
        users = [User(id=1, name="Alice"), User(id=2, name="Bob")]
        print_objects(users, fields=["id", "name"], title="用户列表")
    """
    console = get_console()
    table = make_objects_table(objects, fields_list=fields, title=title, show_lines=show_lines)
    console.print(table)


def print_markdown(content: str):
    """打印 Markdown 文本

    Args:
        content: Markdown 文本

    用法:
        print_markdown("# Hello\\n- item1\\n- item2")
    """
    console = get_console()
    console.print(make_markdown(content))


def print_info(text: str):
    """信息输出（蓝色）"""
    console = get_console()
    console.print(f"[info][INFO][/info] {text}")


def print_success(text: str):
    """成功输出（绿色）"""
    console = get_console()
    console.print(f"[success][OK][/success] {text}")


def print_warning(text: str):
    """警告输出（黄色）"""
    console = get_console()
    console.print(f"[warning][WARN][/warning] {text}")


def print_error(text: str):
    """错误输出（红色）"""
    console = get_console()
    console.print(f"[error][ERROR][/error] {text}")


# ============================================================
#  内部工具
# ============================================================

def _format_dict(data: dict) -> Text:
    """将 dict 格式化为 Rich Text"""
    text = Text()
    for k, v in data.items():
        text.append(f"  {k}: ", style="bold cyan")
        if isinstance(v, dict):
            text.append("\n")
            for kk, vv in v.items():
                text.append(f"    {kk}: ", style="cyan")
                text.append(f"{vv}\n")
        else:
            text.append(f"{v}\n")
    return text
