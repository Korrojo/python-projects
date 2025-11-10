import json
from pathlib import Path
from types import SimpleNamespace

import pytest


class FakeCollection:
    def __init__(self, store):
        self._store = store

    def insert_many(self, docs):
        # Simulate insert and return inserted_ids
        self._store.extend(docs)
        return SimpleNamespace(inserted_ids=[i for i, _ in enumerate(docs)])

    def find(self, query):
        ts = query.get("_batch_ts")
        if ts is None:
            return list(self._store)
        return [d for d in self._store if d.get("_batch_ts") == ts]


class FakeDB:
    def __init__(self, store):
        self._store = store

    def __getitem__(self, name):
        return FakeCollection(self._store)


class FakeMongoConn:
    def __init__(self, cfg):
        self._db = FakeDB([])

    def connect(self):
        return None

    def test_connection(self):
        return {"connected": True}

    def get_database(self):
        return self._db

    def disconnect(self):
        return None


class FakePaths(SimpleNamespace):
    pass


class FakeSettings(SimpleNamespace):
    def ensure_dirs(self):
        self.paths.data_input.mkdir(parents=True, exist_ok=True)
        self.paths.data_output.mkdir(parents=True, exist_ok=True)
        self.paths.logs.mkdir(parents=True, exist_ok=True)


@pytest.mark.integration
def test_sample_project_happy_path(monkeypatch, tmp_path: Path):
    # Arrange fake settings and paths under tmp
    data_in = tmp_path / "data" / "input"
    data_out = tmp_path / "data" / "output"
    logs = tmp_path / "logs"

    settings = FakeSettings(
        mongodb_uri="mongodb://fake:27017",
        database_name="FakeDB",
        paths=FakePaths(data_input=data_in, data_output=data_out, logs=logs),
        sample_collection_name="AD_test_YYYYMMDD",
        sample_input_csv=None,
    )

    # Prepare input CSV under shared path
    input_dir = data_in / "sample_project"
    input_dir.mkdir(parents=True, exist_ok=True)
    input_csv = input_dir / "sample_input.csv"
    input_csv.write_text("Id,Name,Email\n1,Alice,a@x.com\n2,Bob,b@x.com\n3,Carol,c@x.com\n", encoding="utf-8")

    # Import sample_project (conftest.py handles sys.path setup)
    import sample_project.run as sp_run

    # Monkeypatch get_settings and MongoDBConnection in the module under test
    monkeypatch.setattr(sp_run, "get_settings", lambda: settings)
    monkeypatch.setattr(sp_run, "MongoDBConnection", FakeMongoConn)

    # Act
    sp_run.main()

    # Assert: one json file created in data/output/sample_project
    project_out_dir = data_out / "sample_project"
    assert project_out_dir.exists()
    json_files = list(project_out_dir.glob("*_inserted.json"))
    assert len(json_files) == 1

    payload = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert len(payload) == 3
    # batch metadata is attached
    assert all("_batch_ts" in d for d in payload)
