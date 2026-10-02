from pathlib import Path

import pytest

from app.extraction.spike import load_dataset, load_fixture_adapter


DATASET_DIR = Path(__file__).resolve().parents[5] / "data" / "extraction_spike"


@pytest.fixture(scope="session")
def dataset_dir():
    return DATASET_DIR


@pytest.fixture(scope="session")
def dataset(dataset_dir):
    return load_dataset(dataset_dir)


@pytest.fixture(scope="session")
def adapter(dataset_dir, dataset):
    return load_fixture_adapter(dataset_dir, dataset)


@pytest.fixture
def result(dataset, adapter):
    return adapter.extract(dataset.cases[0].bundle, dataset.schema_version)
