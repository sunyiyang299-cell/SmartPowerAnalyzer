# V0.5.0 专业分析报告与系统设置验证记录

本记录对应《智电析电力系统运行数据分析与可视化软件 V1.0》开发版本0.5.0。所有报告样例使用标记为模拟的数据，不是设备测量证据。

## 开发基线与环境

- 最新main基线 `ffd15afd5b2a8a2faa535687ce88e33d363a460f`；编码前确认V0.4 PR #4已合并。新分支 `feature/v0.5-reports-settings`。
- 编码前阅读README、依赖、页面注册、Dataset/SQLite仓库、V0.3分析、V0.4检测/快照、TaskThread、设置页、现有测试和Windows CI；先执行基线：228 passed，25 subtests passed。
- Windows 11 build26200、64位CPython3.13.0、Qt/PySide6 6.10.3、SQLite3.45.3。沿用NumPy2.5.4、Pandas3.0.6、PyQtGraph0.14.0、openpyxl3.1.5。
- 新增运行依赖ReportLab5.0.1，pip自动安装其Pillow/charset-normalizer依赖。本机分别为13.0.0/3.5.2。开发测试新增pypdf6.21.1、沿用Pytest9.1.1。
- PDFium/pypdfium2 5.14.0仅用于本机渲染QA，不加入运行或CI依赖。未引入在线报告生成服务。
- 测试机器系统标识：AMD64 Family25 Model97 Stepping2（AuthenticAMD）、32逻辑处理器、15.69 GiB系统可见内存；测量不承诺其它机器性能。

## 实现功能

1. 报告中心：八页导航保留，读取保存数据集，展示名称/来源/数量，编辑标题和可选异常阈值，离线PDF/XLSX导出，忙碌、错误及完成路径提示。
2. ReportSnapshot：唯一报告ID、正式名称/版本、完整数据集标识/来源、采样数量、最早/最晚采样时间、UTC生成时间、统计/逐点功率/PF、完整阈值/事件和计算模型。
3. PDF：封面、概况、电压/电流/功率/PF、三类矢量时间曲线、完整异常明细、限制、页码、跨页重复表头及来源页脚。
4. Excel：六类工作表，统计和时间/数值类型，完整原始顺序，完整事件，中文样式/列宽/行高/冻结/筛选；文本强制非公式；行数与日期范围预检。
5. 设置：默认报告目录、图表目录、报告标题、启动页面、可选PDF字体；版本化用户JSON，保存/重启读取/确认恢复/损坏回退/原子写入。
6. 报告与设置逻辑不依赖GUI。任务沿用TaskThread，后台不访问控件；关闭忙碌窗口有原有保护。

## 新增文件（16）

- `smartpower/reporting/__init__.py`
- `smartpower/reporting/chart_renderer.py`
- `smartpower/reporting/excel_exporter.py`
- `smartpower/reporting/files.py`
- `smartpower/reporting/fonts.py`
- `smartpower/reporting/models.py`
- `smartpower/reporting/pdf_exporter.py`
- `smartpower/reporting/service.py`
- `smartpower/settings/__init__.py`
- `smartpower/settings/manager.py`
- `smartpower/settings/models.py`
- `smartpower/ui/pages/reports.py`
- `tests/test_reporting.py`
- `tests/test_reports_settings_ui.py`
- `tests/test_settings.py`
- `docs/VALIDATION_V0.5.md`

## 修改文件（13）

- `README.md`
- `requirements-dev.txt`
- `requirements.txt`
- `smartpower/config.py`
- `smartpower/ui/main_window.py`
- `smartpower/ui/pages/home.py`
- `smartpower/ui/pages/registry.py`
- `smartpower/ui/pages/settings.py`
- `smartpower/ui/paths.py`
- `smartpower/visualization/plot_widget.py`
- `tests/conftest.py`
- `tests/test_structure.py`
- `tests/test_window.py`

未删除任何历史测试方法；版本断言更新0.5.0，报告占位断言改为真实报告页类型、默认未检测、空快照、两个导出按钮可用的更严格检查。原报告“待开发”子测试不再适用，故历史子测试计数由25变24，主测试方法保留。测试新增隔离用户设置fixture，避免读写开发者真实偏好。

