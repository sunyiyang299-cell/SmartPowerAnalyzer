# V1.0 发布准备清单

状态截至V0.9本机验证；详细证据、缺陷和测试范围见 [VALIDATION_V0.9.md](VALIDATION_V0.9.md)。PASS不扩展到未列明的环境。

| 检查项 | 状态 | 证据或待办 |
|---|---|---|
| V0.1～V0.5源码与八页功能保留 | PASS | 以main合并PR1～5为基线，完整回归，无业务模块/测试删除 |
| 电气计算准确性 | PASS | 旧基础算例/非法输入/极值；Decimal精度和下溢修复回归 |
| 单相RMS模型、PF算术平均、无功绝对值说明 | PASS | 原算法和说明保留，非三相/谐波/能量计量模型 |
| 数据完整性 | PASS | SQLite事务/重启/kill；十万条Excel逐条与37077事件核验 |
| Windows11 Python3.13源码安装运行 | PASS | 独立新venv，非管理员，原生Qt回归 |
| Windows10 | NOT TESTED | 需要独立实机/虚拟机 |
| GUI常规回归、关闭/竞态保护 | PASS | 八页、实际QThread、原有后台报告任务与切换用例 |
| 900×620及Qt缩放自动化 | PASS | QT_SCALE_FACTOR1/1.25/1.5叠加实际DPI，非人工系统设置测试 |
| 真实系统DPI切换、多显示器、长期人工操作 | NOT TESTED | V1.0安装包阶段验证 |
| 中文路径与显式Windows扩展长路径 | PASS | >260字符端到端；不修改系统策略 |
| 普通Windows >260字符路径 | FAIL | 本机MAX_PATH限制，需系统策略/应用路径适配评估 |
| 实际文件占用与目标文件只读 | PASS | CreateFileW独占及只读属性，旧文件保护 |
| 目录ACL拒写实测 | NOT TESTED | 目前仅权限故障注入，未修改用户目录ACL |
| 磁盘满保护 | PASS | ENOSPC注入；不是实际耗尽磁盘 |
| 离线核心业务 | PASS | socket禁用启动及端到端，非物理断网 |
| 真正物理断网及新机离线EXE | NOT TESTED | 打包后执行 |
| PDF/Excel导出内容 | PASS | 真实产物重开，PDF事件全量匹配，Excel原始全量值/顺序/来源 |
| PDF中文引用/嵌入本机渲染 | PASS | 两种模式各20页，渲染40页、FontFile2检查；缺失/缺字拒绝 |
| 跨机器中文阅读器与Microsoft Excel实机 | NOT TESTED | 尤其默认CID字体依赖阅读器支持 |
| 大报告资源体验 | FAIL | 10万条PDF1285页、峰值约853MiB；已提示，尚无取消/内存上限 |
| 配置持久化与损坏/权限回退 | PASS | 原文件保护与中文错误回归 |
| 强杀恢复 | PASS | 隔离SQLite完整性和已有报告字节断言；强杀可残留未发布临时文件 |
| 断电与存储设备故障恢复 | NOT TESTED | 不能从kill测试推导断电耐久性 |
| 最新依赖漏洞数据库 | NOT TESTED | pip-audit有界超时，未取得有效结果；发行前必须重查 |
| 依赖兼容性与锁定 | PASS | requirements不变，独立环境安装与pip check通过 |
| 完整第三方依赖/Qt/字体许可汇编 | NOT TESTED | 需按实际EXE内容整理许可及分发义务 |
| 本次字体二进制分发 | NOT APPLICABLE | 未提交或分发字体文件；本机QA使用已有字体 |
| 版本与正式名称 | PASS | 开发0.9.0，正式名称V1.0不变 |
| 源码、测试、文件清单 | PASS | 新增/修改文件见验证记录，无真实数据库/报告入库 |
| 本机自动化测试及语法 | PASS | 最终数量/时间见验证记录；不跳过失败测试 |
| GitHub Actions | NOT TESTED | 创建PR后检查；以PR实时Checks与最终交付报告为准 |
| EXE构建/干净Windows安装与卸载/升级 | NOT TESTED | 收集Qt平台/翻译/ReportLab/NumPy等资源，验证数据目录、卸载保留数据 |
| 安装签名/防病毒/自动更新策略 | NOT TESTED | V1.0发布流程待定；不擅自添加网络更新 |
| 使用说明书/软件著作权材料 | NOT TESTED | 待基于最终软件制作真实截图、说明书、源码材料 |

结论：具备进入V1.0打包与验证工作的基础；当前不是可直接正式发行的安装包。发行前完成FAIL和关键NOT TESTED项，人工审核后决定是否合并/发布。
