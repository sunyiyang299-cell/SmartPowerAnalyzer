# V0.1 基础框架交付与验证记录

验证日期：2026-10-20。平台：Windows，Python 3.13.0（按本次确认由 3.12 调整为 3.13）。

## 实现内容

正式窗口标题为《智电析电力系统运行数据分析与可视化软件 V1.0》，开发版本为 0.1.0。
已提供模块化入口、浅色主窗口、左侧导航及八个页面，使用 QStackedWidget 切换。
保留原生窗口控制、缩放与滚动，提供清晰的功能说明及待开发状态。
没有硬编码电气指标、曲线或分析结论，数据导入、算法及导出未在本阶段实现。

## 已执行验证

| 阶段 | 执行内容 | 结果 |
| --- | --- | --- |
| 语法 | `python -m compileall -q main.py smartpower tests` | 通过 |
| 结构 | `python -m unittest discover -s tests -p test_structure.py -v` | 3/3 通过 |
| 存储 | `python -m unittest discover -s tests -p test_database.py -v` | 1/1 通过 |
| 界面离屏 | `python -m unittest discover -s tests -p test_window.py -v` | 7/7 通过 |
| 完整回归 | `python -m unittest discover -s tests -v`，Qt offscreen | 12/12 通过 |
| Windows 原生 | `python -m unittest tests.test_window tests.test_entrypoint -v`，Qt windows | 8/8 通过 |
| 依赖 | `python -m pip check` | No broken requirements found |
| 格式 | `git diff --check` | 通过 |

完整套件包含 12 个独立测试，原生运行的 8 项为其中 GUI 与入口测试的复跑，不另算 8 项功能。
覆盖八按钮往返点击、互斥选中、标题、状态栏、首页入口、空格键、程序化路由同步、非法路由、待开发提示、最小尺寸适配、窗口尺寸与状态、SQLite 幂等初始化、依赖导入以及 main.py 子进程事件循环与正常退出。

已在 Windows 原生 Qt 后端成功显示窗口并自动执行上述操作，另抓取默认尺寸首页、电压分析页、最小尺寸首页并目视检查截图布局。未进行人工鼠标交互验收；截图不包含操作系统标题栏。未测试打包安装、其他 Windows 版本、多显示器及其他缩放比例。
仓库提供 Windows/Python 3.13 CI；本记录的通过结果来源于本地实际执行，远程 CI 结果以 PR 页面为准。

依赖版本：PySide6 6.10.3、Pandas 3.0.6、NumPy 2.5.4、PyQtGraph 0.14.0。
SQLite 来自 Python 标准库。因初次深路径环境遇到 Windows 路径长度限制，本地测试使用较短路径的独立虚拟环境，README 已提供对应处理说明。

## 修改文件清单

| 文件 | 作用 |
| --- | --- |
| `.gitignore` | 排除虚拟环境、缓存及本地数据库 |
| `.github/workflows/tests.yml` | Windows Python 3.13 自动测试 |
| `main.py` | 程序入口 |
| `requirements.txt` | 四项直接依赖 |
| `README.md` | 安装、运行、测试与扩展说明 |
| `docs/VALIDATION_V0.1.md` | 本次文件清单和测试记录 |
| `smartpower/__init__.py` | 软件包 |
| `smartpower/config.py` | 正式名称、开发版本 |
| `smartpower/application.py` | 应用初始化及事件循环 |
| `smartpower/ui/__init__.py` | UI 包 |
| `smartpower/ui/main_window.py` | 主窗口、导航和页面切换 |
| `smartpower/ui/theme.py` | 统一浅色主题 |
| `smartpower/ui/widgets.py` | 共享卡片与标签 |
| `smartpower/ui/pages/__init__.py` | 页面包 |
| `smartpower/ui/pages/base.py` | 通用滚动页面 |
| `smartpower/ui/pages/registry.py` | 八个页面及说明的注册 |
| `smartpower/ui/pages/home.py` | 首页及有效快捷入口 |
| `smartpower/ui/pages/features.py` | 业务模块待开发页面 |
| `smartpower/ui/pages/settings.py` | 软件与真实环境信息 |
| `smartpower/storage/__init__.py` | 存储包 |
| `smartpower/storage/database.py` | 显式 SQLite 元数据初始化 |
| `tests/__init__.py` | 测试包 |
| `tests/test_structure.py` | 结构、身份和技术栈测试 |
| `tests/test_database.py` | SQLite 初始化与无分析数据测试 |
| `tests/test_window.py` | 页面与窗口行为测试 |
| `tests/test_entrypoint.py` | 入口启动、事件循环和退出测试 |

共 26 个文件：更新 1 个 README，新增 25 个文件。
