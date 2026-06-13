"""Pancake CUI Plugin — CLI 框架 + TUI 交互界面

提供命令行参数解析、子命令分组、Rich 组件输出、交互式用户输入。

核心组件:
  CLI 命令框架:
  - @Command:       注册子命令
  - @Group:         命令分组
  - @Option:        命令选项
  - @Argument:      命令参数
  - @Before/@After: 前置/后置钩子

  TUI 组件:
  - Table / Panel / Tree / Markdown / Progress

  快捷输出:
  - print_table / print_panel / print_json / print_tree / print_dict / print_objects

  交互组件:
  - show_menu / show_form / show_confirm / show_select / show_checkbox / show_password / show_progress

配置项（YAML）:
  pancake.cui.app_name:              应用名称
  pancake.cui.version:               应用版本
  pancake.cui.theme.primary:         主题色
"""

import logging
import sys

from pancake.ovenware import InitAction, check_dependencies

logger = logging.getLogger(__name__)


class Main(InitAction):
    """CUI 插件入口

    init_order=55, 在 web(50) 和 web-template(51) 之后加载。
    提供 CLI 命令框架 + Rich TUI 组件 + 交互式输入。
    """

    init_order = 55
    build_order = 55

    def __init__(self):
        from pancake.registry import export
        from pancake import settings

        # ── 读取配置 ──────────────────────────────
        app_name = settings.get("pancake.cui.app_name", "Pancake App")
        version = settings.get("pancake.cui.version", "0.1.0")
        self.app_name = app_name
        self.version = version

        # ── 初始化 Console ────────────────────────
        theme = {
            "info": settings.get("pancake.cui.theme.info", "cyan"),
            "success": settings.get("pancake.cui.theme.success", "green"),
            "warning": settings.get("pancake.cui.theme.warning", "yellow"),
            "error": settings.get("pancake.cui.theme.error", "red bold"),
            "primary": settings.get("pancake.cui.theme.primary", "cyan"),
        }
        from pancake_cui.console import init_console
        init_console(theme=theme)

        # ── 导出 CLI 装饰器 ─────────────────────
        from pancake_cui.cli import Command, Group, Option, Argument, Before, After
        export(Command)
        export(Group)
        export(Option)
        export(Argument)
        export(Before)
        export(After)

        # ── 导出 Rich 组件 ──────────────────────
        from rich.table import Table
        from rich.panel import Panel
        from rich.tree import Tree
        from rich.markdown import Markdown
        from rich.progress import Progress
        export(Table)
        export(Panel)
        export(Tree)
        export(Markdown)
        export(Progress)

        # ── 导出 display 工具 ───────────────────
        from pancake_cui.display import (
            make_table, make_objects_table, make_panel, make_tree,
            make_progress, make_spinner, make_markdown, make_live,
        )
        export(make_table)
        export(make_objects_table)
        export(make_panel)
        export(make_tree)
        export(make_progress)
        export(make_spinner)
        export(make_markdown)
        export(make_live)

        # ── 导出输出函数 ────────────────────────
        from pancake_cui.output import (
            print_table, print_panel, print_json, print_tree,
            print_dict, print_objects, print_markdown,
            print_info, print_success, print_warning, print_error,
        )
        export(print_table)
        export(print_panel)
        export(print_json)
        export(print_tree)
        export(print_dict)
        export(print_objects)
        export(print_markdown)
        export(print_info)
        export(print_success)
        export(print_warning)
        export(print_error)

        # ── 导出交互组件 ────────────────────────
        from pancake_cui.interactive import (
            show_menu, show_form, show_confirm, show_select,
            show_checkbox, show_password, show_progress,
        )
        export(show_menu)
        export(show_form)
        export(show_confirm)
        export(show_select)
        export(show_checkbox)
        export(show_password)
        export(show_progress)

        # ── 导出 Console ────────────────────────
        from pancake_cui.console import get_console, set_theme, ConsoleManager
        export(get_console)
        export(set_theme)
        export(ConsoleManager)

        logger.info("CUI 插件已加载")

    def check(self) -> bool:
        return check_dependencies(["click", "rich"], "cui")

    def build(self):
        pass

    async def startup(self):
        pass

    async def shutdown(self):
        pass

    def loop_method(self):
        """有 CLI 参数时启动 CLI 框架"""
        if len(sys.argv) <= 1:
            return

        from pancake_cui.cli import build_cli
        import click

        cli = build_cli(self.app_name, self.version)

        # 注册内置命令
        self._register_builtins(cli)

        logger.info(f"启动 CUI: {self.app_name}")
        try:
            cli(standalone_mode=False)
        except (click.exceptions.Exit, SystemExit, click.exceptions.NoArgsIsHelpError):
            pass
        except Exception as e:
            logger.error(f"CUI 执行错误: {e}")

    def _register_builtins(self, cli):
        """注册内置命令"""
        import click

        @cli.command("version")
        def version_cmd():
            """显示应用版本"""
            click.echo(f"{self.app_name} v{self.version}")

        @cli.command("info")
        def info_cmd():
            """显示系统信息"""
            from pancake_cui.output import print_panel, print_dict
            import platform
            info = {
                "应用": self.app_name,
                "版本": self.version,
                "Python": platform.python_version(),
                "系统": platform.system(),
                "架构": platform.machine(),
            }
            print_dict(info, title="系统信息")


__all__ = [
    # CLI 装饰器
    "Command", "Group", "Option", "Argument", "Before", "After",
    # Rich 组件
    "Table", "Panel", "Tree", "Markdown", "Progress",
    # display 工具
    "make_table", "make_objects_table", "make_panel", "make_tree",
    "make_progress", "make_spinner", "make_markdown", "make_live",
    # 输出函数
    "print_table", "print_panel", "print_json", "print_tree",
    "print_dict", "print_objects", "print_markdown",
    "print_info", "print_success", "print_warning", "print_error",
    # 交互组件
    "show_menu", "show_form", "show_confirm", "show_select",
    "show_checkbox", "show_password", "show_progress",
    # Console
    "get_console", "set_theme", "ConsoleManager",
]
