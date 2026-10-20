"""GUI-independent identity and stable time-order preparation."""

from dataclasses import dataclass
from hashlib import sha256

import numpy as np


def timestamp_parts(frame):
    times = frame["时间"].to_numpy()
    seconds = times.astype("datetime64[s]")
    fractions = (times - seconds).astype("timedelta64[ns]").astype("<i8")
    return times, seconds.astype("<i8"), fractions


def frame_fingerprint(frame):
    digest = sha256()
    _, seconds, fractions = timestamp_parts(frame)
    digest.update(seconds.tobytes())
    digest.update(fractions.tobytes())
    digest.update(frame[["电压", "电流", "功率因数"]].to_numpy(dtype="<f8").tobytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class PlotSamples:
    fingerprint: str
    order: np.ndarray
    seconds: np.ndarray
    origin: np.datetime64
    voltage: np.ndarray
    current: np.ndarray


def prepare_samples(frame):
    times, ticks, fractions = timestamp_parts(frame)
    order = np.argsort(times, kind="stable")
    origin = times[order[0]]
    # Relative seconds preserve subsecond precision near modern dates. Avoid int64
    # subtraction overflow for data spanning the whole supported datetime range.
    seconds = ((ticks[order] - ticks[order[0]]).astype(float)
               + (fractions[order] - fractions[order[0]]) / 1e9)
    arrays = [order, seconds, frame["电压"].to_numpy(copy=True), frame["电流"].to_numpy(copy=True)]
    for array in arrays:
        array.setflags(write=False)
    return PlotSamples(frame_fingerprint(frame), order, seconds, origin, arrays[2], arrays[3])
