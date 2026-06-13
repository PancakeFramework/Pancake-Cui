"""交互式组件 — 菜单 / 表单 / 确认 / 选择 / 进度条

提供终端交互式用户输入组件，基于 Rich 渲染 + 内置输入循环。

使用方法:
    choice = await show_menu("请选择操作", ["新建", "编辑", "删除"])
    data = await show_form({"name": {"label": "用户名"}, "age": {"label": "年龄"}})
    ok = await show_confirm("确认删除？")
    selected = await show_select("选择用户", ["Alice", "Bob", "Charlie"])
    selected = await show_checkbox("选择标签", ["Python", "Redis", "Web"])
    pwd = await show_password("请输入密码")
"""

import asyncio
import getpass
import logging
from typing import Any

from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.text import Text

from pancake_cui.console import get_console
from pancake_cui.display import make_table, make_panel, make_progress

logger = logging.getLogger(__name__)


# ============================================================
#  菜单
# ============================================================

async def show_menu(
    title: str,
    options: list[str],
    prompt_text: str = "请选择",
    show_numbers: bool = True,
) -> int:
    """交互式菜单

    Args:
        title:        菜单标题
        options:      选项列表
        prompt_text:  提示文字
        show_numbers: 是否显示编号

    Returns:
        选中的索引（从 0 开始）

    用法:
        choice = await show_menu("操作", ["新建", "编辑", "删除", "退出"])
        if choice == 0:
            create()
    """
    console = get_console()

    # 打印菜单
    console.print()
    console.print(make_panel(
        _build_menu_text(options, show_numbers),
        title=title,
        border_style="cyan",
        padding=(1, 2),
    ))

    # 输入循环
    while True:
        try:
            choice = Prompt.ask(
                prompt_text,
                console=console,
                choices=[str(i) for i in range(len(options))],
                show_choices=False,
            )
            idx = int(choice)
            if 0 <= idx < len(options):
                return idx
        except (ValueError, KeyboardInterrupt):
            pass
        console.print(f"[warning]请输入 0-{len(options)-1} 的数字[/warning]")


def _build_menu_text(options: list[str], show_numbers: bool) -> Text:
    """构建菜单文本"""
    text = Text()
    for i, opt in enumerate(options):
        if show_numbers:
            text.append(f"  [{i}] ", style="bold cyan")
        else:
            text.append("  * ", style="bold cyan")
        text.append(f"{opt}\n")
    return text


# ============================================================
#  表单
# ============================================================

async def show_form(
    fields: dict[str, dict],
    title: str = "表单",
    confirm_text: str = "确认提交?",
) -> dict[str, Any]:
    """交互式表单

    Args:
        fields:        字段定义 {name: {label, type, default, required, ...}}
        title:         表单标题
        confirm_text:  确认提示

    Returns:
        {name: value} 字典

    字段定义:
        {
            "label": "显示标签",
            "type": "str" | "int" | "float" | "password" | "confirm",  # 默认 str
            "default": 默认值,
            "required": True/False,
            "choices": ["选项1", "选项2"],  # 可选下拉
        }

    用法:
        data = await show_form({
            "name": {"label": "用户名", "required": True},
            "age": {"label": "年龄", "type": "int", "default": 18},
            "role": {"label": "角色", "choices": ["admin", "user"]},
            "active": {"label": "是否激活", "type": "confirm", "default": True},
        })
    """
    console = get_console()

    console.print()
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print("─" * 40)

    result = {}
    for name, field_def in fields.items():
        label = field_def.get("label", name)
        field_type = field_def.get("type", "str")
        default = field_def.get("default")
        required = field_def.get("required", False)
        choices = field_def.get("choices")

        while True:
            try:
                value = _prompt_field(label, field_type, default, choices, required)
                result[name] = value
                break
            except KeyboardInterrupt:
                console.print("\n[warning]已取消[/warning]")
                return {}
            except ValueError as e:
                console.print(f"[error]{e}[/error]")

    # 确认
    if confirm_text:
        if not Confirm.ask(confirm_text, console=console, default=True):
            console.print("[warning]已取消[/warning]")
            return {}

    return result


