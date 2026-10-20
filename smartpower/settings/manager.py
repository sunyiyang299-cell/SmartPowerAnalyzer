"""Versioned JSON in per-user config storage, never in the source tree."""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tempfile

from smartpower.data.validation import DataError
from smartpower.settings.models import AppSettings


@dataclass(frozen=True)
class LoadedSettings:
    value: AppSettings
    warning: str = ""


class SettingsManager:
    def __init__(self, path, default_directory):
        self.path = Path(path)
        self.defaults = AppSettings(str(Path(default_directory).resolve()), str(Path(default_directory).resolve()))

    def load(self):
        try:
            if not self.path.exists():
                return LoadedSettings(self.defaults)
            if self.path.stat().st_size > 65536:
                raise ValueError("设置文件异常过大")
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("version") != 1 or not isinstance(data.get("settings"), dict):
                raise ValueError("设置版本或结构不受支持")
            return LoadedSettings(AppSettings(**data["settings"]).validate())
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            return LoadedSettings(self.defaults, f"设置无法读取或已失效，暂用默认值：{exc}。原文件保留，点击保存才会替换。")

    def save(self, settings):
        settings.validate()
        temporary = None
        try:
            # Explicit Save/confirmed Restore authorizes this dedicated config
            # location. Export directories themselves are never created.
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             suffix=".json", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump({"version": 1, "settings": asdict(settings)}, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            temporary = None
        except (OSError, ValueError, TypeError) as exc:
            raise DataError(f"设置保存失败：{exc}。旧设置文件保留。") from exc
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
