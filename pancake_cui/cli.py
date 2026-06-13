"""CLI 命令框架 — 基于 Click 的装饰器驱动命令注册

对标 Spring Shell / picocli，通过装饰器定义 CLI 命令和参数。

使用方法:
    @Command(name="serve", help="启动服务")
    @Option("--port", "-p", default=8080, help="端口号")
    @Option("--debug", is_flag=True, help="调试模式")
    async def serve(port, debug):
        print_panel(f"服务启动于 :{port}")

    @Group(name="db", help="数据库管理")
    class DbCommands:
        pass

    @Command(name="migrate", help="运行迁移", group="db")
    async def migrate():
        ...
"""

import asyncio
import functools
import inspect
import logging
from typing import Callable

logger = logging.getLogger(__name__)

# ============================================================
#  命令注册表
# ============================================================

# 命令注册表: {name: _CommandInfo}
_command_registry: dict[str, "_CommandInfo"] = {}

# 分组注册表: {name: _GroupInfo}
_group_registry: dict[str, "_GroupInfo"] = {}

# 前置/后置钩子: {group_or_name: [(hook_func, "before"|"after")]}
_hook_registry: dict[str, list] = {}


class _CommandInfo:
    """命令元信息"""

    def __init__(self, name: str, func: Callable, help: str = None, group: str = None):
        self.name = name
        self.func = func
        self.help = help or func.__doc__
        self.group = group
        self.params: list = []
        self.is_async = asyncio.iscoroutinefunction(func)
        self.before_hooks: list[Callable] = []
        self.after_hooks: list[Callable] = []


class _GroupInfo:
    """命令分组元信息"""

    def __init__(self, name: str, cls: type, help: str = None):
        self.name = name
        self.cls = cls
        self.help = help or cls.__doc__


# ============================================================
#  装饰器
# ============================================================

def Command(name: str = None, help: str = None, group: str = None):
    """@Command — 注册 CLI 子命令

    Args:
        name:  命令名称（默认使用函数名，下划线转连字符）
        help:  帮助信息（默认使用 docstring）
        group: 所属分组名称

    用法:
        @Command(name="serve", help="启动服务")
        async def serve(port=8080):
            ...
    """
    def decorator(func: Callable) -> Callable:
        nonlocal name
        if name is None:
            name = func.__name__.replace("_", "-")

        info = _CommandInfo(name, func, help, group)

        # 收集 Option/Argument 装饰器附加的参数
        if hasattr(func, "_cui_params"):
            info.params = func._cui_params

        # 收集 Before/After 钩子
        if hasattr(func, "_cui_before"):
            info.before_hooks = func._cui_before
        if hasattr(func, "_cui_after"):
            info.after_hooks = func._cui_after

        _command_registry[name] = info
        logger.debug(f"CUI 命令注册: {name}")

        @functools.wraps(func)
        def wrapper(*a, **kw):
            return func(*a, **kw)

        wrapper._cui_info = info
        return wrapper
    return decorator


def Group(name: str = None, help: str = None):
    """@Group — 注册命令分组（类装饰器）

    Args:
        name: 分组名称（默认使用类名）
        help: 帮助信息

    用法:
        @Group(name="db", help="数据库管理")
        class DbCommands:
            pass
    """
    def decorator(cls: type) -> type:
        nonlocal name
        if name is None:
            name = cls.__name__.replace("_", "-").lower()

        info = _GroupInfo(name, cls, help)
        _group_registry[name] = info
        logger.debug(f"CUI 分组注册: {name}")
        return cls
    return decorator


def Option(*param_decls, **kwargs):
    """@Option — 添加命令选项 (--option)

    Args:
        *param_decls: 参数声明，如 ("--port", "-p")
        **kwargs: Click Option 参数 (default, type, is_flag, help, required 等)

    用法:
        @Command(name="serve")
        @Option("--port", "-p", default=8080, help="端口号")
        @Option("--debug", is_flag=True, help="调试模式")
        async def serve(port, debug):
            ...
    """
    import click

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_cui_params"):
            func._cui_params = []
        func._cui_params.append(click.Option(param_decls, **kwargs))
        return func
    return decorator


def Argument(*param_decls, **kwargs):
    """@Argument — 添加命令参数 (positional)

    Args:
        *param_decls: 参数声明，如 ("config_file",)
        **kwargs: Click Argument 参数 (required, default, type 等)

    用法:
        @Command(name="run")
        @Argument("config_file", required=False)
        async def run(config_file):
            ...
    """
    import click

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_cui_params"):
            func._cui_params = []
        func._cui_params.append(click.Argument(param_decls, **kwargs))
        return func
    return decorator


