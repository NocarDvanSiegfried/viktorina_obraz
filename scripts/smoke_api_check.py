#!/usr/bin/env python3
"""Smoke-test all major API endpoints against a running backend (local or prod)."""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

DEFAULT_BASE = os.getenv("SMOKE_API_URL", os.getenv("API_URL", "http://127.0.0.1:8000"))
TIMEOUT = 120.0
_REPO_ROOT = Path(__file__).resolve().parents[1]


def ok(name: str, cond: bool, detail: str = "") -> tuple[bool, str]:
    status = "OK " if cond else "FAIL"
    line = f"  [{status}] {name}" + (f" — {detail}" if detail else "")
    print(line)
    return cond, line


def check_export_headers(response: httpx.Response, kind: str) -> bool:
    content_type = (response.headers.get("content-type") or "").lower()
    disposition = (response.headers.get("content-disposition") or "").lower()

    if kind == "pdf":
        type_ok = "pdf" in content_type
    else:
        type_ok = (
            "officedocument" in content_type
            or "wordprocessingml" in content_type
            or "octet-stream" in content_type
        )

    disposition_ok = "attachment" in disposition or "filename" in disposition
    return type_ok and disposition_ok


def run_smoke(base_url: str) -> tuple[int, int, list[str]]:
    owner = f"smoke-{uuid.uuid4()}"
    base = base_url.rstrip("/")
    results: list[bool] = []
    log_lines: list[str] = []

    print(f"API smoke test -> {base}\n")

    with httpx.Client(base_url=base, timeout=TIMEOUT) as client:
        r = client.get("/health")
        passed, line = ok(
            "GET /health",
            r.status_code == 200 and r.json().get("status") == "ok",
        )
        results.append(passed)
        log_lines.append(line)

        gen = client.post(
            "/quiz/generate-from-materials",
            data={
                "owner_id": owner,
                "subject": "Biology",
                "grade": "8",
                "topic": "Cell",
                "question_count": "2",
                "difficulty": "easy",
                "question_types": ["single_choice", "true_false"],
                "source_text": (
                    "The cell is the basic unit of life. "
                    "The membrane protects the cell contents."
                ),
            },
        )
        passed, line = ok(
            "POST /quiz/generate-from-materials",
            gen.status_code == 200,
            f"{gen.status_code} {gen.text[:120] if gen.status_code != 200 else ''}",
        )
        results.append(passed)
        log_lines.append(line)

        if gen.status_code != 200:
            print("\nAbort: generation failed (check GIGACHAT_AUTH_KEY / E2E_MOCK).")
            return sum(results), len(results), log_lines, None

        body = gen.json()
        quiz_id = body["quiz_id"]
        questions = body.get("questions", [])
        passed, line = ok(
            "Generation returned questions",
            len(questions) >= 1,
            f"count={len(questions)}",
        )
        results.append(passed)
        log_lines.append(line)

        lst = client.get("/quiz/list", params={"owner_id": owner})
        passed, line = ok(
            "GET /quiz/list",
            lst.status_code == 200 and len(lst.json().get("quizzes", [])) >= 1,
        )
        results.append(passed)
        log_lines.append(line)

        detail = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner})
        passed, line = ok("GET /quiz/{id}", detail.status_code == 200)
        results.append(passed)
        log_lines.append(line)
        detail_body = detail.json() if detail.status_code == 200 else {}
        fragments = detail_body.get("fragments") or []
        passed, line = ok(
            "fragments catalog with preview",
            len(fragments) >= 1 and bool((fragments[0] or {}).get("preview")),
            f"count={len(fragments)}",
        )
        results.append(passed)
        log_lines.append(line)
        qid = detail_body.get("questions", [{}])[0].get("id", "")

        put = client.put(
            f"/quiz/{quiz_id}",
            data={
                "owner_id": owner,
                "title": "Smoke Quiz Updated",
                "difficulty": "medium",
                "full_time_seconds": "60",
                "question_time_seconds": "30",
                "max_attempts": "2",
                "status": "draft",
            },
        )
        passed, line = ok("PUT /quiz/{id}", put.status_code == 200)
        results.append(passed)
        log_lines.append(line)
        passed, line = ok(
            "updated_at in response",
            bool(put.json().get("updated_at")),
        )
        results.append(passed)
        log_lines.append(line)

        pdf = client.get(f"/quiz/{quiz_id}/export-pdf", params={"owner_id": owner})
        pdf_ok = pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
        passed, line = ok(
            "GET /quiz/{id}/export-pdf",
            pdf_ok,
            f"{len(pdf.content)} bytes",
        )
        results.append(passed)
        log_lines.append(line)
        passed, line = ok(
            "PDF Content-Type/Disposition",
            pdf_ok and check_export_headers(pdf, "pdf"),
            (pdf.headers.get("content-type") or "")[:60],
        )
        results.append(passed)
        log_lines.append(line)

        docx = client.get(f"/quiz/{quiz_id}/export-docx", params={"owner_id": owner})
        docx_ok = docx.status_code == 200 and docx.content[:2] == b"PK"
        passed, line = ok(
            "GET /quiz/{id}/export-docx",
            docx_ok,
            f"{len(docx.content)} bytes",
        )
        results.append(passed)
        log_lines.append(line)
        passed, line = ok(
            "DOCX Content-Type/Disposition",
            docx_ok and check_export_headers(docx, "docx"),
            (docx.headers.get("content-type") or "")[:60],
        )
        results.append(passed)
        log_lines.append(line)

        regen = client.post(
            f"/quiz/{quiz_id}/questions/{qid}/regenerate",
            data={"owner_id": owner},
        )
        passed, line = ok(
            "POST .../regenerate",
            regen.status_code == 200,
            f"{regen.status_code}",
        )
        results.append(passed)
        log_lines.append(line)

        versions = client.get(f"/quiz/{quiz_id}/versions", params={"owner_id": owner})
        passed, line = ok("GET /quiz/{id}/versions", versions.status_code == 200)
        results.append(passed)
        log_lines.append(line)
        version_items = versions.json().get("versions", []) if versions.status_code == 200 else []
        passed, line = ok(
            "versions list not empty",
            len(version_items) >= 1,
            f"count={len(version_items)}",
        )
        results.append(passed)
        log_lines.append(line)
        if version_items:
            vid = version_items[-1]["id"]
            vdetail = client.get(
                f"/quiz/{quiz_id}/versions/{vid}",
                params={"owner_id": owner},
            )
            passed, line = ok(
                "GET /quiz/{id}/versions/{vid}",
                vdetail.status_code == 200,
            )
            results.append(passed)
            log_lines.append(line)

        start = client.post(
            "/student/start",
            data={"quiz_id": quiz_id, "student_name": "Smoke Student"},
        )
        passed, line = ok("POST /student/start", start.status_code == 200)
        results.append(passed)
        log_lines.append(line)
        result_id = start.json()["result_id"]

        answered = 0
        nq = client.get("/student/questions", params={"result_id": result_id}).json().get(
            "next_question"
        )
        passed, line = ok("next_question present", nq is not None)
        results.append(passed)
        log_lines.append(line)

        while nq:
            opts = nq.get("options", [])
            pick = nq.get("correct_answers") or (opts[:1] if opts else [])
            if nq.get("question_type") == "multiple_choice" and len(opts) >= 2:
                pick = opts[:2]
            ans = client.post(
                "/student/answer",
                data={
                    "result_id": result_id,
                    "question_id": nq["id"],
                    "selected_options": pick,
                    "question_started_at": "2026-01-01T12:00:00+00:00",
                    "answered_at": "2026-01-01T12:00:05+00:00",
                },
            )
            if ans.status_code != 200:
                passed, line = ok(
                    "POST /student/answer",
                    False,
                    f"{ans.status_code} {ans.text[:80]}",
                )
                results.append(passed)
                log_lines.append(line)
                break
            answered += 1
            nq = client.get("/student/questions", params={"result_id": result_id}).json().get(
                "next_question"
            )

        passed, line = ok(
            "POST /student/answer (all)",
            answered >= 1,
            f"answered={answered}",
        )
        results.append(passed)
        log_lines.append(line)

        fin = client.post(
            "/student/finish",
            data={
                "result_id": result_id,
                "finished_at": "2026-01-01T12:01:00+00:00",
            },
        )
        passed, line = ok("POST /student/finish", fin.status_code == 200)
        results.append(passed)
        log_lines.append(line)
        fin_body = fin.json()
        passed, line = ok(
            "finish shows score",
            "score" in fin_body and "percent" in fin_body,
            f"{fin_body.get('score')}/{fin_body.get('max_score')} ({fin_body.get('percent')}%)",
        )
        results.append(passed)
        log_lines.append(line)

        res = client.get(f"/quiz/{quiz_id}/results", params={"owner_id": owner})
        passed, line = ok("GET /quiz/{id}/results", res.status_code == 200)
        results.append(passed)
        log_lines.append(line)
        passed, line = ok(
            "results list attempts",
            len(res.json().get("results", [])) >= 1,
        )
        results.append(passed)
        log_lines.append(line)

        forbidden = client.get(f"/quiz/{quiz_id}", params={"owner_id": "other-owner"})
        passed, line = ok("403 wrong owner", forbidden.status_code == 403)
        results.append(passed)
        log_lines.append(line)

    passed_count = sum(results)
    total = len(results)
    print(f"\n{passed_count}/{total} checks passed")
    meta = None
    if gen.status_code == 200:
        meta = {"quiz_id": quiz_id, "owner_id": owner}
    return passed_count, total, log_lines, meta


