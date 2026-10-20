"""Standard PDF CJK reference or explicitly configured, embeddable TrueType."""

from hashlib import sha256
from pathlib import Path
from threading import RLock

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont

from smartpower.data.validation import DataError

FONT_LOCK = RLock()


def report_font(path=""):
    with FONT_LOCK:
        if not path:
            name = "STSong-Light"
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(UnicodeCIDFont(name))
            return name
        target = Path(path)
        if not target.is_file() or target.suffix.lower() not in (".ttf", ".ttc"):
            raise DataError("中文字体不可用，请在系统设置中选择具备嵌入许可的 TrueType .ttf/.ttc 文件；或清空路径使用标准中文字体引用。")
        try:
            name = "SPA_" + sha256(target.read_bytes()).hexdigest()[:20]
            if name not in pdfmetrics.getRegisteredFontNames():
                font = TTFont(name, str(target), validate=1)
                # ReportLab rejects restricted embedding in its TrueType parser.
                pdfmetrics.registerFont(font)
            return name
        except Exception as exc:
            raise DataError(f"中文字体无法嵌入：{exc}。请选择具有许可且包含所需中文的 TrueType 字体，或清空路径使用标准引用。") from exc


def ensure_glyphs(font_name, text):
    if font_name == "STSong-Light":
        missing = {c for c in text if ord(c) > 0xFFFF}
    else:
        mapping = pdfmetrics.getFont(font_name).face.charToGlyph
        missing = {c for c in text if not c.isspace() and ord(c) not in mapping}
    if missing:
        codes = "、".join(f"U+{ord(c):04X}" for c in sorted(missing)[:12])
        raise DataError(f"中文字体缺少报告所需字形（{codes}），未生成缺字报告；请在系统设置选择含这些字符且有嵌入许可的中文 TrueType 字体。")
