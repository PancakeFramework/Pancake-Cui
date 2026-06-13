"""Rich 组件封装 — Table / Panel / Tree / Progress / Markdown

提供 Pancake 风格的 Rich 组件，方便在插件中使用。

使用方法:
    from pancake_cui.display import make_table, make_panel, make_tree

    table = make_table("用户列表", [("ID", "cyan"), ("Name", "green")])
    table.add_row("1", "Alice")
    console.print(table)
"""

import logging
from dataclasses import fields, is_dataclass
from typing import Any

from rich.table import Table as RichTable
from rich.panel import Panel as RichPanel
from rich.tree import Tree as RichTree
from rich.markdown import Markdown as RichMarkdown
from rich.progress import Progress as RichProgress
from rich.progress import SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.live import Live as RichLive
from rich.text import Text

logger = logging.getLogger(__name__)


# ============================================================
#  Table
# ============================================================

def make_table(
    title: str = None,
    columns: list[tuple[str, str]] = None,
    show_lines: bool = False,
    show_edge: bool = True,
    expand: bool = False,
    border_style: str = "dim",
) -> RichTable:
    """创建 Rich Table

    Args:
        title:        表格标题
        columns:      列定义 [(name, style), ...]，style 可为 None
        show_lines:   是否显示行线
        show_edge:    是否显示边框
        expand:       是否扩展到终端宽度
        border_style: 边框样式

    用法:
        table = make_table("用户列表", [("ID", "cyan"), ("Name", "green")])
        table.add_row("1", "Alice")
        console.print(table)
    """
    table = RichTable(
        title=title,
        show_lines=show_lines,
        show_edge=show_edge,
        expand=expand,
        border_style=border_style,
    )
    if columns:
        for col_name, col_style in columns:
            table.add_column(col_name, style=col_style)
    return table


def make_objects_table(
    objects: list,
    fields_list: list[str] = None,
    title: str = None,
    show_lines: bool = False,
) -> RichTable:
    """将 dataclass/Struct 对象列表转为 Rich Table

    Args:
        objects:     dataclass 实例列表
        fields_list: 要显示的字段名列表（None 则显示全部）
        title:       表格标题
        show_lines:  是否显示行线

    用法:
        users = [User(id=1, name="Alice"), User(id=2, name="Bob")]
        table = make_objects_table(users, ["id", "name"], title="用户列表")
        console.print(table)
    """
    if not objects:
        return make_table(title=title)

    obj = objects[0]
    if not is_dataclass(obj) or isinstance(obj, type):
        raise TypeError(f"期望 dataclass 实例列表，得到 {type(obj)}")

    # 确定字段
    all_fields = [f.name for f in fields(obj)]
    if fields_list:
        display_fields = [f for f in fields_list if f in all_fields]
    else:
        display_fields = all_fields

    # 创建表格
    table = make_table(title=title, show_lines=show_lines)
    for field_name in display_fields:
        table.add_column(field_name, style="cyan")

    # 填充数据
    for obj in objects:
        row = []
        for field_name in display_fields:
            val = getattr(obj, field_name, "")
            row.append(str(val) if val is not None else "")
        table.add_row(*row)

    return table


# ============================================================
#  Panel
# ============================================================

def make_panel(
    content: Any,
    title: str = None,
    subtitle: str = None,
    border_style: str = "blue",
    width: int = None,
    expand: bool = True,
    padding: tuple = (1, 2),
) -> RichPanel:
    """创建 Rich Panel

    Args:
        content:      面板内容（字符串或 Rich 对象）
        title:        标题
        subtitle:     副标题
        border_style: 边框颜色
        width:        宽度
        expand:       是否扩展
        padding:      内边距 (top_bottom, left_right)

    用法:
        panel = make_panel("Hello World", title="欢迎", border_style="green")
        console.print(panel)
    """
    if isinstance(content, dict):
        content = _dict_to_text(content)

    return RichPanel(
        content,
        title=title,
        subtitle=subtitle,
        border_style=border_style,
        width=width,
        expand=expand,
        padding=padding,
    )


def _dict_to_text(data: dict) -> Text:
    """将 dict 转为格式化 Text"""
    text = Text()
    for k, v in data.items():
        text.append(f"{k}: ", style="bold cyan")
        text.append(f"{v}\n")
    return text


# ============================================================
#  Tree
# ============================================================

def make_tree(
    label: str,
    data: dict = None,
    guide_style: str = "dim",
) -> RichTree:
    """创建 Rich Tree

    Args:
        label:       根节点标签
        data:        嵌套 dict 自动展开为树
        guide_style: 引导线样式

    用法:
        tree = make_tree("项目结构")
        src = tree.add("src/")
        src.add("main.py")
        console.print(tree)

        # 或从 dict 生成
        tree = make_tree("配置", {"db": {"host": "localhost", "port": 5432}})
        console.print(tree)
    """
    tree = RichTree(label, guide_style=guide_style)
    if data:
        _add_dict_to_tree(tree, data)
    return tree


def _add_dict_to_tree(tree: RichTree, data: dict):
    """递归将 dict 添加到 tree"""
    for k, v in data.items():
        if isinstance(v, dict):
            branch = tree.add(f"[bold]{k}[/bold]")
            _add_dict_to_tree(branch, v)
        elif isinstance(v, list):
            branch = tree.add(f"[bold]{k}[/bold]")
            for item in v:
                if isinstance(item, dict):
                    _add_dict_to_tree(branch, item)
                else:
                    branch.add(str(item))
        else:
            tree.add(f"[cyan]{k}[/cyan] = {v}")


# ============================================================
#  Progress
# ============================================================

def make_progress(
    show_spinner: bool = True,
    show_bar: bool = True,
    show_time: bool = True,
    show_text: bool = True,
) -> RichProgress:
    """创建 Rich Progress 进度条

    Args:
        show_spinner: 显示旋转动画
        show_bar:     显示进度条
        show_time:    显示已用时间
        show_text:    显示任务文本

    用法:
        with make_progress() as progress:
            task = progress.add_task("下载中...", total=100)
            for i in range(100):
                do_work()
                progress.update(task, advance=1)
    """
    columns = []
    if show_spinner:
        columns.append(SpinnerColumn())
    if show_text:
        columns.append(TextColumn("[progress.description]{task.description}"))
    if show_bar:
        columns.append(BarColumn())
    if show_time:
        columns.append(TimeElapsedColumn())

    return RichProgress(*columns)


def make_spinner(text: str = "处理中...") -> RichProgress:
    """创建仅旋转动画的进度指示器

    用法:
        with make_spinner("加载中..."):
            do_heavy_work()
    """
    return RichProgress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    )


# ============================================================
#  Markdown
# ============================================================

def make_markdown(content: str) -> RichMarkdown:
    """创建 Rich Markdown 渲染对象

    Args:
        content: Markdown 文本

    用法:
        console.print(make_markdown("# Hello\\n- item1\\n- item2"))
    """
    return RichMarkdown(content)


# ============================================================
#  Live
# ============================================================

def make_live(
    renderable=None,
    refresh_per_second: float = 4,
    screen: bool = False,
) -> RichLive:
    """创建 Rich Live 实时刷新上下文

    Args:
        renderable:         初始渲染对象
        refresh_per_second: 刷新频率
        screen:             是否全屏

    用法:
        with make_live(console=console) as live:
            for i in range(100):
                live.update(f"进度: {i}%")
                time.sleep(0.1)
    """
    from pancake_cui.console import get_console
    return RichLive(
        renderable,
        console=get_console(),
        refresh_per_second=refresh_per_second,
        screen=screen,
    )
