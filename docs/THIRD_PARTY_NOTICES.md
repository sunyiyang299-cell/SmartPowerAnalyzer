# 第三方组件与发行审查记录

本记录对应V1.0候选构建，不等于已完成全部发行许可审查。应用自身著作权人和授权方式须由申请人确认，未擅自添加MIT等应用许可证。

版本来自实际构建环境metadata，许可原文复制在onedir的`_internal/notices`，精确路径见其中`inventory.json`。目录分发保留Qt等动态库，没有加密封装或防替换机制。

| 组件 | 实际版本 | 元数据许可标识（不是法律结论） | 原文来源 |
|---|---|---|---|
| PySide6 | 6.10.3 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | 安装轮子自带许可证；`_internal/notices/PySide6` |
| PySide6_Essentials | 6.10.3 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | 安装轮子自带许可证；`_internal/notices/PySide6_Essentials` |
| PySide6_Addons | 6.10.3 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | 安装轮子自带许可证；`_internal/notices/PySide6_Addons` |
| shiboken6 | 6.10.3 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | 安装轮子自带许可证；`_internal/notices/shiboken6` |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | 安装轮子自带许可证；`_internal/notices/numpy` |
| pandas | 3.0.6 | BSD 3-Clause License | 安装轮子自带许可证；`_internal/notices/pandas` |
| pyqtgraph | 0.14.0 | MIT | 安装轮子自带许可证；`_internal/notices/pyqtgraph` |
| openpyxl | 3.1.5 | MIT | 安装轮子自带许可证；`_internal/notices/openpyxl` |
| reportlab | 5.0.1 | BSD license (see license.txt for details), Copyright (c) 2000-2025, ReportLab Inc. | 安装轮子自带许可证；`_internal/notices/reportlab` |
| pillow | 13.0.0 | MIT-CMU | 安装轮子自带许可证；`_internal/notices/pillow` |
| charset-normalizer | 3.5.2 | MIT | 安装轮子自带许可证；`_internal/notices/charset-normalizer` |
| python-dateutil | 2.9.0.post0 | Dual License | 安装轮子自带许可证；`_internal/notices/python-dateutil` |
| six | 1.17.0 | MIT | 安装轮子自带许可证；`_internal/notices/six` |
| tzdata | 2026.5 | Apache-2.0 | 安装轮子自带许可证；`_internal/notices/tzdata` |
| colorama | 0.4.6 | UNCONFIRMED | 安装轮子自带许可证；`_internal/notices/colorama` |
| et-xmlfile | 2.0.0 | MIT | 安装轮子自带许可证；`_internal/notices/et-xmlfile` |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | 安装轮子自带许可证；`_internal/notices/packaging` |
| pyinstaller | 6.22.3 | GPLv2-or-later with a special exception which allows to use PyInstaller to build and distribute non-free programs (including commercial ones) | 安装轮子自带许可证；`_internal/notices/pyinstaller` |
| pyinstaller-hooks-contrib | 2026.8 | UNCONFIRMED | 安装轮子自带许可证；`_internal/notices/pyinstaller-hooks-contrib` |

Python 3.13.0：实际python313.dll与标准库来自构建解释器；Python-LICENSE.txt随包保留。SQLite来自Python标准库运行环境，不安装第三方Python sqlite包。

## 已执行的整理

- 完整保留复制到notices目录的许可证和原版权声明，不把它们当作本项目自有代码。NumPy等轮子含多项子组件许可，应以完整原文为准。
- Qt/PySide6/Shiboken版本6.10.3，未修改DLL。另保留Qt LGPLv3/GPLv3原文；轮子商业许可引用文本也保留，不能据其存在认定本项目拥有商业许可。
- 构建限定Python/Windows原生依赖来源，排除来自开发工具PATH的Poppler/libheif库。未采用QML、VirtualKeyboard、QtPdf及其插件；PDF由ReportLab生成。
- 原创图标由仓库SVG及可复现脚本生成，不使用外部商标或网络图片。
- 不附带第三方字体二进制；ReportLab自动收集的.ttf/.ttc/.otf/.pfb被排除。PDF默认CID引用，用户可配置有合法嵌入许可的字体。手册PDF若使用默认引用，同样受阅读器中文支持限制。
- Inno Setup 6.7.3工具来自官方发布，下载SHA256为9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732，官方签名Pyrsys B.V.验证为Valid。Inno原文在packaging/licenses/Inno-Setup.txt；中文翻译取自同标签官方仓库并保留作者署名。
- PyInstaller 6.22.3及hooks 2026.8仅为构建工具；保留其许可证。PyInstaller构建例外不替代应用依赖各自的许可义务。

## 正式发行阻塞项

1. Qt/PySide6选择开源许可路线时，需逐组件核对实际适用许可，安排准确对应源码提供方式、用户替换/重链接与调试权利、必要安装信息、版权和通知。现已保留动态库及条款，但未冒充已完成所有LGPL履约。
2. VC运行库来自锁定PySide6轮子，实际文件版本14.44.35211.0；轮子携带并不自动证明本申请人的再分发授权条件已满足。需核对Microsoft条款和可分发清单，补齐适用许可记录。正式分发前不得仅以“开源依赖”作替代结论。
3. 需完成最终包所有DLL/Qt插件的组件与许可证对应表，包括Python附带的OpenSSL、压缩/加密库和Qt第三方组件。当前metadata/原文收集不等于逐二进制法律审计。
4. 应用自身权利归属、第三方源代码来源、AI辅助开发事实与最终对外许可由申请人确认。没有伪造作者、开发完成日期、首次发表情况或商业授权。
5. 未解决以上事项、独立干净机与必要兼容验证前，只保留本地候选包，不自动正式发布Release或标签。

## 核对依据

- [Qt6.10许可概览](https://doc.qt.io/qt-6.10/licensing.html)
- [Qt官方LGPL义务说明](https://www.qt.io/development/open-source-lgpl-obligations)
- [Qt for Python第三方许可](https://doc.qt.io/qtforpython-6.10/licenses.html)
- [Qt6.10.3 LGPL原文](https://github.com/qt/qtbase/blob/v6.10.3/LICENSES/LGPL-3.0-only.txt)
- [PyInstaller许可及构建例外](https://pyinstaller.org/en/stable/license.html)
- [Microsoft VC再分发说明](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files)
- [Microsoft需分发DLL的确定方法](https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute)
- [Inno Setup准确标签许可](https://github.com/jrsoftware/issrc/blob/is-6_7_3/LICENSE.TXT)

查询日期以VALIDATION_V1.0记录为准。以上为技术材料整理与待核对事项，不保证授权或软著登记结果。
