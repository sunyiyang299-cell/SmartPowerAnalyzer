# 智电析电力系统运行数据分析与可视化软件 V1.0

SmartPowerAnalyzer 是一款面向 Windows 的电力系统运行数据分析桌面软件。
当前开发版本为 **V0.1.0 基础框架**；产品正式名称中的 V1.0 与开发版本分别管理。

## 本次功能范围

- PySide6 原生桌面主窗口，浅色界面、左侧导航、状态栏。
- 首页、数据管理、电压分析、电流分析、功率分析、异常检测、分析报告、系统设置共八个页面。
- 使用 `QStackedWidget` 切换，导航选中状态同步；首页快捷入口、键盘 Tab/空格操作可用。
- 保留 Windows 原生标题栏及最小化、最大化、关闭、拖拽缩放能力；最小窗口为 900 × 620，内容可滚动。
- 软件与环境信息展示、SQLite 元数据初始化基础模块、自动化测试及 Windows CI。

**当前尚未实现**数据导入、分析算法、图表、异常检测、报告导出及可修改设置。
各业务页面明确标注待开发，不包含模拟指标、曲线或虚假分析结果。
Pandas、NumPy 和 PyQtGraph 已作为后续开发依赖安装和验证；当前不调用它们生成任何数据。
SQLite 使用 Python 标准库 `sqlite3`，无需额外安装数据库服务；启动程序不会创建数据库。

## 安装（Windows PowerShell）

按当前确认的开发环境，使用 **64 位 Python 3.13**。

```powershell
git clone https://github.com/sunyiyang299-cell/SmartPowerAnalyzer.git
cd SmartPowerAnalyzer
# 本 PR 合并前，切换到开发分支：
git switch feat/v0.1-desktop-framework
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

若未安装 Python Launcher，可用指向 Python 3.13 的 `python` 替代 `py -3.13`。
无需激活虚拟环境，直接调用其中的 Python，避免 PowerShell 脚本执行策略限制。
若安装 Qt 时出现 Windows 路径过长错误，请将仓库和虚拟环境放到较短的路径（例如 `C:\dev\SmartPowerAnalyzer`），再安装依赖。

## 运行

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe main.py
```

点击左侧任一模块可切换页面，首页也提供数据管理和设置入口。设置页展示真实运行时版本信息。
本阶段无需外部数据文件、账号、网络服务或数据库配置，也尚未提供 `.exe` 安装包。

## 测试

测试使用 Python 标准库 `unittest` 和 PySide6 自带的 `QTest`，无需 pytest 等额外依赖。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_structure.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_database.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_window.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

GUI 测试默认使用 Qt `offscreen` 后端，验证页面、鼠标点击、快捷入口、键盘、导航同步、缩放及窗口状态。
这不能替代真实 Windows 桌面上的人工交互验收。在可用的 Windows 桌面中，可额外运行原生后端测试（会短暂显示测试窗口）：

```powershell
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m unittest tests.test_window -v
Remove-Item Env:QT_QPA_PLATFORM
```

手工验收：启动 `main.py`，逐一点击八个导航；检查选中项、标题及说明；检查首页两个入口；最大化、还原、最小化及恢复；拖动边框缩放；在最小尺寸下滚动内容并通过 Tab/空格操作按钮。分析页应始终显示待开发说明。

## 项目结构

```text
main.py                         程序入口
requirements.txt                固定版本的四项直接依赖
smartpower/
  config.py                     正式名称、开发版本
  application.py                QApplication 创建、主题、事件循环
  ui/
    main_window.py              主窗口、导航及页面栈
    theme.py                    浅色样式
    widgets.py                  共享标签、卡片
    pages/
      base.py                   可滚动页面壳
      registry.py               八个页面的注册、顺序及构造
      home.py                   首页及快捷入口
      features.py               业务模块待开发页面
      settings.py               软件与运行环境信息
  storage/
    database.py                 显式 SQLite 初始化边界
tests/
  test_entrypoint.py            子进程验证 main.py 事件循环与退出
  test_structure.py             名称、入口和技术栈导入检查
  test_database.py              初始化、幂等性、无分析数据检查
  test_window.py                导航、页面、快捷入口和窗口行为
.github/workflows/tests.yml     Windows / Python 3.13 CI
```

## 后续扩展

新增页面时创建独立的页面模块，并在 `PAGE_SPECS` 中注册稳定 key、名称及工厂，导航会自动生成。
业务逻辑应放入后续独立的服务模块，数据访问放入 `storage`；页面负责展示与用户操作，不直接混入计算或 SQL。
当前 `initialize_database(path)` 仅显式建立模式版本元数据，不插入电气记录；后续数据结构变更须引入迁移。
电气算法需先约定数据字段、采样时间、单位、计算方法和限值来源，并以已知输入与期望值编写测试后接入界面。

Qt 页面切换与互斥导航采用官方接口，参见 [QStackedWidget](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QStackedWidget.html) 和 [QButtonGroup](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QButtonGroup.html)。