## 快照与一致性

仓库只读取一次，复用V0.2校验；V0.3 `analyze_dataset`计算统计和功率；V0.4 `detect_anomalies`执行可选完整检测，V0.4 PlotSamples用于排序时间映射和原数值。没有重复电气公式。
所有NumPy样本/逐点功率复制为bytes后备只读缓冲区，不能重新设为可写；报告元数据、统计、阈值、事件采用不可变对象。报告不持有可变DataFrame或GUI截图。起止时间是全记录min/max，原始保存顺序不改变。
导出前捕获数据集ID、标题、阈值、设置和字体；文件对话框中变化会取消。任务启动后若选择/配置变化，文件仍由启动时快照生成，完成提示明确说明旧快照且不保存为当前选择的报告状态。更换系统偏好也使当前报告状态失效。原始SQLite内容与模式有前后比较测试，未改表。

## PDF 实现与中文许可

ReportLab Platypus、A4、CJK段落、LongTable、重复表头与页脚。用户文本使用XML转义，正文/图表/数值来自相同快照。图表为reportlab Drawing矢量路径，使用真实采样时间和V0.3功率数组；每条曲线最多约1800个按桶保留极值的代表点，仅影响渲染，不改变统计或全部异常事件。

默认字体使用标准PDF `STSong-Light` UnicodeCIDFont引用，不查找未知系统字体路径、不附带字体文件。引用模式未嵌入字形，阅读器需支持中文/亚洲字体包；对非BMP字符明确拒绝并提示配置字体，不生成缺字报告。
可选用户指定TrueType .ttf/.ttc，TTC使用首个字面，注册后核对所需字符覆盖；缺文件、格式错误或缺字明确失败。失效设置要求先到设置页确认保存，避免悄悄改成引用模式。

