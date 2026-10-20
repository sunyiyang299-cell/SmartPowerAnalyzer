"""Calendar labels for local, timezone-free sampling times (no DST conversion)."""

import numpy as np
import pyqtgraph as pg


class SampleTimeAxis(pg.AxisItem):
    def __init__(self):
        super().__init__(orientation="bottom")
        self.origin = None
        self.setLabel("采样时间（本地无时区）")
        self.enableAutoSIPrefix(False)

    def tickStrings(self, values, scale, spacing):
        if self.origin is None:
            return [""] * len(values)
        labels = []
        for value in values:
            try:
                # Calendar formatting via datetime64 avoids system timezone/epoch limits.
                stamp = self.origin.astype("datetime64[ms]") + np.timedelta64(round(value * 1000), "ms")
                labels.append(np.datetime_as_string(stamp, unit="ms").replace("T", "\n")
                              if spacing < 1 else np.datetime_as_string(stamp, unit="s").replace("T", "\n"))
            except (ValueError, OverflowError):
                labels.append("")
        return labels
