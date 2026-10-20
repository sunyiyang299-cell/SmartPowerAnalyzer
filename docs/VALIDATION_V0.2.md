# V0.2 数据管理系统交付与验证记录

验证日期：2026-10-20。环境：Windows，64 位 Python 3.13.0，PySide6 6.10.3，Pandas 3.0.6，NumPy 2.5.4，PyQtGraph 0.14.0，openpyxl 3.1.5，Pytest 9.1.1。

## 本次实现

- CSV / Excel（第一工作表）导入，支持中文路径，Pandas 解析与整批校验。
- 校验空文件、表头、重复字段、缺失值、时间、有限非负电压电流及 0～1 功率因数；显示错误字段、数据行号和总数，最多展示前 40 处。
- QTableView 预览、双向滚动、数值/时间排序、按字段或全字段文本筛选及总记录数显示。
- 校验、导入、排序筛选、SQLite 操作、生成与导出在后台线程执行，模型与控件更新在主线程进行。
- SQLite 数据集名称、带时区导入时间、模拟来源元数据及全部采样数据持久化；历史读取、确认删除、事务回滚和 V0.1 模式升级。
- 生成 1000 条明确标记的单相交流模拟数据，支持界面与独立命令行 CSV 导出；原子替换，覆盖前确认。
- 保留 V0.1 八个页面、导航和窗口操作；替换预览和退出时保护未保存数据，后台任务未完成时阻止关闭。

没有实现电气分析算法或伪造分析结论。模拟数据仅用于演示，不是设备测量，也不作为电气合格判据。

## 分阶段测试与最终结果

| 阶段 | 已实际执行的检查 | 结果 |
| --- | --- | --- |
| V0.1 基线 | 原有 unittest 全量回归 | 12/12 通过 |
| 导入与校验 | 首批 CSV、Excel、空文件、字段和非法值测试 | 22 项通过 |
| 存储与校验复验 | repository、旧 database、importer | 31 项通过 |
| 模拟数据及查询 | demo、query | 首批 5 项通过 |
| 数据管理界面 | 生成、预览、筛选、排序、保存、读取、删除、失败保留和后台响应 | 首批 5 项通过，扩展后 10 项通过 |
| 最终完整回归 | `python -m pytest -q`，Qt offscreen | **61 passed，26 subtests passed** |
| 最终原生 Windows GUI | `python -m pytest tests/test_window.py tests/test_data_ui.py tests/test_entrypoint.py -q`，Qt windows | **18 passed，21 subtests passed** |
| 依赖 | `python -m pip check` | No broken requirements found |
| 语法 | `python -m compileall -q main.py smartpower tests` | 通过 |
| 差异格式 | `git diff --check` | 通过 |

完整套件最后一次执行耗时 13.33 秒，原生 GUI 复跑耗时 7.43 秒；仅代表本机此次执行。原生测试是完整套件中相关用例的重复验证，不是另外 18 个独立功能。

测试期间曾遇到并处理：沙箱默认临时目录无写权限（将 TEMP、TMP 及 basetemp 指向工作目录）；混合时间格式测试夹具需明确 format；历史列表需默认选中首条；模型重置时需避免递归请求排序；滚动条断言需等待 Qt 布局完成。对应失败用例均保留并重跑通过，没有删除用例来规避失败。

首次远程 Windows CI 发现两处额外问题：英文系统的 cp1252 重定向输出无法打印中文，以及较长英文数据库路径撑大最小页面宽度。已先用强制 cp1252 子进程和超长 ASCII 路径在本地复现失败，再分别修复为显式 UTF-8 命令行输出和可任意位置换行的只读路径框。原失败用例保留，新增路径回归测试后，完整套件为上述 61 项。

事务测试通过 SQLite 触发器主动制造中途插入/删除失败，验证已有数据集、采样记录和预览保持可用；GUI 测试验证错误提示及重试按钮。中文删除确认框测试验证默认按钮为“取消”。

## 性能与图形验证边界

已实际使用 Qt `windows` 原生后端显示窗口并自动执行操作；抓取并查看默认尺寸和最小尺寸的模拟数据预览截图。一次十万条 CSV 导入约 0.281 秒、10 毫秒界面定时器触发 25 次；另一次约 0.367 秒、触发 24 次。仅为当前机器上的样本，不是任意文件的性能承诺。

文件采用内存加载，尚未实现流式导入或数据库分页。未进行人工鼠标验收、打包安装、多显示器、其他 Windows 版本或其他缩放比例验证。文件对话框的操作入口使用自动化替身验证，真实 Windows 文件选择器的人工交互尚未验收。

远程 CI 由 PR 的 GitHub Actions 单独运行，结果以 PR 检查为准。本记录中的通过数均来自本地实际执行。

## 新增文件清单（18 个）

| 文件 | 用途 |
| --- | --- |
| `docs/VALIDATION_V0.2.md` | 本次交付记录 |
| `pytest.ini` | 测试发现配置 |
| `requirements-dev.txt` | 独立开发测试依赖 |
| `smartpower/data/__init__.py` | 数据处理包 |
| `smartpower/data/validation.py` | 字段、时间、缺失值和电气数值校验 |
| `smartpower/data/importer.py` | Pandas 文件导入与数据集对象 |
| `smartpower/data/demo.py` | 模拟数据生成、原子导出及命令行 |
| `smartpower/data/query.py` | 后台排序与筛选视图索引 |
| `smartpower/storage/repository.py` | SQLite 模式管理、事务和数据集仓库 |
| `smartpower/ui/pages/data_management.py` | 数据管理页面与任务编排 |
| `smartpower/ui/table_model.py` | 只读表格模型 |
| `smartpower/ui/tasks.py` | 后台任务线程 |
| `tests/conftest.py` | GUI 测试后端默认值 |
| `tests/test_importer.py` | CSV、Excel、中文路径及校验 |
| `tests/test_repository.py` | 存储、读取、删除、迁移与回滚 |
| `tests/test_demo.py` | 生成、来源、导出、命令行与覆盖保护 |
| `tests/test_query.py` | 数值排序与文字筛选 |
| `tests/test_data_ui.py` | 数据管理流程、失败提示与 GUI 保护 |

## 更新文件清单（12 个）

`.github/workflows/tests.yml`、`.gitignore`、`README.md`、`requirements.txt`、`smartpower/application.py`、`smartpower/config.py`、`smartpower/ui/main_window.py`、`smartpower/ui/pages/home.py`、`smartpower/ui/pages/registry.py`、`smartpower/ui/pages/settings.py`、`tests/test_structure.py`、`tests/test_window.py`。

原有结构测试的版本断言更新为 0.2.0，页面测试由数据管理占位检查改为实际数据管理页面检查，其他分析页继续检查待开发提示。原测试文件全部保留。