[ReportLab开源许可说明](https://docs.reportlab.com/developerfaqs/)为BSD，支持本项目离线应用。没有使用商业rlextra或pyRXP。中文引用方式依据[官方字体说明](https://docs.reportlab.com/reportlab/userguide/ch3_fonts/)。
本机另下载[Noto官方简体中文TrueType](https://github.com/notofonts/noto-cjk/tree/main/Sans/Variable/TTF/Subset)用于嵌入验证，遵循[SIL OFL1.1](https://github.com/notofonts/noto-cjk/blob/main/Sans/LICENSE)；样例实际嵌入NotoSansSC默认Thin实例的子集，PDF中检查到FontFile2流。字体文件只留在本机QA目录，未提交GitHub。用户配置其它字体仍须核对其许可。EXE打包尚未进行，未来需包含真实依赖/字体资源及相应许可。

## PDF 实际文件验证

- Windows原生窗口用1000条固定种子模拟数据、210/230V及20A用户演示阈值，实际生成32页PDF。模拟事件717次、唯一异常采样613条，不是设备结论。
- 标准字体引用样例、另一个嵌入Noto中文字体样例均是真实PDF；检查文件头、A4页数、元数据、正式名称、来源、数据集、数值、三类曲线、全部事件、页码和重复表头。
- pypdf执行文本/对象检查；PDFium将两类样例共64页渲染为PNG，检查全页缩略图及封面/三类分析/异常分页/限制页细节，未见重叠、丢表头或拉伸图像。曲线是矢量路径，不是假占位图。
- Poppler工具曾在本机中文安装路径下无法读取CMap/语言资源，故未将其失败输出当作合格渲染；改用PDFium检查。这个问题属于本机QA工具路径，不是未处理的报告生成失败。
- 未进行多种实际阅读器、无中文资源机器的人工兼容测试。标准引用的可移植性限制明确告知；嵌入模式经结构与渲染检查。

## Excel 实际文件验证

- 真正ZIP/OpenXML .xlsx，openpyxl重新打开六表：报告概况、电压分析、电流分析、功率分析、异常检测、原始数据。
- 1000条原始数据全部存在，保存顺序与原采样一致，717事件完整，模拟来源保留；统计/PF/P/S/|Q|与算法逐项比较。
- 原生日期列可排序筛选；另存精确时间文本以保留纳秒。测试乱序纳秒时间与日期/数值类型。日期1900～9999外明确拒绝，不静默更改。
- 文本单元格强制`s`，测试`=1+1`、`+cmd`、`-1+2`、`@SUM(...)`和XML样式文本；工作簿中没有公式单元格。
- 每表1,048,576行上限含统计区/表头；任何采样或事件超限拒绝。行数分支通过临时缩小上限测试，未声称实际导出了百万行；不截断数据。
- 没有启动Microsoft Excel/LibreOffice进行人工打开验收，不能将openpyxl重开等同于所有办公软件兼容认证。

## 文件安全与设置

PDF/XLSX使用相同目录临时文件，完成后原子替换；默认拒绝覆盖，GUI确认默认“否”。缺目录、扩展名错误、占用/写入失败会提示并保留旧目标；没有修改采样数据库。测试模拟失败并比较原文件字节。
JSON在Qt用户配置目录，页面显示路径。仅明确保存/确认恢复才创建专用设置目录；报告/图表目标目录必须已存在，不自动创建。保存使用fsync与os.replace。坏JSON、过大文件、未知版本/类型、失效路径均提示回退，保留原文件。默认目录为文档目录，不存在时主目录；启动页重启生效，其余默认值用于后续导出。
用真实Windows窗口保存设置、重新创建主窗口，以及单独启动新的Python/Qt进程，确认报告标题/目录和启动报告页重读成功。没有写入项目源码、安装目录或用户数据库，也不保存敏感字段。

## Windows GUI 实际验证

真实PySide6 windows后端运行报告中心和系统设置，以1000条明确标记模拟数据导出PDF/XLSX。生成四张真实窗口截图（两页大窗口及900×620最小窗口），检查八页导航、滚动与控件布局。
最终长路径布局问题已修复：设置文件路径采用WrapAnywhere的只读文本框，保留原最小宽度断言，未降低测试要求。批量导出测试用Qt事件循环等待任务；期间保持导航与关闭保护，后台没有操作控件。

实际1000条原生UI任务测量（一次运行，不承诺跨硬件性能）：

| 格式 | 从按钮启动到任务完成 | 5ms定时器次数 | 最大相邻间隔 |
| --- | --- | --- | --- |
| PDF标准引用 | 0.4344秒 | 72 | 47.21ms |
| XLSX完整报告 | 0.8581秒 | 171 | 8.77ms |

字体嵌入和报告分页/表格处理仍可能受字体体积、记录数与硬件影响，所有生成在后台。界面少量同步路径/JSON检查不等同于无限规模无延迟保证。

## 自动化与检查结果

最终完整回归：**287 passed，24 subtests passed，31.71秒**，无失败或跳过。新增59项Pytest参数化测试；包含报告与旧算法一致、来源/快照/数据库未改、未执行/零事件区分、PDF有效性/中文/图表/分页/文件保护、XLSX六表/完整顺序/类型/公式防护/容量、设置保存/新实例读取/恢复/损坏和GUI切换/配置竞争/错误/响应/导航/关闭保护。
Python compileall与pip check已执行成功；Git差异检查在提交前执行，提交版本无空白错误。最终Windows原生GUI回归：**109 passed，19 subtests passed，28.68秒**，无失败或跳过。远程CI在PR中核验，交付报告记录实际结果，不把计划当结果。

## 未验证范围与已知限制

没有已知未修复的算法/自动化失败。尚未进行最终用户人工点击验收、原生文件对话框人工交互、多显示器/各种DPI/阅读器、真实设备测量、长时间稳定性、完整百万行文件、Windows安装包或EXE验证。对话框/覆盖确认分支通过测试替身严格断言；真实UI控件、线程、文件生成和截图已实际运行。
报告及事件快照仍在内存中；PDF异常明细全量输出可能产生很多页，不能承诺任意文件规模。Excel原生数值约15位有效数字，纳秒时间由附加文本追溯。标准字体引用依赖阅读器中文支持；配置字体缺字会拒绝，而非伪造结果。

## V0.9 准备结论

具备进入V0.9综合测试的功能和自动化基础。仍需先审核本PR，并在V0.9执行人工验收、跨机器/阅读器、真实来源数据、长期与边界规模测试，为V1.0 EXE打包和软著材料收集证据。没有将未执行项目描述为已通过，没有把模拟数据当测量证据。
