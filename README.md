# 智电析电力系统运行数据分析与可视化软件 V1.0

Windows 桌面软件，开发版本 **V0.9.0 综合测试与稳定性优化**。按本次确认使用 64 位 Python 3.13。
产品正式名称中的 V1.0 与开发版本分别管理。V0.1 的八个页面、导航、首页入口和原生窗口操作均保留。


## V0.9 质量优化

保留 V0.1～V0.5 八页导航、数据管理、统计分析、异常检测、曲线、PDF/Excel 和设置功能。本版修复相邻浮点采样标准差精度、非零功率下溢被当作零、设置文件读取权限错误及模拟 CSV 未经确认覆盖问题；不新增测量数据或分析模型。

- 总体标准差仍为 `sqrt(mean((x-mean(x))²))`，`ddof=0`。实现先减最小值再按极差归一化，以保留相邻 float64 差值并避免平方溢出。
- 非零功率结果舍入成零时明确报错；真实零输入、PF=0/1 的零分量仍有效。单相正弦稳态公式、单位和无功绝对值含义不变。
- 模拟 CSV 导出默认拒绝覆盖，界面只确认一次，CLI 需 `--overwrite`；并发出现同名文件时也不会静默覆盖。Python API 若确认覆盖需 `export_demo(dataset, path, overwrite=True)`。
- 核心业务离线 socket 禁用测试、隔离数据库异常终止恢复、原生 Windows Qt 与缩放测试、完整导出核验已加入质量验证。全新 Python 3.13 虚拟环境实际安装并验证。
- 大量异常的完整 PDF 可能耗时并占用较多内存；不会截断事件，当前没有取消功能。十万条模拟数据的完整 PDF 有 1,285 页；请按机器容量选择数据量，逐条筛选可用 Excel。

详细实测、三轮性能数据与限制见 [V0.9 验证记录](docs/VALIDATION_V0.9.md)、[发布准备清单](docs/RELEASE_READINESS.md)。V0.9 是发布前质量版本，尚未完成 EXE、Windows 10、真实系统 DPI 切换、多机器阅读器及最新漏洞数据库审计。

本机普通 Windows 路径超过 260 字符受系统策略限制，扩展路径 `\\?\` 模式已实测；普通长路径尚不保证。目录不可写或被占用时应更换路径，已有文件保持不变。

## 安装与运行

在 Windows PowerShell 执行，推荐较短的目录，避免 Windows 路径长度限制：

```powershell
git clone https://github.com/sunyiyang299-cell/SmartPowerAnalyzer.git
cd SmartPowerAnalyzer
git switch feature/v0.9-quality-hardening
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

如果没有 Python Launcher，可用指向 Python 3.13 的 `python` 替代 `py -3.13`。
直接调用虚拟环境的 Python，无需修改 PowerShell 执行策略。当前提供源码运行，尚无 `.exe` 安装包。
运行依赖为 PySide6、Pandas、NumPy、PyQtGraph、openpyxl 和 ReportLab；SQLite 是 Python 标准库。ReportLab 的 Pillow、charset-normalizer 依赖由 pip 安装。PDF 检查库 pypdf 仅用于开发测试。

## V0.5 专业报告与系统设置

保留 V0.1～V0.4 的全部数据管理、分析、图表和异常检测功能。报告完全离线生成，不使用在线报告服务，不修改 SQLite 模式或原始采样值。

### 生成报告

1. 在数据管理保存数据集。
2. 进入“分析报告”，点击“刷新数据集”，选择数据集，核对名称、来源和已保存记录数。
3. 填写报告标题。默认不执行异常检测；需要时勾选“在本次报告中执行用户阈值检测”，填写电压下限/上限 V、电流上限 A。
4. 点击“生成 PDF 报告”或“生成 Excel 报告”，选择已有目录及正确扩展名。覆盖已有文件必须确认，默认不覆盖。
5. 等待后台生成。完成后显示实际保存路径及本次报告的数据集来源；错误信息会明确显示。

