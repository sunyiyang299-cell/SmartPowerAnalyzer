# V0.3 电气参数分析与计算系统验证记录

日期：2026-10-20。正式软件名称：智电析电力系统运行数据分析与可视化软件 V1.0；开发版本 0.3.0。

## 开发前核对与环境

- 已获取最新 main，基线提交为 `904f9741554778176a0ca936de509d3ec8cdbf0c`，GitHub PR #1、#2 均已合并。
- 在现有仓库上创建 `feature/v0.3-electrical-analysis`；使用独立工作树，没有重建项目或覆盖旧开发分支。
- 已读取 README、数据对象、导入与校验、SQLite 仓库、GUI 注册表/主窗口/后台线程及现有测试和 CI。
- 本地：Windows、64 位 Python 3.13.0、PySide6 6.10.3、Pandas 3.0.6、NumPy 2.5.4、PyQtGraph 0.14.0、openpyxl 3.1.5、Pytest 9.1.1。
- 仍使用现有运行依赖、开发依赖及 Windows/Python 3.13 CI，不增加第三方依赖。
- 字段约定：时间为本地无时区日期时间，电压/电流为单相交流有效值（V/A），功率因数为 0～1 的非负数。

## 实现功能与公式

电压、电流、PF 的核心统计使用 NumPy，返回 Statistics 结构：数量、均值、最大值、最小值、总体标准差及单位。`ddof=0`，各采样点等权：

```text
μ = Σxᵢ / N
σ = sqrt(Σ(xᵢ − μ)² / N)
```

电流最大值是采样有效值最大值，不是瞬时峰值。平均 PF 是采样点的算术平均值，不是时间段综合 PF。

单相正弦稳态模型逐点计算：

```text
S = U × I                                  （VA）
P = S × PF                                 （W）
|Q| = S × sqrt(max(0, (1−PF) × (1+PF)))     （var）
```

无功功率只返回绝对值，不能推断相位方向、感性/容性或超前/滞后。功率结果返回完整只读序列及均值、最大值、最小值；S=0 时三个功率为 0。

统计先按最大值缩放再求 NumPy 均值和标准差，避免可表示的极大非负输入因中间求和或平方而溢出。无功采用与 `1−PF²` 等价的因式分解，避免直接计算 S² 并减轻 PF 接近 1 时的消减误差。拒绝空输入、非一维、类型错误、布尔/文本/复数、负数、NaN/Infinity、越界 PF 和长度不一致。功率超出 float64 表示范围时明确失败，不返回非有限结果。

服务层复用 V0.2 Dataset、validate_frame 和 DatasetRepository；没有改变现有数据库版本 2 或表结构。模拟数据来源标记随分析结果保留。

三个分析页面从已保存数据集中选择并手动开始/重新分析，显示名称、数量、来源、统计指标及单位；功率页显示逐点序列。所有读写/计算在现有 TaskThread 中运行，GUI 模型只在主线程更新。切换数据集、刷新或开始新分析立即清空旧结果；后台任务完成时再次校验选择代次，避免过期结果回填。失败保持无结果状态并显示明确提示。主窗口关闭保护覆盖全部后台任务，原数据管理未保存预览保护保留。

## 需求算例 1 的数值更正

U=220 V、I=10 A、PF=0.9 时，P=1980 W、S=2200 VA；

`|Q| = sqrt(2200²−1980²) = sqrt(919600) = 958.957767578948 var`。

需求中的“约 958.47 var”与给定公式不一致，正确近似是 958.96 var。已在实现前明确说明；测试使用独立三角关系及数值参考，未放宽容差或修改算法来迎合错误近似。

## 实际测试结果

| 阶段 | 执行内容 | 实际结果 |
| --- | --- | --- |
| 修改前基线 | V0.2 全量 Pytest | 61 passed，26 subtests passed |
| 核心算法/服务 | test_analysis_algorithms.py、test_analysis_service.py | 69 passed |
| 首轮 GUI 与导航 | 新分析 GUI 首批用例及 test_window.py | 26 passed，21 subtests passed |
| 扩展分析 GUI | 新分析 GUI 全部用例，包含十万条数据集 | 26 passed |
| 最终完整回归 | `python -m pytest -q`，Qt offscreen | **156 passed，26 subtests passed，16.61 秒** |
| 最终原生 Windows GUI | `python -m pytest tests/test_window.py tests/test_data_ui.py tests/test_analysis_ui.py tests/test_entrypoint.py -q`，Qt windows | **44 passed，21 subtests passed，13.47 秒** |
| Python 语法 | `python -m compileall -q main.py smartpower tests` | 通过 |
| 依赖 | `python -m pip check` | No broken requirements found |
| 差异 | `git diff --check` | 通过 |

