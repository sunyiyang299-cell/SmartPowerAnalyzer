from dataclasses import dataclass
from pathlib import Path

from smartpower.data.validation import DataError
from smartpower.reporting.models import DEFAULT_TITLE, validate_title

PAGE_KEYS = ("home", "data", "voltage", "current", "power", "anomalies", "reports", "settings")


@dataclass(frozen=True)
class AppSettings:
    report_directory: str
    chart_directory: str
    report_title: str = DEFAULT_TITLE
    startup_page: str = "home"
    font_path: str = ""

    def validate(self):
        for name, value in (("默认报告目录", self.report_directory), ("默认图表目录", self.chart_directory)):
            if not isinstance(value, str) or not Path(value).is_absolute() or not Path(value).is_dir():
                raise DataError(f"{name}不存在或不是有效绝对目录，请选择已有目录；未自动创建目录。")
        validate_title(self.report_title)
        if self.startup_page not in PAGE_KEYS:
            raise DataError("启动页面设置无效。")
        if not isinstance(self.font_path, str):
            raise DataError("中文字体路径必须为文本。")
        if self.font_path and (not Path(self.font_path).is_file() or Path(self.font_path).suffix.lower() not in (".ttf", ".ttc")):
            raise DataError("中文字体文件不存在，请选择合法可嵌入的 .ttf/.ttc 字体，或清空以使用标准中文引用。")
        return self
