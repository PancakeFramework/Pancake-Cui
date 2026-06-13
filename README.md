# pancake-cui

CLI 框架 + TUI 交互界面插件，基于 Click + Rich，通过装饰器驱动。

## 特性

- **CLI 命令框架** — `@Command` / `@Group` / `@Option` / `@Argument`，支持 async
- **前置/后置钩子** — `@Before` / `@After`
- **Rich 组件** — Table / Panel / Tree / Markdown / Progress
- **快捷输出** — `print_table` / `print_panel` / `print_json` / `print_tree`
- **Struct → 表格** — `print_objects()` 自动将 dataclass 列表转为表格
- **交互式组件** — 菜单 / 表单 / 确认 / 选择 / 多选 / 密码输入
- **异步进度条** — `async with show_progress()`
- **主题系统** — 可自定义颜色主题

## 安装

```bash
pip install pancake-cui
```

## 配置

```yaml
pancake:
  cui:
    app_name: "MyApp"
    version: "1.0.0"
    theme:
      primary: "cyan"
      success: "green"
      warning: "yellow"
      error: "red bold"
```

## 使用方法

### 1. CLI 命令

```python
@Command(name="serve", help="启动服务")
@Option("--port", "-p", default=8080, help="端口号")
@Option("--debug", is_flag=True, help="调试模式")
async def serve(port, debug):
    print_panel(f"服务启动于 :{port}", title="启动")

@Group(name="db", help="数据库管理")
class DbCommands:
    pass

@Command(name="migrate", help="运行迁移", group="db")
async def migrate():
    print_success("迁移完成")

@Before(group="db")
def check_db():
    print_info("检查数据库连接...")
```

### 2. 表格输出

```python
print_table(
    headers=["ID", "姓名", "年龄"],
    rows=[[1, "Alice", 18], [2, "Bob", 20]],
    title="用户列表"
)
```

### 3. Struct 对象 → 表格

```python
users = [User(id=1, name="Alice"), User(id=2, name="Bob")]
print_objects(users, fields=["id", "name"], title="用户列表")
```

### 4. 面板 / JSON / 树

```python
print_panel("服务已启动", title="启动成功", border_style="green")
print_json({"name": "Alice", "scores": [90, 85]})
print_tree({"db": {"host": "localhost", "port": 5432}}, root_label="配置")
```

### 5. 交互式组件

```python
choice = await show_menu("请选择", ["新建", "编辑", "删除"])
data = await show_form({"name": {"label": "用户名", "required": True}})
ok = await show_confirm("确认删除？")
name = await show_select("选择用户", ["Alice", "Bob"])
tags = await show_checkbox("选择标签", ["Python", "Redis"])
pwd = await show_password("请输入密码")
```

### 6. 进度条

```python
async with show_progress("下载中...", total=100) as p:
    for i in range(100):
        await download_chunk(i)
        p.advance(1)
```

## 架构

```
console.py       →  Rich Console 单例 + 主题
cli.py           →  @Command / @Group / @Option / @Argument / @Before / @After
display.py       →  make_table / make_panel / make_tree / make_progress
output.py        →  print_table / print_panel / print_json / print_tree / print_objects
interactive.py   →  show_menu / show_form / show_confirm / show_select / show_progress
```
