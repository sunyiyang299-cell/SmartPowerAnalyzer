# V0.9.0 综合验证记录

验证日期：2026-10-20。只使用明确标记的模拟数据和隔离临时目录。正式软件名称保持《智电析电力系统运行数据分析与可视化软件 V1.0》。本文的 PASS 只代表所列环境及断言范围，不代表所有 Windows、阅读器或设备均已通过。

## 开发基线与环境

- 最新 main：`c0c1f18f56bc474c2113f7c2caf4839465bf024c`，GitHub 已核实 PR #1～#5 均 Merged。
- 分支：`feature/v0.9-quality-hardening`。创建时工作树干净，未覆盖已有开发工作。
- Windows 11 build 26200，AMD64 Family 25 Model 97 Stepping 2，非管理员运行（IsUserAnAdmin=False）。未获得可靠的内存总量信息。
- Python 3.13.0 64 位；全新独立 venv 从 requirements-dev.txt 安装成功。运行依赖版本保持 PySide6 6.10.3、pandas 3.0.6、NumPy 2.5.4、PyQtGraph 0.14.0、openpyxl 3.1.5、ReportLab 5.0.1；测试 pytest 9.1.1、pypdf 6.21.1。
- PDF 另用 QA 环境 pypdfium2 5.14.0 渲染，不增加应用依赖。不上传字体、数据库、报告或用户数据。

## 问题登记

共 5 项：P0 3 项、P1 1 项、P2 1 项。已修复 4 项；P2 已增加提示但资源问题仍保留为限制。没有已知未修复 P0/P1；这不等于完成安全认证。

| ID | 级别 | 复现及原因 | 处理 / 对应测试 | 状态 |
|---|---|---|---|---|
| Q01 | P0 | `summarize([1e16,1e16+2])` 标准差约 1.110223，应为 1；按最大值先除导致相邻差值丢失 | 先减最小值再按极差归一化；Decimal 400 位独立参考检验常规、相邻大数、1e308、次正规数 | PASS，修复 |
| Q02 | P0 | U=I=1e-200 的非零 S 被下溢输出为 0；P、无功也可下溢 | 对正数输入产生零的 S/P/无功分量明确拒绝；三类下溢回归及旧零值、PF 端点用例 | PASS，修复 |
| Q03 | P0 | `export_demo` 默认 os.replace，可未经确认覆盖现有文件；CLI 存在检查到写入的竞态 | 默认独占发布，覆盖仅显式允许；GUI 单次确认、取消保留原文件、并发目标保护、原替换失败回归均保留 | PASS，修复 |
| Q04 | P1 | Path.exists 抛 PermissionError 时 SettingsManager.load 未捕获，可阻断启动 | 存在性检查移到错误处理内，默认设置附中文警告，原文件不写入 | PASS，修复 |
| Q05 | P2 | 十万条、37077 个完整事件 PDF 有 1285 页，实测峰值工作集约 853 MiB，单轮约 55～58 秒；缺少容量说明 | 报告页和 README 增加时间/内存/无取消说明，保留完整记录并建议 Excel 筛选 | FAIL，已缓解，内存与取消机制待优化 |

修复前定向回归：统计/权限/覆盖 5 failed、1 passed；功率下溢 3 failed。修复后对应回归通过。旧 `test_export_failure_preserves_existing_file` 仅增加 `overwrite=True`，以新显式授权 API 继续测试原有替换失败场景；未删除用例、未降低原文件字节与临时文件清理断言。旧版本两个版本字符串断言同步到 0.9.0。

## 自动化测试与代码检查

