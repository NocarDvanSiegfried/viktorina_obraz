"""Day 21: fragment catalog preview helpers."""

from app.schemas.material import SourceFragment
from app.services import fragment_catalog_service as svc


def test_make_preview_truncates_long_text():
    text = "а" * 300
    preview = svc.make_preview(text, max_chars=50)
    assert len(preview) <= 51
    assert preview.endswith("…")


def test_serialize_catalog_from_fragments():
    fragments = [
        SourceFragment(
            fragment_id="manual_1",
            source_type="manual_text",
            source_name="teacher_input",
            text="Клетка — основная единица жизни. " * 10,
        ),
        SourceFragment(
            fragment_id="txt_1",
            source_type="txt",
            source_name="notes.txt",
            text="Короткий фрагмент",
        ),
    ]
    catalog = svc.build_catalog(fragments, max_chars=40)
    assert len(catalog) == 2
    assert catalog[0]["id"] == "manual_1"
    assert catalog[0]["source_type"] == "manual_text"
    assert "Клетка" in catalog[0]["preview"]
    assert len(catalog[0]["preview"]) <= 41
    assert catalog[1]["preview"] == "Короткий фрагмент"


def test_parse_and_roundtrip_json():
    catalog = [{"id": "manual_1", "preview": "abc", "source_type": "manual_text"}]
    raw = svc.catalog_to_json(catalog)
    restored = svc.parse_catalog_json(raw)
    assert restored == catalog


def test_fallback_from_questions_unique_ids():
    class Q:
        source_fragment = "pdf_page_1_chunk_1"

    catalog = svc.fallback_from_questions([Q(), Q()])
    assert len(catalog) == 1
    assert catalog[0]["id"] == "pdf_page_1_chunk_1"
    assert catalog[0]["source_type"] == "pdf"
    assert catalog[0]["preview"] == ""
