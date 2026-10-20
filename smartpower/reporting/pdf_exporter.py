"""Paginated offline Chinese technical PDF, with vector time charts."""

from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, TableStyle

from smartpower.analysis.power import POWER_MODEL
from smartpower.anomaly.models import DISCLAIMER
from smartpower.reporting.chart_renderer import render_chart
from smartpower.reporting.files import atomic_report
from smartpower.reporting.fonts import FONT_LOCK, ensure_glyphs, report_font
from smartpower.reporting.models import LIMITATIONS, statistics_rows


def export_pdf(snapshot, path, *, overwrite=False, font_path=""):
    with FONT_LOCK:
        font = report_font(font_path)
        body = ParagraphStyle("正文", fontName=font, fontSize=10, leading=17, spaceAfter=9, wordWrap="CJK")
        heading = ParagraphStyle("章节", parent=body, fontSize=17, leading=25, textColor=colors.HexColor("#183153"), spaceAfter=18)
        small = ParagraphStyle("表格", parent=body, fontSize=8, leading=12, spaceAfter=0)

        def paragraph(value, style=body):
            return Paragraph(escape(str(value)), style)

        def table(rows, widths):
            result = LongTable([[paragraph(v, small) for v in row] for row in rows], colWidths=widths,
                               repeatRows=1, hAlign="LEFT", splitByRow=1, splitInRow=1)
            result.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9f0fa")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d3ddea")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            return result

        a = snapshot.analysis
        story = [Spacer(1, 65), paragraph(snapshot.product_name, heading), Spacer(1, 25),
                 paragraph(snapshot.title, ParagraphStyle("封面", parent=heading, fontSize=25, leading=36)),
                 Spacer(1, 35), table([
                     ("报告信息", "内容"), ("数据集", a.dataset_name), ("来源", snapshot.source_label),
                     ("生成时间", snapshot.created_at.isoformat(timespec="seconds")),
                     ("开发版本", "V" + snapshot.version), ("报告唯一标识", snapshot.report_id),
                 ], [110, 385]), Spacer(1, 28), paragraph("离线生成 · 单相交流运行数据分析"),
                 paragraph(DISCLAIMER), PageBreak(), paragraph("一、数据概况", heading), table([
                     ("项目", "内容"), ("数据集 ID", a.dataset_id), ("数据集名称", a.dataset_name),
                     ("数据来源", snapshot.source_label), ("是否模拟", "是" if a.simulated else "否，文件来源未核验"),
                     ("采样数量", f"{a.count} 条"), ("起始时间", snapshot.time_start), ("结束时间", snapshot.time_end),
                     ("字段与单位", "时间：本地无时区；电压有效值 V；电流有效值 A；功率因数：无量纲，0～1。"),
                 ], [110, 385]), Spacer(1, 16), paragraph(POWER_MODEL),
                 paragraph("时间范围取完整数据的最早/最晚时间，原始记录顺序不改变。"), PageBreak()]
        rows = statistics_rows(snapshot)
        for mode, title, quantities in (
            ("voltage", "二、电压分析", {a.voltage.quantity}),
            ("current", "三、电流分析", {a.current.quantity}),
            ("power", "四、功率及功率因数分析", {a.power.active_statistics.quantity, a.power.apparent_statistics.quantity,
                                                    a.power.reactive_abs_statistics.quantity, a.power.power_factor_statistics.quantity}),
        ):
            story += [paragraph(title, heading), table([("参数", "统计指标", "数值", "单位")] +
                      [(q, label, f"{value:.12g}", unit) for q, label, value, unit in rows if q in quantities],
                      [150, 135, 140, 70]), Spacer(1, 18), render_chart(snapshot, mode, font),
                      paragraph("绘图可减少显示点数；本报告统计及异常明细均基于完整数据。"), PageBreak()]
        story += [paragraph("五、异常检测结果", heading),
                  paragraph("检测启用状态：已启用。" if snapshot.thresholds is not None else "检测启用状态：未启用。"),
                  paragraph(snapshot.detection_status),
                  paragraph("阈值是用户配置条件，不是国家标准限值；等于阈值不计异常。")]
        if snapshot.detection is not None:
            d, t = snapshot.detection, snapshot.thresholds
            story.append(paragraph(f"检测已启用且已执行：电压下限 {t.voltage_lower:g} V，电压上限 {t.voltage_upper:g} V，电流上限 {t.current_upper:g} A。"))
            story.append(table([("统计项目", "次数 / 数量"), ("异常事件总数", len(d.events)),
                                ("唯一异常采样点", d.unique_sample_count), *d.type_counts.items()], [250, 245]))
            if d.events:
                story += [Spacer(1, 15), paragraph("全部异常明细（原始索引从 0 起）"), table(
                    [("原始索引", "采样时间", "异常类型", "采样值", "用户阈值", "单位")] +
                    [(e.row_index, str(e.timestamp).replace("T", " "), e.kind, f"{e.value:.12g}", f"{e.threshold:.12g}", e.unit)
                     for e in d.events], [48, 151, 72, 82, 82, 60])]
        story += [PageBreak(), paragraph("六、说明与限制", heading)]
        story.extend(paragraph(f"{j + 1}. {text}") for j, text in enumerate(LIMITATIONS))
        story.append(paragraph("中文字体：" + ("用户配置的嵌入式 TrueType 字体。" if font_path else
                    "标准 PDF 中文字体 STSong-Light 引用（未嵌入字体文件），阅读器需支持中文字体/亚洲语言字体包；离线跨机分发建议在系统设置配置有嵌入许可的中文 TrueType 字体。")))

        def texts(item):
            if isinstance(item, Paragraph):
                yield item.getPlainText()
            elif isinstance(item, LongTable):
                for row in item._cellvalues:
                    for cell in row:
                        yield from texts(cell)
            elif hasattr(item, "contents"):
                for child in item.contents:
                    yield from texts(child)
            elif hasattr(item, "text"):
                yield item.text

        ensure_glyphs(font, "".join(text for item in story for text in texts(item)) + "第页智电析运行数据分析")

        def footer(canvas, document):
            canvas.saveState()
            canvas.setFont(font, 8)
            canvas.setFillColor(colors.HexColor("#56677e"))
            canvas.drawString(44, 818, f"智电析 · V{snapshot.version} · 运行数据分析")
            canvas.drawString(44, 29, f"报告 {snapshot.report_id[:8]} · {snapshot.source_label}")
            canvas.drawRightString(A4[0] - 44, 29, f"第 {document.page} 页")
            canvas.restoreState()

        with atomic_report(path, ".pdf", overwrite=overwrite) as temporary:
            document = SimpleDocTemplate(str(temporary), pagesize=A4, rightMargin=44, leftMargin=44,
                                         topMargin=50, bottomMargin=48, title=snapshot.title, author=snapshot.product_name)
            document.build(story, onFirstPage=footer, onLaterPages=footer)
