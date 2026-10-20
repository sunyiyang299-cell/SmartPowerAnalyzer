# V1.0 Windows 候选交付验证记录

验证周期：2026-10-20～2026-10-21（Asia/Shanghai）。这是实际开发/测试记录，不是软件著作权申请的法定完成或首次发表日期。

## 基线与版本

GitHub main基线`54e90b17bb16109417aef5be0cddf3877bca97bd`，PR#1～#6已Merged。分支`release/v1.0-windows`。业务源码快照`0d8d871ad6755808732f8ba3683e4fe4ad00b33c`；当前main.py/smartpower与该提交一致，冻结程序使用此业务源码，正式名称不变，版本1.0.0。未直接修改main、强推、删除分支或创建Release/标签。

## 构建环境与实际步骤

Windows11 x64 build26200，AMD64 Family25 Model97 Stepping2，Python3.13.0，SQLite3.45.3，独立新venv。PyInstaller6.22.3、hooks2026.8、Inno Setup6.7.3；完整锁定见requirements-windows-build.lock。运行依赖保持原版本，因实际PyPI公告将构建pip24.2更新为26.2.1。

实际执行了：

```powershell
python -m pytest -q
python -m compileall -q main.py smartpower tests tools
python -m pip check
python -m PyInstaller --noconfirm --clean --distpath ../v10-dist --workpath ../v10-build packaging/SmartPowerAnalyzer.spec
python tools/verify_frozen.py ../v10-dist/SmartPowerAnalyzer ../v10-frozen-delivery
# 用已验证的官方Inno6.7.3 ISCC编译SmartPowerAnalyzer.iss，传入实际DistDir与ReleaseDir
python tools/verify_installer.py ../v10-release/SmartPowerAnalyzer-Setup-1.0.0.exe ../v10-installation-delivery
python tools/make_release.py ../v10-dist/SmartPowerAnalyzer ../v10-release
python tools/verify_quality_exports.py ../v10-performance-100000/0
git diff --check
```

上述为记录的相对路径；不能在已有真实数据目录执行验证器。可重建入口见packaging/build_windows.ps1与README，工具下载由setup_inno.ps1校验SHA和官方签名。产物为真实文件，不以空文件占位。流程可重建，但不承诺每次PE时间戳/压缩结果逐字节相同，各构建使用自己的校验值。

## 实现与修正

1. 版本、EXE属性、应用图标、资源路径、关于卡片、PDF/XLSX版本保持1.0.0。
2. DeferredEventTable最多256事件延迟排版，字体检查仅累积字符集；不删除明细。十万条37077事件逐条重开验证通过。
3. 真实EXE首次失败，定位为开发工具PATH中Poppler ICU/libheif库污染。清理DLL搜索路径、限定来源、统一轮子VC运行库并剔除未用QML/VirtualKeyboard/QtPdf。最终产物普通启动及全业务通过；不是依赖EXE存在来判断成功。
4. 启动时序增加回归，显示调度在活动事件循环中；外部关闭验证等待初次show/paint完成。修复前回归失败，修复后通过，最终实际普通关闭/重启验证通过。
5. onedir不包含用户DB、配置、日志、个人报告或第三方字体文件。内含Qt平台/中文翻译、数值与报告依赖及原许可证；用户数据仍用QStandardPaths，与安装目录隔离。
6. 当前用户Inno安装、开始菜单/可选桌面任务、卸载不清理用户数据；安全隔离验证器拒绝已有安装注册和已有验证目录。
7. 原创SVG及16/32/48/64/256多尺寸ICO，保留生成脚本。没有借用第三方商标或未经授权字体。

## 实际测试结果

详见[TEST_REPORT_V1.0.md](TEST_REPORT_V1.0.md)，不把计划/源码验证扩展为安装器结果。

- 基线311 passed/24子测试，68.75秒；最终offscreen318 passed/24子测试，79.14秒；原生Qt318 passed/24子测试，100.25秒；均0失败、0跳过。
- compileall、pip check、PowerShell语法、实际Inno编译、git diff --check通过。
- 普通EXE可见窗口、官方标题与正常关闭；实际冻结全业务1000条模拟记录、717事件，两种导入、SQLite、分析、曲线、PNG、PDF/XLSX真实保存对话框、设置和新进程重读通过。
- 子进程PATH不含Python/Git，cwd不含源码，完整复制包在中文路径运行；宿主仍安装Python，不能称为独立无Python机器。
- 当前用户安装、从安装目录及实际开始菜单.lnk启动、安装EXE全业务、卸载、数据/设置/报告逐字节保留、重装重读、最终卸载及目录/QA菜单/注册项清理通过。
- 桌面快捷方式任务未选，NOT TESTED；默认用户AppData真实数据未操作，安装验收使用自选隔离目录及隔离数据覆盖。
- 十万条：PDF1290页、37077事件全量匹配，Excel100000原始行和37077事件逐条核对通过；PNG/报告来源保持模拟标记。
- 用户手册PDF10页、8张真实冻结EXE截图（路径遮蔽），本机PDFium渲染检查全部页；默认中文引用不等于跨机字体已验证。