报告生成读取一次仓库数据，校验后形成不可变 `ReportSnapshot`：唯一标识、软件名称/版本、数据集 ID/名称/来源、采样数、最早/最晚时间、带 UTC 时区的生成时间、全部统计、逐点功率、原始时间/数值、阈值和完整事件。
统计与功率复用 V0.3，检测复用 V0.4，曲线使用 V0.4 同一份排序视图与原始索引映射。数组以不可写 bytes 缓冲区固定，不从已有界面截图取图，不受其他页面选择影响。

文件对话框期间配置或选择改变会取消本次导出；任务启动后固定数据集 ID、标题、阈值和字体配置。用户通过程序改动配置，或在设置页保存新偏好时，已启动任务仍按原快照完成，并明确提示该文件对应启动时数据集；不把旧报告状态当成当前选择结果。
导出采用同目录临时文件，写完后原子改名/替换；缺少目录不会自动创建，失败不替换旧目标。目标已被其它程序占用时请关闭占用程序后重试。

### PDF 内容与字体

A4 中文技术报告包括封面、数据概况、电压统计/曲线、电流统计/曲线、P/S/|Q|及功率因数统计/曲线、检测状态与阈值、全部异常明细、说明与限制，附页码与来源页脚。跨页表格重复表头；曲线是从本次快照生成的矢量图，可保留缩放清晰度。
每曲线最多约1800个极值代表点，仅减少绘图点数；统计、事件及原始数据不抽稀。时间排序稳定，重复时间保留，横轴显示实际日期时间；原始时间和数值仍保留在快照/Excel。

默认使用 ReportLab 的标准 PDF 中文字体 **STSong-Light 引用**，不依赖某个 Windows 字体路径，不向仓库提交字体文件。它不嵌入字体，PDF 阅读器须支持中文/亚洲字体包；离线跨电脑分发时，建议配置可嵌入中文 TrueType 字体：

1. 合法取得包含报告字符、允许嵌入的中文 `.ttf` 或 TrueType `.ttc` 字体；TTC 使用首个字面，CFF/OpenType `.otf` 不支持。
2. 系统设置 → PDF 中文字体 → 选择字体 → 保存设置。
3. 重新生成 PDF。导出器检查文件、字体格式和报告所需字形；缺失/无效/缺字会明确拒绝，不生成缺字报告。
4. 清空字体路径并保存可恢复标准引用。字体仅在本地使用，不上传，不自动下载安装字体。

