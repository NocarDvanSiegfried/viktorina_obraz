"""Build and parse source-fragment catalogs for quiz transparency (day 21)."""

from __future__ import annotations

import json
import re

from app.core.config import settings
from app.schemas.material import SourceFragment

_PREVIEW_SUFFIX = "…"
_WHITESPACE_RE = re.compile(r"\s+")


def make_preview(text: str, *, max_chars: int | None = None) -> str:
    limit = max_chars if max_chars is not None else settings.SOURCE_FRAGMENT_PREVIEW_MAX_CHARS
    cleaned = _WHITESPACE_RE.sub(" ", (text or "").strip())
    if not cleaned:
        return ""
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(1, limit - 1)].rstrip() + _PREVIEW_SUFFIX


def infer_source_type(fragment_id: str) -> str:
    fid = (fragment_id or "").strip()
    if fid.startswith("image_ocr_"):
        return "image"
    if fid.startswith("pdf_ocr_"):
        return "pdf"
    if fid.startswith("pdf_page_"):
        return "pdf"
    if fid.startswith("docx_chunk_"):
        return "docx"
    if fid.startswith("pptx_slide_"):
        return "pptx"
    if fid.startswith("txt_"):
        return "txt"
    if fid == "manual_1" or fid.startswith("manual_"):
        return "manual_text"
    return "unknown"


def build_catalog(
    fragments: list[SourceFragment],
    *,
    max_chars: int | None = None,
) -> list[dict[str, str]]:
    catalog: list[dict[str, str]] = []
    seen: set[str] = set()
    for fragment in fragments:
        fragment_id = fragment.fragment_id.strip()
        if not fragment_id or fragment_id in seen:
            continue
        seen.add(fragment_id)
        catalog.append(
            {
                "id": fragment_id,
                "preview": make_preview(fragment.text, max_chars=max_chars),
                "source_type": fragment.source_type or infer_source_type(fragment_id),
            }
        )
    return catalog


def catalog_to_json(catalog: list[dict[str, str]]) -> str:
    return json.dumps(catalog, ensure_ascii=False)


def parse_catalog_json(raw: str | None) -> list[dict[str, str]]:
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    catalog: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        fragment_id = str(item.get("id") or "").strip()
        if not fragment_id:
            continue
        catalog.append(
            {
                "id": fragment_id,
                "preview": str(item.get("preview") or ""),
                "source_type": str(item.get("source_type") or infer_source_type(fragment_id)),
            }
        )
    return catalog


def fallback_from_questions(questions: list) -> list[dict[str, str]]:
    catalog: list[dict[str, str]] = []
    seen: set[str] = set()
    for question in questions:
        fragment_id = (getattr(question, "source_fragment", None) or "").strip()
        if not fragment_id or fragment_id in seen:
            continue
        seen.add(fragment_id)
        catalog.append(
            {
                "id": fragment_id,
                "preview": "",
                "source_type": infer_source_type(fragment_id),
            }
        )
    return catalog


def resolve_catalog(quiz, questions: list) -> list[dict[str, str]]:
    stored = parse_catalog_json(getattr(quiz, "source_fragments_json", None))
    if stored:
        return stored
    return fallback_from_questions(questions)


def find_fragment(catalog: list[dict[str, str]], fragment_id: str) -> dict[str, str] | None:
    target = (fragment_id or "").strip()
    if not target:
        return None
    for item in catalog:
        if item.get("id") == target:
            return item
    return None