## 性能与资源

十万条模拟数据单轮、与构建并行。PDF22.5747秒，进程累计峰值273.95MiB、最大GUI定时器间隔0.0984秒；V0.9三轮约55.06～57.61秒、峰值853.03MiB。页数1285→1290是分批重复表头，不是遗漏/删减。

同轮Excel93.2347秒，整个进程累计峰值508.46MiB；不能将其当作Excel增量内存或通用提速结论。没有安全取消或百分比进度，大报告仍需等待，强杀可残留未发布临时文件。原始测量见docs/quality/performance-v1.0.json。

## 安全、隐私和许可

PyPI JSON版本公告实际查询29个安装分发，首次pip24.2命中CVE-2025-8869、CVE-2026-1703、CVE-2026-3219、CVE-2026-6357、CVE-2026-8643、CVE-2026-13346等公告，原结果有重复别名；固定pip26.2.1后全部查询成功、未检出版本公告。证据docs/quality/security-v1.0.json，工具tools/audit_dependencies.py。该检查不是pip-audit全量结果，亦不覆盖全部CPython、SQLite/Qt原生组件或Windows漏洞；不能声称“没有安全漏洞”。

仅generate_demo模拟数据进入验证；未提交DB、个人报告、日志、字体二进制或EXE/ZIP。截图显示真实GUI，测试路径在控件中遮蔽。源码与脚本无硬编码个人目录、令牌、上传电气数据或自动更新逻辑。EXE业务中禁用Python socket，不等于物理断网/全流量网络捕获。

许可证原文和实际版本已随onedir收集；发行审查**FAIL（阻塞）**：Qt对应源码提供/替换和调试权利、VC再分发授权、全部原生组件义务及应用自身权属仍需确认。详见[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。不把轮子携带DLL视为申请人当然已获全部发行授权。

## 实际发布文件与SHA-256

以下为本机最终候选产物的实际哈希；CI重建会有自己的哈希，不可混用。安装器和ZIP只保留本地/CI候选产物，不提交源码仓库，不自动正式发布。

| 文件 | 字节 | SHA-256 |
|---|---:|---|
| RELEASE_NOTES_V1.0.md | 2779 | `8a0d57736eed1d18af556c42081add7ababc68e5dc2ecbb99b243dd70c8c1d67` |
| SmartPowerAnalyzer-Portable-1.0.0.zip | 72408635 | `67fe2c55ba04ca252ade6ec6ddb90ba10b6d05d2d50de8126d362ccb63aa8968` |
| SmartPowerAnalyzer-Setup-1.0.0.exe | 51083599 | `54bdfaaddf86474a1d9062cac68426d65f3fe0fa116731ae2584d8195dbdb5a1` |
| USER_MANUAL_V1.0.pdf | 959470 | `8fd1822815837b18eb7677dff9fba9089ab44505854ae4aed3ed84663ed4b287` |

完整onedir主程序SmartPowerAnalyzer.exe：SHA256 `0da0f585221b9ec6743a22a4a93087cc6fbafae5fcc2e561855238fd5d7d1bee`；ZIP实际1025个文件条目，CRC校验通过；EXE自身不单独代替整个运行目录。

## 文档、软著与范围

- docs/USER_MANUAL_V1.0.md（另生成PDF）、SOFTWARE_DESIGN_V1.0.md、TEST_REPORT_V1.0.md、THIRD_PARTY_NOTICES.md与真实截图。
- copyright/SOURCE_MANIFEST.md、SOURCE_EXCERPT_V1.0.txt来自明确Git提交的项目Python源码，排除第三方库与缓存。材料记录真实生成时点，不冒充软件完成或首次发表日期。
- copyright/APPLICATION_INFO_TEMPLATE.md与MATERIALS_CHECKLIST.md保留身份、权属、开发方式、日期等申请人待确认项；如实记录AI辅助开发，未申请或保证登记。

## 未验证与发布建议

**NOT TESTED**：独立无Python机器、Windows10、不同账号/真实系统DPI切换、物理断网、跨机阅读器/真实Microsoft Excel、目录ACL实测、长期压力/断电、代码签名与杀毒兼容、完整原生安全与发行许可验收。普通长路径仍受环境限制；默认CID字体不能保证所有阅读器。

**结论：已完成源码开发、自动化、本机真实冻结与安装/卸载/重装验证；未完成独立Windows和关键许可验收。保持发行候选状态，不能作正式公开发行或软著登记已完成的结论。** PR目标main，不自动合并、不创建正式Release或标签。

CI：创建PR后实际等待并在交付报告记录最终结果。源码测试工作流与Windows真实构建/运行/安装工作流分开检查，尚未完成的远程步骤不预先写PASS。