def _prompt_field(
    label: str,
    field_type: str,
    default: Any,
    choices: list,
    required: bool,
) -> Any:
    """单个字段输入"""
    console = get_console()

    # 构建提示文本
    hint_parts = []
    if default is not None:
        hint_parts.append(f"default={default}")
    if choices:
        hint_parts.append(f"choices={choices}")
    if required:
        hint_parts.append("required")

    hint = f" ({', '.join(hint_parts)})" if hint_parts else ""
    prompt_text = f"  {label}{hint}"

    if choices:
        # 选择列表
        console.print(f"  [cyan]{label}[/cyan]:")
        for i, opt in enumerate(choices):
            console.print(f"    [{i}] {opt}")
        while True:
            choice = Prompt.ask("  选择编号", console=console, default=str(default) if default is not None else None)
            try:
                idx = int(choice)
                if 0 <= idx < len(choices):
                    return choices[idx]
            except ValueError:
                pass
            console.print(f"[warning]请输入 0-{len(choices)-1}[/warning]")

    if field_type == "password":
        value = getpass.getpass(f"  {label}: ")
        if required and not value:
            raise ValueError(f"{label} 不能为空")
        return value

    if field_type == "confirm":
        return Confirm.ask(prompt_text, console=console, default=bool(default) if default is not None else False)

    if field_type == "int":
        value = IntPrompt.ask(prompt_text, console=console, default=default)
        return value

    if field_type == "float":
        value = FloatPrompt.ask(prompt_text, console=console, default=default)
        return value

    # 默认: 字符串
    value = Prompt.ask(prompt_text, console=console, default=str(default) if default is not None else None)
    if required and not value:
        raise ValueError(f"{label} 不能为空")
    return value


# ============================================================
#  确认
# ============================================================

async def show_confirm(text: str, default: bool = False) -> bool:
    """确认对话框

    Args:
        text:    提示文字
        default: 默认值

    Returns:
        True/False
    """
    console = get_console()
    return Confirm.ask(text, console=console, default=default)


# ============================================================
#  选择
# ============================================================

async def show_select(
    title: str,
    options: list[str],
    prompt_text: str = "请选择",
) -> str:
    """单选列表

    Args:
        title:        标题
        options:      选项列表
        prompt_text:  提示文字

    Returns:
        选中的值

    用法:
        name = await show_select("选择用户", ["Alice", "Bob", "Charlie"])
    """
    idx = await show_menu(title, options, prompt_text)
    return options[idx]


async def show_checkbox(
    title: str,
    options: list[str],
    prompt_text: str = "请选择（用逗号分隔多个）",
) -> list[str]:
    """多选列表

    Args:
        title:        标题
        options:      选项列表
        prompt_text:  提示文字

    Returns:
        选中的值列表

    用法:
        tags = await show_checkbox("选择标签", ["Python", "Redis", "Web", "Docker"])
    """
    console = get_console()

    console.print()
    console.print(make_panel(
        _build_menu_text(options, True),
        title=title,
        border_style="cyan",
        padding=(1, 2),
    ))

    while True:
        try:
            raw = Prompt.ask(prompt_text, console=console)
            indices = [int(x.strip()) for x in raw.split(",") if x.strip()]
            valid = [options[i] for i in indices if 0 <= i < len(options)]
            if valid:
                return valid
        except (ValueError, KeyboardInterrupt):
            pass
        console.print(f"[warning]请输入 0-{len(options)-1} 的数字，逗号分隔[/warning]")


# ============================================================
#  密码
# ============================================================

async def show_password(prompt_text: str = "请输入密码") -> str:
    """密码输入（不回显）

    Args:
        prompt_text: 提示文字

    Returns:
        输入的密码
    """
    return getpass.getpass(f"  {prompt_text}: ")


# ============================================================
#  进度条
# ============================================================

class ProgressWrapper:
    """进度条包装器，支持 async with"""

    def __init__(self, progress, task_id):
        self._progress = progress
        self._task_id = task_id

    def advance(self, amount: float = 1):
        self._progress.advance(self._task_id, amount)

    def update(self, description: str = None, completed: float = None, total: float = None):
        self._progress.update(self._task_id, description=description, completed=completed, total=total)


class AsyncProgressContext:
    """异步进度条上下文管理器"""

    def __init__(self, description: str, total: int, **kwargs):
        self._description = description
        self._total = total
        self._kwargs = kwargs
        self._progress = None
        self._task_id = None
        self._ctx = None

    async def __aenter__(self):
        self._progress = make_progress(**self._kwargs)
        self._ctx = self._progress.__enter__()
        self._task_id = self._ctx.add_task(self._description, total=self._total)
        return ProgressWrapper(self._ctx, self._task_id)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._ctx.__exit__(exc_type, exc_val, exc_tb)


def show_progress(description: str, total: int, **kwargs) -> AsyncProgressContext:
    """异步进度条

    Args:
        description: 任务描述
        total:       总数
        **kwargs:    make_progress 参数

    Returns:
        AsyncProgressContext (async with 使用)

    用法:
        async with show_progress("下载中...", total=100) as p:
            for i in range(100):
                await asyncio.sleep(0.1)
                p.advance(1)
    """
    return AsyncProgressContext(description, total, **kwargs)
