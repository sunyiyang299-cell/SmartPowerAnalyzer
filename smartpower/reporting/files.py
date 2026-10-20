"""Atomic report publication; exporters never touch the original target first."""

from contextlib import contextmanager
import os
from pathlib import Path
import tempfile

from smartpower.data.validation import DataError


@contextmanager
def atomic_report(path, suffix, *, overwrite=False):
    target = Path(path)
    if target.suffix.lower() != suffix:
        raise DataError(f"报告文件必须使用 {suffix} 扩展名。")
    if not target.parent.is_dir():
        raise DataError("保存目录不存在，请选择已有目录；未自动创建目录。")
    temporary = None
    try:
        if target.exists() and not overwrite:
            raise DataError("报告文件已存在，请先确认覆盖。")
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=suffix, delete=False) as stream:
            temporary = Path(stream.name)
        yield temporary
        if not temporary.stat().st_size:
            raise DataError("报告为空，未发布文件。")
        if overwrite:
            os.replace(temporary, target)
        elif os.name == "nt":
            os.rename(temporary, target)
        else:
            os.link(temporary, target)
            temporary.unlink()
        temporary = None
    except DataError:
        raise
    except Exception as exc:
        raise DataError(f"报告导出失败：{exc}。已有文件未被本次失败写入替换。") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