- 基线：287 passed，24 subtests passed，41.04 秒。
- 修复前三项后完整回归：293 passed，24 subtests passed，33.51 秒。
- 算法与质量定向回归：74 passed，1.50 秒。
- 新增质量回归：11 passed；隔离恢复/业务测试：10 passed；原生 Qt 三组缩放：3 passed。
- 最终完整 offscreen：311 passed，24 subtests passed，54.38 秒，0 failed、0 skipped，包含显式 Windows 扩展长路径端到端。
- 最终原生全量结果：311 passed，24 subtests passed，64.34秒，0 failed、0 skipped；包含显式扩展长路径端到端。
- `python -m compileall -q main.py smartpower tests tools`：PASS。
- 新 venv `python -m pip check`：PASS，No broken requirements found。
- `git diff --check`：PASS，提交前执行。
- Windows CI 增加语法检查和原生窗口/缩放/恢复回归；保留完整 offscreen pytest。实际代码提交 `dfe3596ffdc6760971d349a77c36ad85df84a738` 的 [PR CI](https://github.com/sunyiyang299-cell/SmartPowerAnalyzer/actions/runs/39425536195) 与 [push CI](https://github.com/sunyiyang299-cell/SmartPowerAnalyzer/actions/runs/39425528019) 均 success；完整 offscreen 311 passed、24 subtests passed、74.40秒，原生专项20 passed、19 subtests passed、28.81秒，0 failed、0 skipped，依赖/语法检查也通过。后续提交仅补充这份CI记录，最终状态见 [PR #6 Checks](https://github.com/sunyiyang299-cell/SmartPowerAnalyzer/pull/6/checks)。

测试开发过程中纠正了新测试的控件接口（曲线键、QPlainTextEdit）和截图断言（从任意压缩字节阈值改为 PNG 签名及像素尺寸）；不是软件计算错误。中间原生测试的普通长路径创建失败按以下限制记录，随后改用显式扩展路径完成原有完整业务断言，没有跳过失败测试。

## 功能覆盖与验证范围

| 项目 | 状态 | 证据及边界 |
|---|---|---|
| 八页导航、最大化/缩放、快捷入口、未选数据提示 | PASS | 保留 test_window、test_analysis_ui、test_anomaly_ui、test_reports_settings_ui |
| CSV/Excel、UTF-8/GB18030、中文路径、空/损坏文件、重复/缺失字段、非法时间/数值/PF | PASS | 保留 test_importer；大 CSV 另测1000/1万/10万 |
| SQLite 保存、列表、读取、删除确认、事务回滚、新 schema 拒绝 | PASS | 保留 repository/data_ui 测试，新增异常终止恢复；测试自动隔离 DB 与设置路径 |
| 电压/电流/PF 总体统计、P/S/无功绝对值 | PASS | 旧全量算法测试与新增 Decimal/下溢回归；基础算例 P=1980 W，S=2200 VA，绝对无功约958.9577676 var |
| 异常阈值等号、多事件、唯一采样点、来源、索引、竞态 | PASS | 原 test_anomaly/test_anomaly_ui 保留，按完整记录检测，不以显示抽稀输入 |
| 图表乱序/重复/不等间隔/跨日期、缩放平移、重置、PNG、旧数据保护 | PASS | 保留 test_visualization，含十万条完整检测与标记上限验证 |
| 导入→SQLite→分析→曲线→检测→PDF/XLSX→新进程读取 | PASS | test_release_hardening，150条模拟数据，PNG真实生成，报告重开与值断言，新进程来源标记不丢失 |
| 配置持久化、损坏、非法值、恢复默认、保存失败 | PASS | 保留 test_settings/test_reports_settings_ui，新增 exists 权限失败回归 |
| 后台任务中关闭保护 | PASS | 原有真实报告导出关闭测试；新增实际 QThread 等待时对 data/analysis/reports 的关闭保护，覆盖导入/存储/分析/PDF/Excel 共用 guard；不是每种任务均被强杀 |
| Windows 11 原生 Qt、中文用户目录、非管理员 | PASS | 本机 windows 平台全量回归；安装到独立新 venv |
| 900×620、QT_SCALE_FACTOR=1/1.25/1.5 | PASS | 三个独立进程、八页切换、滚动可达、PNG尺寸按实际DPR断言；与本机原生DPI叠加，不等价于真实系统DPI切换 |
| 普通 >260 字符路径 | FAIL | 本机 Path.mkdir WinError3，系统传统 MAX_PATH 限制；未修改用户系统策略。显式 `\\?\` 长路径模式端到端通过，不保证所有外部工具/EXE支持 |
| Windows 独占文件占用 / 只读目标文件 | PASS | 原生 CreateFileW(share=0) 与只读属性，实际替换失败，旧字节与临时清理断言 |
| 无写入权限目录 / 只读目录 ACL | NOT TESTED | 未更改用户目录 ACL。PermissionError 已注入测试；不把文件只读属性视为目录拒写 |
| 磁盘满 | PASS | ENOSPC 故障注入，旧设置/报告不替换；未实际填满磁盘 |
| 离线启动与业务 | PASS | 禁用 Python socket.connect/create_connection，实际构造八页并执行端到端；不是物理断网实测 |
| Windows10、真实系统DPI切换、长时间人工交互、EXE安装 | NOT TESTED | 无对应环境或尚未打包 |

## PDF / Excel 真实产物

默认 STSong-Light 引用、NotoSansSC TrueType 嵌入模式各生成20页PDF（1000条模拟数据、378事件）。pypdf重开检查来源/名称，嵌入模式检查到FontFile2，默认模式未嵌入；全部40页经PDFium渲染并检查联系表及关键大图，中文、三类图表、重复表头、页脚/页码无明显遮挡。合法字体仅来自本机先前取得的QA字体，未提交字体二进制。

缺失字体、拉丁字体缺字、默认引用非BMP字符均保留拒绝导出的旧测试。没有把本机PDFium显示成功等同于跨机器兼容：默认引用依赖阅读器中文字体支持；用户嵌入字体须核对实际许可。跨机器阅读器兼容性 **NOT TESTED**。

十万条完整产物另用 `tools/verify_quality_exports.py` 核验：1285页PDF逐事件正则解析，与完整检测事件顺序/索引/时间/类型/数值/阈值/单位精确匹配37077条；每页有正确页码且三类图表标题存在。Excel用openpyxl重新读取，100000条原始记录逐行比对数值、时间、来源，37077条异常逐条匹配。六个工作表存在，原始数据不抽稀。真实Microsoft Excel/打印效果 **NOT TESTED**。公式注入、行数上限、写入失败、确认覆盖等旧测试全部保留。

## 性能与资源

工具：`tools/quality_benchmark.py`。同一数据规模重复3轮，seed=42，仅模拟数据；阈值U<220、U>240、I>20。数据与报告生成在实际TaskThread，Qt主线程10ms定时器记录间隔；绘图/PNG为GUI线程实际执行。CPU为整个进程CPU秒，内存为 **进程累计峰值工作集**，不能当成每个任务的增量内存。部分测量与其他QA任务并行，有资源争用；不是通用性能承诺。

原始90条记录（27个任务+3个产物汇总×3规模）见 [performance-v0.9.json](quality/performance-v0.9.json)，含每轮实际wall/CPU、峰值、定时器间隔、事件数、文件大小。下表为秒的中位数 [最小,最大]：

| 任务 | 1000条 | 10000条 | 100000条 |
|---|---|---|---|
| CSV导入 | .0194 [.0185,.0207] | .0645 [.0515,.0676] | .2848 [.2780,.2874] |
| SQLite保存 | .0632 [.0613,.0632] | .1321 [.1037,.1352] | .5545 [.5350,.5587] |
| SQLite读取 | .0127 [.0126,.0162] | .0424 [.0379,.0562] | .2641 [.2584,.2739] |
| 电气分析 | .0089 [.0076,.0097] | .0375 [.0271,.0380] | .2103 [.2021,.2164] |
| 异常检测 | .0073 [.0065,.0092] | .0484 [.0334,.0538] | .2701 [.2531,1.1646] |
| 绘图及PNG | .0849 [.0665,.0855] | .1198 [.1149,.1201] | .1334 [.1320,.1352] |
| 报告快照 | .0309 [.0303,.0452] | .1501 [.1178,.1746] | .9565 [.9490,1.0033] |
| PDF | .2792 [.2647,.2851] | 3.0145 [2.9846,3.2176] | 56.1221 [55.0573,57.6097] |
| Excel | .9821 [.9528,1.0699] | 10.1542 [9.6709,10.4289] | 64.6750 [63.5982,77.5081] |

对应事件378/3690/37077，唯一异常采样341/3353/33700。第三轮PDF大小104886/487192/3935294字节，Excel184242/1713326/17048060字节，页数20/134/1285。各规模进程最终峰值194.87/256.05/853.03 MiB。10万条 PDF 最大定时器间隔0.9802秒、Excel0.4657秒，仍有短暂停顿；不能称为完全不卡顿。图表/PNG最大约0.0757秒。未实现取消、流式PDF明细或超过10万条的长期压力测试。

复现（输出目录必须不存在，禁止指向真实数据目录）：

```powershell
python tools/quality_benchmark.py --count 100000 --repeat 3 --output ./qa-output/performance-100k
python tools/verify_quality_exports.py ./qa-output/performance-100k/2
```

## 异常终止与恢复

隔离子进程在SQLite `BEGIN IMMEDIATE` 事务更新后被kill，新连接读取原数据，PRAGMA integrity_check=ok；报告临时文件写入后被kill，已有目标字节不变。强杀不执行finally，未发布临时文件可残留。测试仅清理自己明确知道的临时文件；应用不自动扫描删除其他进程/用户文件。设置/报告ENOSPC、占用目标、普通失败路径有原文件保护断言。断电、存储设备故障、文件系统损坏与已发布文件的物理耐久性 **NOT TESTED**，不承诺断电零丢失。

## 依赖、安全与隐私

运行依赖未盲目升级，没有新增运行依赖。全新venv安装与pip check通过，只证明兼容和依赖完整性。QA安装pip-audit 2.10.1，首次解析未完成；第二次对新venv冻结清单使用 `--disable-pip --no-deps --timeout 15`，总180秒超时，未取得有效漏洞报告。因此最新漏洞数据库审计 **NOT TESTED**，不声称依赖无漏洞；正式发布前须联网复查并处理受影响版本。

静态检查范围：main.py、smartpower、tools、工作流及待提交文件。运行模块无requests/socket/urllib/QtNetwork等网络调用或上传逻辑，未发现令牌、密码、硬编码本机用户路径；README/旧验证文档仅有公共资料链接。socket禁用下业务仍可运行。所有QA数据来自generate_demo；原始用户数据、个人设置、字体、PDF/XLSX/PNG产物不入库。测试fixture自动隔离数据库和配置；这不是完整第三方依赖安全审计或隐私认证。

EXE发行许可汇编、Qt插件/中文翻译/ReportLab资源收集、字体分发许可、安装包签名、防病毒误报、离线新机运行均 **NOT TESTED**。软件著作权登记材料尚未制作。

## 文件变更

新增：`tests/test_quality_regressions.py`、`tests/test_release_hardening.py`、`tests/test_scaled_layout.py`、`tools/quality_benchmark.py`、`tools/verify_quality_exports.py`、`docs/VALIDATION_V0.9.md`、`docs/RELEASE_READINESS.md`、`docs/quality/performance-v0.9.json`。

修改：`smartpower/analysis/statistics.py`、`smartpower/analysis/power.py`、`smartpower/settings/manager.py`、`smartpower/data/demo.py`、`smartpower/ui/pages/data_management.py`、`smartpower/ui/pages/reports.py`、`smartpower/config.py`、`tests/conftest.py`、`tests/test_demo.py`、`tests/test_reporting.py`、`tests/test_structure.py`、`.github/workflows/tests.yml`、`.gitignore`、`README.md`。

## 发布判断

可以进入V1.0 EXE打包和安装验证阶段；**不等于达到正式发行条件**。四项P0/P1已修复，P2资源负担尚未消除。最新漏洞审计、普通长路径兼容、Windows10、真实DPI/多机器阅读器、EXE及许可材料仍需完成。远程CI须通过后再由用户审核PR，不自动合并。
