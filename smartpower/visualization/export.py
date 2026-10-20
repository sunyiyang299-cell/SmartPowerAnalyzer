"""Atomic PNG writing, separate from UI path selection and confirmation."""

import os
from pathlib import Path
import tempfile

from smartpower.data.validation import DataError


def save_png(image, path, *, overwrite=False):
    target = Path(path)
    if target.suffix.lower() != ".png":
        raise DataError("图表文件必须使用 .png 扩展名。")
    temporary = None
    try:
        if target.exists() and not overwrite:
            raise DataError("目标文件已存在，必须先确认覆盖。")
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".png", delete=False) as stream:
            temporary = Path(stream.name)
        if not image.save(str(temporary), "PNG"):
            raise DataError("PNG 图像编码或写入失败。")
        if overwrite:
            os.replace(temporary, target)
        else:
            # Exclusive creation prevents an intervening writer being overwritten.
            if os.name == "nt":
                os.rename(temporary, target)  # Windows rename fails if target exists.
            else:
                os.link(temporary, target)
                temporary.unlink()
        temporary = None
    except (OSError, ValueError) as exc:
        raise DataError(f"PNG 导出失败：{exc}。原文件保留，请检查目录和写入权限。") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