用例包含：

- 220/10/0.9 独立参考值、零电压/零电流、PF=1、PF=0；逐点功率序列及每种功率的极值/均值。
- 电压 [220,221,219] 平均 220 V 与总体标准差；电流有效值最大值；PF 采样点算术统计。
- 空数据、NaN/Infinity、非法类型、负数、PF=1.2、PF 刚超过 1、不同长度输入。
- [0,1e308] 的有限统计、最大 float64 常量、1e300/1e-300 可表示功率、不可表示功率拒绝、PF 接近 1 的高精度 Decimal 参考。
- V0.2 模拟数据 1000 条完整分析、来源标记、历史数据读取、分析前后表结构与模式版本不变。
- GUI 未选择、无历史、空数据、读取失败、数据集已删除、同一数据集重新分析失败、数据集成功切换、后台过程中选择变化、旧结果清除、单位、源标记及主窗口关闭保护。
- 实际十万条已保存数据集后台读取/分析，界面定时器持续响应；逐点模型按需取值。
- 全部原有导入、数据库、模拟数据、数据管理、导航与窗口回归测试。

原有测试文件均保留。仅更新开发版本断言，以及三个已实现页面的占位断言，改为检查真实页面和初始无结果状态；异常检测与报告页继续检查待开发提示。没有删除失败用例，也没有放宽数值容差掩盖算法问题。

## GUI 验证与未验证范围

已实际在 Windows 原生 Qt `windows` 后端显示窗口并运行 44 项自动化测试；另用真实保存的模拟数据集计算结果，抓取并查看电压、电流、功率页面及最小尺寸布局。截图始终明确标记为模拟数据，不是设备测量。

没有进行人工鼠标/原生文件选择器验收、安装包/EXE 验证、多显示器、其他 Windows 版本或其他缩放比例验证。没有以外部真实设备测量数据对照实验室仪器；本阶段检验的是指定数学模型和软件行为。

远程 GitHub Actions 结果以本次 PR 检查为准，上述结果均来自实际本地执行，不将测试计划当结果。

## 新增文件（14 个）

| 文件 | 作用 |
| --- | --- |
| `smartpower/analysis/__init__.py` | 核心分析包 |
| `smartpower/analysis/statistics.py` | 严格数值输入、总体统计、结果结构 |
| `smartpower/analysis/voltage.py` | 电压有效值统计 |
| `smartpower/analysis/current.py` | 电流有效值统计 |
| `smartpower/analysis/power_factor.py` | PF 采样点算术统计 |
| `smartpower/analysis/power.py` | 单相逐点功率与统计 |
| `smartpower/analysis/service.py` | 数据集/仓库分析服务 |
| `smartpower/ui/paths.py` | 共享现有数据库路径规则 |
| `smartpower/ui/power_series_model.py` | 逐点功率只读表格模型 |
| `smartpower/ui/pages/analysis.py` | 三个分析页面与任务编排 |
| `tests/test_analysis_algorithms.py` | 算例、非法输入及数值边界 |
| `tests/test_analysis_service.py` | V0.2 数据集/数据库集成 |
| `tests/test_analysis_ui.py` | GUI 交互、失效、竞态与响应 |
| `docs/VALIDATION_V0.3.md` | 本记录 |

## 修改文件（8 个）

`README.md`、`smartpower/config.py`、`smartpower/ui/main_window.py`、`smartpower/ui/pages/registry.py`、`smartpower/ui/pages/home.py`、`smartpower/ui/pages/data_management.py`、`tests/test_structure.py`、`tests/test_window.py`。

data_management.py 仅将原数据库路径函数提取到共享模块，并保留原导入位置可用。V0.2 导入、校验、仓库、数据库模式、依赖和 CI 工作流均未改动。

## 已知限制与后续条件

无已知的本阶段功能阻塞问题。float64 范围/精度边界会舍入，极小乘积可能下溢为 0；界面显示 12 位有效数字，算法保留完整 float64 结果。计算结果不等于设备是否合格的判据，不计算电能或时间段综合 PF，也不处理三相/非正弦模型。

在 PR 审核并合并后，可将本版本作为 V0.4 的开发基线；图表、报告、真实设备验证及更广泛平台验收仍属于后续工作。

参考：[NumPy std](https://numpy.org/doc/stable/reference/generated/numpy.std.html)、[Yokogawa 功率测量基础](https://tmi.yokogawa.com/library/resources/fundamentals/fundamentals-of-electric-power-measurements/)。
