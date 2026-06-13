"""Rich Console 管理器 — 全局单例 + 主题配置

提供统一的 Rich Console 实例，所有 TUI 组件共享。

使用方法:
    from pancake_cui.console import get_console
    console = get_console()
    console.print("Hello", style="bold green")
"""

import logging
from rich.console import Console as RichConsole
from rich.theme import Theme

logger = logging.getLogger(__name__)

# 默认主题
_DEFAULT_THEME = {
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red bold",
    "primary": "cyan",
    "secondary": "dim",
    "highlight": "bold magenta",
    "muted": "dim white",
}

# 全局 Console 实例
_console: RichConsole | None = None


class ConsoleManager:
    """Rich Console 管理器

    使用方法:
        manager = ConsoleManager()
        console = manager.get_console()
        console.print("Hello")

        # 自定义主题
        manager.set_theme({"info": "blue", "error": "red bold"})
    """

    def __init__(
        self,
        theme: dict = None,
        width: int = None,
        force_terminal: bool = None,
        color_system: str = "auto",
    ):
        self._theme = {**_DEFAULT_THEME, **(theme or {})}
        self._width = width
        self._force_terminal = force_terminal
        self._color_system = color_system
        self._console = None

    def get_console(self) -> RichConsole:
        """获取 Console 实例（懒创建）"""
        if self._console is None:
            rich_theme = Theme(self._theme, inherit=False)
            self._console = RichConsole(
                theme=rich_theme,
                width=self._width,
                force_terminal=self._force_terminal,
                color_system=self._color_system,
            )
        return self._console

    def set_theme(self, theme_dict: dict):
        """更新主题（下次获取 console 时生效）"""
        self._theme.update(theme_dict)
        self._console = None  # 重建

    def reset(self):
        """重置（用于测试）"""
        self._console = None


# 模块级默认管理器
_manager = ConsoleManager()


def get_console() -> RichConsole:
    """获取全局 Rich Console 实例"""
    return _manager.get_console()


def set_theme(theme_dict: dict):
    """更新全局主题"""
    _manager.set_theme(theme_dict)


def init_console(theme: dict = None, width: int = None, force_terminal: bool = None):
    """初始化全局 Console（在 Main.__init__ 中调用）"""
    global _manager
    _manager = ConsoleManager(
        theme=theme or {},
        width=width,
        force_terminal=force_terminal,
    )