标准引用对非 BMP 字符（例如部分 emoji/生僻字）明确拒绝，需选择覆盖这些字符的 TrueType 字体。嵌入模式使用字体默认实例；用户须自行核对其许可。开发验证曾使用 [Noto CJK 官方字体](https://github.com/notofonts/noto-cjk/tree/main/Sans/Variable/TTF/Subset) 及其 [SIL OFL 1.1 许可](https://github.com/notofonts/noto-cjk/blob/main/Sans/LICENSE)，实际检查生成 PDF 的 FontFile2 嵌入流；该字体不随项目分发。
ReportLab 开源工具采用 [BSD 许可](https://docs.reportlab.com/developerfaqs/)，字体引用/嵌入方式见 [官方字体说明](https://docs.reportlab.com/reportlab/userguide/ch3_fonts/)。本阶段尚未制作 EXE，后续打包需附带所有实际依赖及字体适用的许可和资源，不能只复制程序代码。

### Excel 内容与限制

真实 `.xlsx` 包含“报告概况、电压分析、电流分析、功率分析、异常检测、原始数据”六个工作表。统计值为数值单元格；时间为 Excel 原生日期，另有“精确时间文本”保留原始纳秒精度。各采样表按原始保存顺序完整导出，含中文表头、单位、样式、列宽、冻结和筛选。
写入采用 openpyxl 流式工作簿；数据集名称、标题等文本强制写为文本单元格，即使以 `= + - @` 开头也不生成公式。
每表上限 1,048,576 行（含统计区/表头）；任何数据表或事件表超限均拒绝整个导出，不静默截断。功率表预留16行，因此单次原始采样上限为1,048,560行，异常表另受事件行数限制。Excel 日期接受1900～9999年，超出则拒绝；PDF不受该日期约束。Excel 原生日期/数值有自身精度限制，精确时间文本可追溯；不承诺 Excel 具备任意高精度数值能力。

未执行异常检测会明确写“本次未执行异常检测”，不会写成零异常；执行后无事件才写“未检测到符合当前阈值条件的异常记录”。事件总数和唯一异常采样点分别统计。用户阈值不是国家标准限值，不代表设备合格。
模拟来源从元数据传到封面、概况、曲线、页脚及 Excel 原始数据：“模拟数据，非真实设备测量”。导入文件仅表示来源未核验，不证明设备测量真实性。

### 系统设置

可保存默认报告目录、默认图表目录、默认报告标题、启动页面及 PDF 字体。导出目录必须为已有绝对目录，程序不会静默创建它们。
点击“保存设置”写入 Qt 用户配置目录下的版本化 JSON（界面显示实际路径），同目录临时文件写完后原子替换。仅这个专用配置目录会在用户明确保存/确认恢复时创建。设置不写入源码或安装目录，不保存密码，不改变 `SMARTPOWER_DB_PATH` 及 SQLite 默认路径规则。
默认目录为用户文档目录；该目录不存在时使用用户主目录。默认图表目录用于 PNG 保存对话框，报告默认目录用于 PDF/XLSX。已保存设置重启读取；启动页面在重启后生效，其它默认值用于后续导出。恢复默认设置必须确认，确认后保存默认值，取消不改设置。
损坏、版本不兼容或失效路径会提示并暂用默认设置，保留原文件；只有用户明确保存才替换。报告中心遇到失效设置会要求先到系统设置确认保存，避免缺失字体被无提示换成标准引用。测试/便携配置可设置 `SMARTPOWER_SETTINGS_PATH` 指向独立 JSON，不影响数据库环境变量。

### V0.5 测试与范围

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests/test_reporting.py tests/test_settings.py tests/test_reports_settings_ui.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q main.py smartpower tests
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

Windows 原生 GUI 复验：设置 `$env:QT_QPA_PLATFORM = "windows"`，运行 `tests/test_reports_settings_ui.py` 以及所有历史 GUI 测试。实际结果、样例文件验证和未验证范围见 [V0.5 验证记录](docs/VALIDATION_V0.5.md)。
只支持单相正弦稳态交流模型；无功为绝对值，PF平均为采样算术平均，不作时间加权。报告不构成设备安全或标准符合性认证，不代替计量仪器校准，模拟数据不是测量证据。
报告及事件快照仍在内存中，PDF全部异常明细可能产生大量页面；后台任务保持界面可用，但不承诺无限数据量或任意文件规模。尚未进行用户人工验收、真实设备验证或 EXE 打包。

新增 `reporting/`、`settings/` 及 `ui/pages/reports.py`；核心报告/设置逻辑与 GUI 分离，无新增数据库表。新增运行依赖 ReportLab，复用 openpyxl；pypdf 仅开发测试使用。

## V0.4 曲线可视化与异常检测

保留 V0.1～V0.3 的八页导航、导入、校验、SQLite、排序筛选和统计分析。正式产品名称仍为 V1.0，开发版本为 0.4.0。

1. 数据管理中导入并保存数据，或生成并保存明确标记的模拟数据。
2. 进入电压、电流或功率分析，刷新、选择已保存数据集，点击“开始分析”。
3. 曲线横轴为本地无时区采样时间，支持滚轮缩放、左键拖动平移和“恢复完整视图”；悬停显示原始索引、完整时间及 12 位有效数字的数值。
4. 电压为有效值 V、电流为有效值 A，不是交流瞬时波形。功率复用 V0.3：P（W）、S（VA）、无功绝对值 |Q|（var）；共享数值轴但分别标明单位，勾选框可单独显隐。
5. 进入异常检测，刷新并选择同一数据集；填写电压下限、电压上限、电流上限，明确勾选启用，再点击“开始检测”。演示预设 210 V / 230 V / 20 A **不是国家标准或设备合格判据**，不会自动启用检测。
6. 查看事件总数、唯一异常采样点数、各类型次数和明细，可按类型筛选。电压/电流图中显示匹配数据集和数据内容的异常标记，点击或悬停标记查看时间、原始索引、采样值和触发阈值；支持隐藏标记。
7. 修改阈值、启用状态或检测数据集立即清除旧结果与联动标记。后台检测期间改动配置会丢弃过期结果，须重新检测。分析页面切换数据集会清空图表，读取或计算失败不保留旧结果。
8. 点击“导出 PNG”选择中文路径。图像包含标题、名称、采样数、时间轴、单位、图例、来源和当前视图；模拟图像明确显示“模拟数据，非真实设备测量”。导出当前缩放、显隐状态；如需全图，先恢复完整视图。已有文件必须确认覆盖，默认不覆盖。

### 阈值规则与统计口径

- 电压 `< 下限`：电压偏低；电压 `> 上限`：电压偏高；电流 `> 上限`：电流偏高。
- **等于阈值不计异常**。阈值须为有限非负数，电压下限小于上限，电流上限大于 0。空值、NaN、Infinity、负数及无效配置明确拒绝，不静默修正输入。
- 一行电压与电流同时越限计两个事件；唯一采样点数按原始行去重。原始记录索引从 0 起，对应 SQLite 保存顺序，与排序后的时间位置区分。
- 事件保留数据集标识、原始行、时间、参数、采样值、类型、阈值、单位和来源。没有符合条件的记录时仅提示“未检测到符合当前阈值条件的异常记录。”

**异常检测结果仅供数据分析参考，不构成设备安全或电气标准符合性认证。**

### 时间、性能与导出边界

绘图采用稳定时间排序视图：非等间隔、跨日期和乱序时间按实际时间排列；重复时间戳全部保留，按原始先后连接，因此可能出现竖直线段。重复时刻悬停按纵向距离选择对应原始行；功率页以 P 曲线选取同一原始行，并显示全部功率值。原始数据、数据库顺序和逐点功率表不改变。
内部相对秒坐标避免现代日期的绝对 epoch 浮点误差；时间标签显示日期和秒（亚秒视区显示毫秒），精确原始时间在读数/明细中显示。跨度很大时浮点坐标仍有分辨率限制，不改变原始时间。

读取、校验、排序准备、统计及完整数据异常检测使用后台 TaskThread。PyQtGraph 启用可视区裁剪和 peak 自动降采样，使用一像素曲线和 NumPy 数组；仅渲染减少点数，统计、异常明细和存储使用完整数据。
每类异常在当前视区最多显示 1500 个均匀选取的代表标记；缩放后重新选择，**代表标记不等于全部异常**，准确数量和完整事件见异常明细。每类仅一个 ScatterPlotItem，不创建十万个独立图形对象。
十万条采样已进行实际测试，结果见 [V0.4 验证记录](docs/VALIDATION_V0.4.md)；性能受内存、硬件和数据分布影响。当前为内存加载，无流式分页或实时采集，不承诺无限数据量。

异常联动同时核对保存数据集 ID、名称、来源和完整采样内容 SHA-256 指纹。检测配置变化会使结果失效。PNG 文件选择和覆盖对话框返回后再次核对图表修订号；数据集改变即取消导出。GUI 线程先抓取一致快照，再写同目录临时 PNG，完成后原子改名/替换，失败保留旧文件。图像导出是当前图表截图，包含操作栏；不替代原始 CSV 数据导出或正式报告。

新增模块：`anomaly/{models,detector,service}.py`（不依赖 Qt），`visualization/{snapshot,time_axis,plot_widget,export}.py`，`ui/anomaly_model.py`，`ui/pages/anomaly.py`。数据库模式仍为 2，无新运行依赖。

新增专项测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_anomaly.py tests/test_anomaly_ui.py tests/test_visualization.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q main.py smartpower tests
.\.venv\Scripts\python.exe -m pip check
```

Windows 原生复验时将 `QT_QPA_PLATFORM` 设置为 `windows`，运行上述 GUI 测试及原有 GUI 回归。自动化事件、原生窗口截图检查与最终用户人工验收的区别见验证记录。

## V0.3 电气参数分析

保留全部 V0.1 桌面导航和 V0.2 数据管理能力，新增电压、电流及功率分析页面。

1. 在“数据管理”导入并校验文件，或生成明确标记的模拟数据，然后手动保存数据集。
2. 进入“电压分析”“电流分析”或“功率分析”，点击“刷新数据集”。
3. 选择已保存的数据集，点击“开始分析”。显示名称、采样数、数据来源及带单位的结果。
4. 再次点击“开始分析”会重新读取并计算。切换选择或开始新任务立即清空旧结果；失败时不显示容易误认为新结果的旧值。
5. 功率页同时显示逐采样点 P、S、|Q| 序列及功率因数统计；表格与页面均可滚动。

列表读取、数据库读取、校验和计算均在后台线程执行。未选择、数据为空、已删除、损坏或数值无法计算时给出提示。后台任务期间保留导航能力，关闭窗口会提示等待，避免销毁仍运行的线程。
所有结果来自本次读取的已保存数据快照；数据变化后请手动刷新、重新分析。

### 统计公式与单位

对 N 个等权采样点 x₁…xₙ：

```text
算术平均值 μ = Σxᵢ / N
总体标准差 σ = sqrt(Σ(xᵢ − μ)² / N)    （ddof = 0）
最大值 = max(xᵢ)，最小值 = min(xᵢ)，采样数量 = N
```

电压与电流输入均为有效值（RMS）。电压各统计量单位 V，电流各统计量单位 A，采样数量单位“条”。
**电流有效值最大值是各采样记录的最大值，不是交流瞬时峰值。**
功率因数统计为无量纲，显示采样点算术平均值、最大值、最小值及总体标准差。
采样点 PF 算术平均值不等于整个时间段的综合功率因数；本版本没有以功率或能量积分定义综合功率因数。
统计不作时间间隔加权，不推断设备是否合格或是否越限。

### 单相功率公式

适用前提：单相、正弦、稳态交流；U 为电压有效值（V）、I 为电流有效值（A）、PF 为非负功率因数（0～1）。对每个采样点：

```text
S = U × I                                      单位 VA
P = U × I × PF = S × PF                        单位 W
|Q| = sqrt(S² − P²)
    = S × sqrt(max(0, (1 − PF) × (1 + PF)))     单位 var
```

最后一种形式与 `S × sqrt(max(0, 1 − PF²))` 等价，避免直接平方极大 S，且减轻 PF 接近 1 时的消减误差。
当 S=0 时三个功率结果均为 0。每种功率返回完整逐点序列及算术平均、最大、最小值。
无功功率结果始终是**绝对值**，不能据此判断感性/容性、超前/滞后或能量流向。
本版本不适用于三相、非正弦、谐波功率分解，不计算电能、时间段综合 PF 或报告结论。

| 示例 U / I / PF | P（W） | S（VA） | 无功功率绝对值（var） |
| --- | --- | --- | --- |
| 220 / 10 / 0.9 | 1980 | 2200 | 958.9577676 |
| 0 / 10 / 0.9 | 0 | 0 | 0 |
| 220 / 10 / 1 | 2200 | 2200 | 0 |
| 220 / 10 / 0 | 0 | 2200 | 2200 |

需求测试 1 的“约 958.47 var”与其给定公式不符：`sqrt(2200²−1980²)=sqrt(919600)=958.9577676 var`，应约为 958.96 var。实现和测试均以公式及独立计算参考值为准，没有放宽容差去接受错误近似值。

### 数值与模块约定

核心计算不依赖 Qt；`smartpower/analysis/` 中的 voltage、current、power_factor 和 power 模块可独立调用，返回结构化结果。service 复用 V0.2 Dataset、validate_frame 和 DatasetRepository，不改动 SQLite 版本 2 的表结构，不自动保存或覆盖分析结果。
独立算法接口要求非空的一维真实数值序列，拒绝文本、布尔值、复数、负数、NaN、Infinity、长度不匹配以及越界 PF；文件导入的数字文本仍由 V0.2 校验层正常解析。
使用 NumPy float64，统计先缩放后计算均值与 `np.std(..., ddof=0)`，避免极大输入的求和或平方中间溢出。功率结果超出 float64 可表示范围会明确失败，不能把 Infinity 当正常结果。
在 float64 精度和范围边界仍可能发生舍入或极小值下溢为 0；界面按 12 位有效数字展示，算法返回完整 float64 值，不用于替代计量仪器校准或高精度测量认证。

示例（项目根目录内）：

```python
from smartpower.analysis.voltage import analyze_voltage
from smartpower.analysis.power import analyze_power

stats = analyze_voltage([220, 221, 219])
power = analyze_power([220], [10], [0.9])
print(stats.mean, stats.unit)
print(power.active, power.apparent, power.reactive_abs)
```

公式与统计定义参考：[NumPy 总体标准差](https://numpy.org/doc/stable/reference/generated/numpy.std.html)、[Yokogawa 功率测量基础](https://tmi.yokogawa.com/library/resources/fundamentals/fundamentals-of-electric-power-measurements/)。

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
.\.venv\Scripts\python.exe -m pytest tests/test_analysis_algorithms.py tests/test_analysis_service.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_analysis_ui.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

GUI 测试默认 `offscreen`。Windows 原生后端复验（会短暂显示窗口）：

```powershell
$env:QT_QPA_PLATFORM = "windows"
.\.venv\Scripts\python.exe -m pytest tests/test_window.py tests/test_data_ui.py tests/test_analysis_ui.py tests/test_entrypoint.py -q
Remove-Item Env:QT_QPA_PLATFORM
```

CI 在 Windows/Python 3.13 下运行 Pytest。测试涵盖 CSV/Excel、中文路径、字段和数值校验、事务回滚、读写删除、模拟数据标记、原子导出、模型排序筛选、十万条后台导入响应及窗口保护。
V0.3 实际执行结果及文件清单见 [V0.3 验证记录](docs/VALIDATION_V0.3.md)。[V0.2](docs/VALIDATION_V0.2.md) 和 V0.1 记录保留作历史参考。
沙箱环境如不能访问默认临时目录，可将 `TEMP`、`TMP` 和 Pytest 的 `--basetemp` 指向有写入权限的工作目录；不要通过跳过失败测试规避问题。

## 模块结构与扩展

```text
main.py                         桌面入口
smartpower/
  application.py                Qt 初始化、中文翻译、事件循环
  config.py                     正式名称、开发版本
  analysis/
    statistics.py               严格输入检查、缩放统计、结构化结果
    voltage.py / current.py     电压、电流有效值统计
    power_factor.py / power.py  PF 统计及单相逐点功率
    service.py                  复用数据对象、校验和仓库的分析服务
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
    pages/analysis.py           三个分析页面及结果生命周期
    power_series_model.py       功率序列按需展示
    paths.py                    共享数据库路径
    pages/registry.py           八个页面注册表
    pages/{base,home,features,settings}.py
    theme.py / widgets.py       共用浅色样式和控件
tests/                          V0.1/V0.2 回归及 V0.3 算法、服务、GUI 测试
requirements.txt                运行依赖
requirements-dev.txt            测试依赖
.github/workflows/tests.yml     Windows CI
```

数据处理和数据库模块不依赖 Qt。界面通过后台任务调用它们，模型更新仅在 GUI 线程执行；新增分析算法仍应放在独立服务中。
异常检测页支持用户阈值，报告页支持离线 PDF / Excel，系统设置可持久化。分析页仅展示实际计算结果，模拟数据保留模拟标记。

接口参考：[Pandas read_excel](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html)、[Qt 表格模型](https://doc.qt.io/qtforpython-6.6/PySide6/QtCore/QAbstractTableModel.html)、[Qt QThread](https://doc.qt.io/qtforpython-6.10/PySide6/QtCore/QThread.html)。