def Before(name: str = None, group: str = None):
    """@Before — 命令前置钩子

    在指定命令或分组的所有命令执行前运行。

    Args:
        name:  命令名称（精确匹配）
        group: 分组名称（该分组所有命令执行前运行）

    用法:
        @Before(group="db")
        def check_db():
            print("检查数据库连接...")
    """
    def decorator(func: Callable) -> Callable:
        key = name or group or "_global"
        if key not in _hook_registry:
            _hook_registry[key] = []
        _hook_registry[key].append(("before", func))
        return func
    return decorator


def After(name: str = None, group: str = None):
    """@After — 命令后置钩子

    在指定命令或分组的所有命令执行后运行。

    Args:
        name:  命令名称
        group: 分组名称
    """
    def decorator(func: Callable) -> Callable:
        key = name or group or "_global"
        if key not in _hook_registry:
            _hook_registry[key] = []
        _hook_registry[key].append(("after", func))
        return func
    return decorator


# ============================================================
#  CLI 构建器
# ============================================================

def _make_click_callback(info: _CommandInfo) -> Callable:
    """将命令函数包装为 Click 回调（处理 async + 钩子）"""

    async def _run_with_hooks():
        # Before 钩子
        for hook in info.before_hooks:
            result = hook()
            if asyncio.iscoroutine(result):
                await result

        # 执行命令
        if info.is_async:
            await info.func()
        else:
            info.func()

        # After 钩子
        for hook in info.after_hooks:
            result = hook()
            if asyncio.iscoroutine(result):
                await result

    @functools.wraps(info.func)
    def callback(*args, **kwargs):
        # 绑定参数到函数
        sig = inspect.signature(info.func)
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        # 执行全局前置钩子
        global_hooks = _hook_registry.get("_global", [])
        for hook_type, hook_func in global_hooks:
            if hook_type == "before":
                r = hook_func()
                if asyncio.iscoroutine(r):
                    asyncio.run(r)

        # 执行分组/命令钩子 + 命令
        if info.is_async:
            asyncio.run(_run_with_hooks())
        else:
            info.func(*args, **kwargs)

        # 执行全局后置钩子
        for hook_type, hook_func in global_hooks:
            if hook_type == "after":
                r = hook_func()
                if asyncio.iscoroutine(r):
                    asyncio.run(r)

    return callback


def build_cli(app_name: str = "app", version: str = "0.1.0"):
    """构建 Click CLI Group

    将所有注册的命令和分组装入一个 Click Group。

    Args:
        app_name: 应用名称
        version:  版本号

    Returns:
        click.Group 实例
    """
    import click

    cli = click.Group(name=app_name, help=f"{app_name} v{version}")

    # 构建分组
    click_groups: dict[str, click.Group] = {}
    for group_name, group_info in _group_registry.items():
        click_group = click.Group(name=group_name, help=group_info.help)
        click_groups[group_name] = click_group

    # 注册命令
    for cmd_name, info in _command_registry.items():
        callback = _make_click_callback(info)

        # 从函数签名生成 Click 参数
        params = list(info.params)  # 装饰器定义的参数
        if not params:
            params = _extract_click_params(info.func)

        cmd = click.Command(
            name=info.name,
            callback=callback,
            params=params,
            help=info.help,
        )

        if info.group and info.group in click_groups:
            click_groups[info.group].add_command(cmd)
        else:
            cli.add_command(cmd)

    # 将分组添加到主 CLI
    for group_name, click_group in click_groups.items():
        cli.add_command(click_group)

    return cli


def _extract_click_params(func: Callable) -> list:
    """从函数签名提取 Click 参数"""
    import click

    params = []
    sig = inspect.signature(func)

    for name, param in sig.parameters.items():
        if name == "self":
            continue

        # 判断类型
        param_type = click.STRING
        is_flag = False
        default = param.default

        if param.annotation is bool or default is True or default is False:
            param_type = click.BOOL
            is_flag = default is False or default is True
            if default is None:
                default = False
        elif param.annotation is int:
            param_type = click.INT
        elif param.annotation is float:
            param_type = click.FLOAT

        # 有默认值 → Option，否则 → Argument
        if default is not inspect.Parameter.empty:
            option_name = f"--{name.replace('_', '-')}"
            params.append(click.Option(
                [option_name],
                type=param_type,
                default=default,
                is_flag=is_flag,
                show_default=True,
            ))
        else:
            params.append(click.Argument([name], type=param_type))

    return params


def get_command_registry() -> dict[str, _CommandInfo]:
    """获取命令注册表（用于测试）"""
    return dict(_command_registry)


def get_group_registry() -> dict[str, _GroupInfo]:
    """获取分组注册表（用于测试）"""
    return dict(_group_registry)


def clear_registries():
    """清空所有注册表（用于测试）"""
    _command_registry.clear()
    _group_registry.clear()
    _hook_registry.clear()
