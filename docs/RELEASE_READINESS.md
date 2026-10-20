# V1.0 发行候选验收清单

验证周期2026-10-20～2026-10-21；详细实际证据见[VALIDATION_V1.0](VALIDATION_V1.0.md)和[TEST_REPORT_V1.0](TEST_REPORT_V1.0.md)。状态只覆盖列明范围，未测试不得扩展为PASS。

| 项目 | 状态 | 证据/边界 |
|---|---|---|
| PR1～6基线与全部业务/历史测试保留 | PASS | main54e90b1；无模块或测试删除 |
| 正式名称、1.0.0版本、EXE资源 | PASS | 窗口/设置/报告/EXE/安装器一致；原创可编辑SVG及多尺寸ICO |
| 电气统计与功率模型 | PASS | 全部旧算法测试；PF算术平均、无功绝对值、极值/非法输入回归 |
| 源码全量自动化 | PASS | offscreen321项/24子测试89.30s；Windows原生321项/24子测试94.57s，均0失败/0跳过 |
| 编译/依赖/脚本 | PASS | compileall、pip check、git diff --check、PowerShell解析、Inno真实编译 |
| 真实onedir EXE普通启动/关闭 | PASS | 真实可见窗口与官方标题，初始化完成后正常关闭退出0 |
| 实际EXE业务与重启 | PASS | 隔离1000模拟记录、717事件、导入/DB/三类分析/图/PNG/PDF/XLSX/设置/重读 |
| 运行目录与开发环境分离 | PASS（限定） | 中文复制目录、独立cwd、子PATH无Python/Git；宿主仍装Python |
| 独立无Python干净Windows机器 | NOT TESTED | 需要独立虚拟机或电脑验收 |
| 当前用户自选路径安装 | PASS | 真实Setup、非管理员、版本注册与开始菜单创建；不操作真实用户数据库 |
| 开始菜单和安装目录启动 | PASS | .lnk经ShellExecuteEx与EXE普通启动实际验证 |
| 可选桌面快捷方式 | NOT TESTED | 配置存在/编译通过，本机未选择此任务，不修改已有桌面 |
| 卸载/重装及数据保留 | PASS | 隔离数据/设置/报告逐字节不变；重装重读、最终安装目录/QA菜单/注册项清理 |
| 完整便携ZIP/真实SHA256 | PASS | ZIP1025条目CRC、深层解压后实际EXE全业务/重启通过；安装器/ZIP/手册/说明均按实际文件计算哈希 |
| PDF/Excel完整记录 | PASS | 十万原始记录和37077事件；PDF1290页全事件匹配，Excel逐行核对 |
| 大PDF资源改进 | PASS（限定） | 256事件延迟排版，单轮22.6秒/273.95MiB；未静默删事件 |
| 大报告取消/百分比进度/长期压力 | NOT TESTED | 取消与百分比尚未实现，不以强杀替代；只有忙碌与容量提示 |
| Windows11中文用户/文件路径 | PASS | 本机实际运行与安装 |
| Windows10/不同账号/真实DPI切换 | NOT TESTED | Qt缩放自动化不等于真实系统DPI，未做独立账号/Windows10 |
| 普通超长路径无条件支持 | FAIL（限制） | 明确系统与库限制；显式扩展路径回归通过，不修改用户策略 |
| 文件占用/只读目标/磁盘满/事务/kill | PASS（限定） | 真实文件占用与只读；ENOSPC故障注入；隔离kill恢复。非实际填盘或断电 |
| 目录ACL/断电与设备故障 | NOT TESTED | 未修改用户目录ACL，未进行断电测试 |
| PDF字体与手册本机渲染 | PASS（限定） | 默认CID引用、用户TrueType机制保留；10页手册与实际报告渲染检查 |
| 自带中文字体分发 | NOT APPLICABLE | 不分发第三方字体二进制；原创图标不含字体 |
| 跨机器阅读器/真实Microsoft Excel | NOT TESTED | PDFium/pypdf/openpyxl不能替代跨机器/真实Excel验收 |
| 离线核心业务 | PASS（限定） | 实际EXE中禁用Python socket；没有新增联网业务 |
| 物理断网/全部原生网络流量 | NOT TESTED | 未物理断网或抓包，不声称完全独立网络审计 |
| PyPI分发版本公告 | PASS（限定） | 29包全部查询成功，pip26.2.1后未检出；证据security-v1.0.json |
| CPython/SQLite/Qt/系统完整安全复核 | NOT TESTED | PyPI公告范围不覆盖全部原生组件或解释器补丁 |
| Qt/VC/全组件再分发义务 | FAIL（阻塞） | 已保留版本与原文；对应源码/用户权利/VC授权/全DLL许可仍需正式确认 |
| 应用权属及自身对外许可 | FAIL（待申请人） | 不依据GitHub用户名推断权利人，不擅自给出应用许可证 |
| 私人数据与敏感信息检查 | PASS（范围限定） | 只提交模拟证据、真实已遮蔽截图、源码/文档；不提交DB/日志/EXE/ZIP或令牌 |
| 用户手册/设计/测试/验证 | PASS | 真实代码与运行截图候选材料，手册另有10页PDF |
| 软著源码候选材料 | PASS（候选） | 60个项目Python文件/3398行，固定实际Git提交和SHA256，排除依赖源代码 |
| 软著申请人信息/格式核对/登记结果 | NOT TESTED | 待申请人提供和确认；未执行登记、不保证通过 |
| 代码签名/杀毒/SmartScreen | NOT TESTED | EXE/安装包未签名，尚未做相关验收 |
| Windows CI构建/运行/安装 | NOT TESTED | 创建PR后实际等待，最终状态在PR Checks与交付报告记录，不预填通过 |
| 自动正式Release/标签/合并 | NOT APPLICABLE | 本次禁止，未执行 |

结论：源码与本机真实EXE/安装器流程已验证，**仍为发行候选包，不具备正式公开发行结论**。须完成许可/权属阻塞和独立机器等关键验收，再由用户审核是否合并及发布。
