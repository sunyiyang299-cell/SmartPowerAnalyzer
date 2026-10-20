"""Read a repository snapshot, then detect without changing SQLite data."""

from smartpower.anomaly.detector import detect_anomalies


def detect_saved_dataset(repository, dataset_id, thresholds):
    return detect_anomalies(repository.load(dataset_id), thresholds, dataset_id)
