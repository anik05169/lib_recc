"""Regression: Pinecone SDK dataclasses lack .get(); _field must support both."""

from types import SimpleNamespace

from app.services.pinecone_store import _field


def test_field_reads_dict():
    assert _field({"values": [1.0]}, "values") == [1.0]
    assert _field({}, "values", default=None) is None


def test_field_reads_dataclass_style_object():
    record = SimpleNamespace(values=[0.1, 0.2], id="41")
    assert _field(record, "values") == [0.1, 0.2]
    assert _field(record, "missing", default=7) == 7


def test_field_reads_openapi_style_get():
    class FakeOpenApi:
        def get(self, key, default=None):
            data = {"namespaces": {"catalog": {"vector_count": 3}}}
            return data.get(key, default)

    assert _field(FakeOpenApi(), "namespaces")["catalog"]["vector_count"] == 3
