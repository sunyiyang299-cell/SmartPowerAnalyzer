# 智电析电力系统运行数据分析与可视化软件 V1.0

Windows 桌面软件，开发版本 **V0.2.0 数据管理系统**。按本次确认使用 64 位 Python 3.13。
产品正式名称中的 V1.0 与开发版本分别管理。V0.1 的八个页面、导航、首页入口和原生窗口操作均保留。

## 安装与运行

在 Windows PowerShell 执行，推荐较短的目录，避免 Windows 路径长度限制：

```powershell
git clone https://github.com/sunyiyang299-cell/SmartPowerAnalyzer.git
cd SmartPowerAnalyzer
git switch feature/v0.2-data-management
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

如果没有 Python Launcher，可用指向 Python 3.13 的 `python` 替代 `py -3.13`。
直接调用虚拟环境的 Python，无需修改 PowerShell 执行策略。当前提供源码运行，尚无 `.exe` 安装包。
运行依赖为 PySide6、Pandas、NumPy、PyQtGraph 和 Excel 引擎 openpyxl；SQLite 是 Python 标准库。

## 导入、校验与预览

1. 打开“数据管理”，点击“导入 CSV / Excel”，选择 `.csv` 或 `.xlsx`；支持中文路径。
2. 文件第一行为表头，必须包含下面四个中文字段。CSV 支持 UTF-8（含 BOM）和 GB18030，采用逗号分隔；Excel 读取第一个工作表。
3. 后台解析并校验全部记录，成功后显示预览。输入数据集名称，点击“保存数据集”才会写入 SQLite。
4. 任意一条记录错误都会拒绝本次文件，显示字段、数据行号和原因，不静默丢弃或填补记录。失败后保留原预览和历史数据。

| 字段 | 约定与校验 |
| --- | --- |
| 时间 | 本地无时区日期时间，例如 `2026-10-20 10:00:00`；支持年月日、日期加时分秒及小数秒，也支持格式化的 Excel 日期单元格 |
| 电压 | 单相交流电压有效值，单位 V，有限数值且 ≥ 0 |
| 电流 | 单相交流电流有效值，单位 A，有限数值且 ≥ 0 |
| 功率因数 | 非负功率因数，有限数值，0～1（含端点） |

不猜测数字时间戳的单位、Excel 纯数字日期序号或时区，遇到这些格式请先转换。
表头首尾空格可忽略；重复表头会被拒绝。缺失值、非法数字、NaN、正负无穷和不可能日期均有提示。
错误详情最多展示前 40 处，同时报告总错误数；数据第 1 行指表头之后的第一条记录。
额外字段会明确提示“不参与预览和保存”，保存内容为上述四个字段及数据集元信息。
导入文件标记为“来源未核验”，不代表软件已验证真实设备来源。

## 表格、筛选与排序

- QTableView 采用只读模型，支持水平和垂直滚动、选择记录，显示全部已通过校验的数据。
- 点击表头按列升降序排列，数值按数值大小排列，时间按日期时间排列；来源列为数据集统一标记。
- 选择“全部字段”或指定字段，输入包含文本，点击“筛选”；按文字包含关系匹配，不使用正则表达式。点击“清除”恢复全部记录。
- 显示总记录数及当前显示数。排序和筛选仅改变视图，**保存及模拟 CSV 导出始终使用全部记录**。
- 解析、校验、生成、数据库读写、筛选、排序和 CSV 导出在后台线程执行。任务期间可以切换导航，操作按钮暂时禁用，关闭窗口会提示等待任务完成。
- 导入数据采用内存加载，尚非流式数据库分页。已测试十万条 CSV；可处理规模仍取决于内存、文件复杂度和硬件，不承诺无限大文件。

## SQLite 历史数据集

点击“刷新历史”初始化/读取本地数据库，再选择历史数据集并点击“读取”。列表显示名称、记录数、导入时间和来源标记。
数据库路径显示在数据管理页底部，默认使用 Qt 的用户本地应用数据目录（Windows 下通常位于 `%LOCALAPPDATA%`）；以界面展示的实际路径为准。
需要指定路径时，在启动前设置：

```powershell
$env:SMARTPOWER_DB_PATH = "C:\你的数据目录\datasets.sqlite3"
.\.venv\Scripts\python.exe main.py
```

保存与删除使用事务，失败时回滚，错误明确显示，预览保留以便重试。程序不会因导入文件错误或常见数据库操作失败直接退出。
“删除”仅删除指定数据集及其采样记录，弹出中文确认框，默认“取消”。删除当前已加载数据集后，内存预览仍保留并重新标记为未保存。
替换未保存预览及退出前会询问是否放弃预览。历史记录不会被导入自动覆盖；同名保存作为独立数据集管理。
首次使用可升级 V0.1 的元数据模式至版本 2；检测到更高版本则拒绝操作，不降级覆盖。
启动主窗口本身不创建数据库；首次刷新历史或保存时才初始化。备份时请关闭程序，再复制界面显示的 SQLite 文件。

## 模拟数据

点击“生成 1000 条模拟数据”可预览单相交流演示数据：电压 218～242 V、电流 0.5～25 A、功率因数 0.85～1，时间从 `2026-01-01 00:00:00` 起每秒一条。
这些范围仅用于软件演示，不作为设备合格判据或电气分析结果。数据采用固定随机种子，便于重复测试。
界面、历史列表、数据库元数据及导出 CSV 的“数据来源”列均标注模拟数据，不冒充真实设备测量。
模拟 CSV 重新导入后仍保留模拟标记；混有模拟标记的文件整批按模拟数据标记。

点击“导出模拟 CSV”选择目标路径，覆盖已有文件需要确认；临时文件写完后原子替换目标文件，失败时保留原文件。
也可独立运行生成模块：

```powershell
.\.venv\Scripts\python.exe -m smartpower.data.demo --output "模拟数据.csv"
```

命令行默认拒绝覆盖已有文件；确需覆盖时显式加 `--overwrite`。
数据来源列是用户可编辑的文件标记，不具备防篡改证明能力。

## 自动化测试

新增测试使用 Pytest，原有 unittest 用例保留，由 Pytest 一并收集。仅开发测试需要 `requirements-dev.txt`：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests/test_importer.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_repository.py tests/test_database.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_demo.py tests/test_query.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_data_ui.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

GUI 测试默认 `offscreen`。Windows 原生后端复验（会短暂显示窗口）：

```powershell
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m pytest tests/test_window.py tests/test_data_ui.py tests/test_entrypoint.py -q
Remove-Item Env:QT_QPA_PLATFORM
```

CI 在 Windows/Python 3.13 下运行 Pytest。测试涵盖 CSV/Excel、中文路径、字段和数值校验、事务回滚、读写删除、模拟数据标记、原子导出、模型排序筛选、十万条后台导入响应及窗口保护。
本阶段实际执行结果及新增文件清单见 [V0.2 验证记录](docs/VALIDATION_V0.2.md)，V0.1 记录保留作历史参考。
沙箱环境如不能访问默认临时目录，可将 `TEMP`、`TMP` 和 Pytest 的 `--basetemp` 指向有写入权限的工作目录；不要通过跳过失败测试规避问题。

## 模块结构与扩展

```text
main.py                         桌面入口
smartpower/
  application.py                Qt 初始化、中文翻译、事件循环
  config.py                     正式名称、开发版本
  data/
    validation.py               独立字段、时间和电气数值校验
    importer.py                 Pandas CSV / Excel 导入及数据集对象
    demo.py                     独立模拟数据生成、原子 CSV 导出与命令行
    query.py                    后台排序筛选视图索引
  storage/
    database.py                 保留 V0.1 元数据初始化接口
    repository.py               SQLite 模式升级、事务与历史数据仓库
  ui/
    main_window.py              主窗口、导航、退出保护
    tasks.py                    后台任务，结果在主线程消费
    table_model.py              QAbstractTableModel，只读按需取值
    pages/data_management.py    数据管理控件和任务编排
    pages/registry.py           八个页面注册表
    pages/{base,home,features,settings}.py
    theme.py / widgets.py       共用浅色样式和控件
tests/                          V0.1 回归及 V0.2 Pytest 测试
requirements.txt                运行依赖
requirements-dev.txt            测试依赖
.github/workflows/tests.yml     Windows CI
```

数据处理和数据库模块不依赖 Qt。界面通过后台任务调用它们，模型更新仅在 GUI 线程执行；新增分析算法仍应放在独立服务中。
电压、电流、功率分析、异常检测和报告页在本阶段继续保留待开发说明，没有新增虚假分析结果。

接口参考：[Pandas read_excel](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html)、[Qt 表格模型](https://doc.qt.io/qtforpython-6.6/PySide6/QtCore/QAbstractTableModel.html)、[Qt QThread](https://doc.qt.io/qtforpython-6.10/PySide6/QtCore/QThread.html)。