def write_report(
    path: Path,
    *,
    base_url: str,
    passed: int,
    total: int,
    lines: list[str],
    frontend_url: str = "",
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status = "PASSED" if passed == total else "FAILED"
    body = [
        "# Production smoke report",
        "",
        f"- **Date:** {now}",
        f"- **API base:** `{base_url}`",
        f"- **Frontend:** `{frontend_url or '(not checked)'}`",
        f"- **Result:** **{status}** ({passed}/{total} API checks)",
        "",
        "## API checks",
        "",
        "```text",
        *lines,
        "```",
        "",
        "## Jury demo checklist",
        "",
        "| Step | OK |",
        "|------|-----|",
        "| Create quiz (text or file) | ☐ |",
        "| Edit + versions | ☐ |",
        "| Student attempt + score | ☐ |",
        "| Results page | ☐ |",
        "| PDF + DOCX download | ☐ |",
        "| Teacher fullscreen | ☐ |",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="API smoke test for viktorina backend.")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE,
        help="Backend base URL (or SMOKE_API_URL / API_URL env)",
    )
    parser.add_argument(
        "--report",
        default="",
        help="Write markdown report to this path (e.g. docs/PROD_SMOKE_REPORT.md)",
    )
    parser.add_argument(
        "--frontend-url",
        default=os.getenv("FRONTEND_URL", os.getenv("PUBLIC_FRONTEND_URL", "")),
        help="Optional frontend URL for report header",
    )
    args = parser.parse_args(argv)
    args.base_url = args.base_url.rstrip("/")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    passed, total, lines, _meta = run_smoke(args.base_url)

    if args.report:
        write_report(
            Path(args.report),
            base_url=args.base_url.rstrip("/"),
            passed=passed,
            total=total,
            lines=lines,
            frontend_url=args.frontend_url,
        )
        print(f"\nReport written: {args.report}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
