"""Day 16: quiz version history — list, detail, restore."""

from unittest.mock import patch

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Version Quiz",
  "subject": "Biology",
  "grade": "8",
  "topic": "Cell",
  "questions": [
    {
      "type": "single_choice",
      "text": "Original question?",
      "options": ["A", "B", "C", "D"],
      "correct_answers": ["A"],
      "explanation": "A",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""


def _generate_quiz(client, owner_id: str) -> str:
    response = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "Biology",
            "grade": "8",
            "topic": "Cell",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "Cell basics for version test.",
        },
    )
    assert response.status_code == 200
    return response.json()["quiz_id"]


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_version_created_on_generate(_mock_chat, client):
    owner_id = "owner-day16-gen"
    quiz_id = _generate_quiz(client, owner_id)

    listed = client.get(f"/quiz/{quiz_id}/versions", params={"owner_id": owner_id})
    assert listed.status_code == 200
    versions = listed.json()["versions"]
    assert len(versions) >= 1
    assert versions[0]["version_number"] == 1
    assert versions[0]["label"]


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_versions_increment_on_settings_update(_mock_chat, client):
    owner_id = "owner-day16-inc"
    quiz_id = _generate_quiz(client, owner_id)

    client.put(
        f"/quiz/{quiz_id}",
        data={
            "owner_id": owner_id,
            "title": "Version Quiz v2",
            "difficulty": "medium",
            "full_time_seconds": "0",
            "question_time_seconds": "0",
            "max_attempts": "1",
            "status": "draft",
        },
    )

    listed = client.get(f"/quiz/{quiz_id}/versions", params={"owner_id": owner_id})
    numbers = [v["version_number"] for v in listed.json()["versions"]]
    assert numbers == sorted(numbers, reverse=True)
    assert max(numbers) >= 2


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_list_versions_403_wrong_owner(_mock_chat, client):
    owner_id = "owner-day16-403"
    quiz_id = _generate_quiz(client, owner_id)

    forbidden = client.get(
        f"/quiz/{quiz_id}/versions",
        params={"owner_id": "other-owner"},
    )
    assert forbidden.status_code == 403


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_restore_reverts_question_and_settings(_mock_chat, client):
    owner_id = "owner-day16-restore"
    quiz_id = _generate_quiz(client, owner_id)

    detail_before = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id}).json()
    question_id = detail_before["questions"][0]["id"]
    original_text = detail_before["questions"][0]["question_text"]
    original_title = detail_before["title"]

    client.put(
        f"/quiz/{quiz_id}",
        data={
            "owner_id": owner_id,
            "title": "Changed title",
            "difficulty": "hard",
            "full_time_seconds": "120",
            "question_time_seconds": "30",
            "max_attempts": "2",
            "status": "published",
        },
    )

    client.put(
        f"/quiz/{quiz_id}/questions/{question_id}",
        data={
            "owner_id": owner_id,
            "question_text": "Completely new text?",
            "question_type": "single_choice",
            "answers": ["X", "Y", "Z", "W"],
            "correct_answers": ["X"],
            "explanation": "X",
            "source_fragment": "manual_1",
        },
    )

    versions = client.get(
        f"/quiz/{quiz_id}/versions", params={"owner_id": owner_id}
    ).json()["versions"]
    first_version = next(v for v in versions if v["version_number"] == 1)

    restored = client.post(
        f"/quiz/{quiz_id}/versions/{first_version['id']}/restore",
        data={"owner_id": owner_id},
    )
    assert restored.status_code == 200
    body = restored.json()
    assert body["title"] == original_title
    assert body["questions"][0]["question_text"] == original_text


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_get_version_detail_includes_snapshot_summary(_mock_chat, client):
    owner_id = "owner-day16-detail"
    quiz_id = _generate_quiz(client, owner_id)

    versions = client.get(
        f"/quiz/{quiz_id}/versions", params={"owner_id": owner_id}
    ).json()["versions"]
    version_id = versions[0]["id"]

    detail = client.get(
        f"/quiz/{quiz_id}/versions/{version_id}",
        params={"owner_id": owner_id},
    )
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["version_number"] == versions[0]["version_number"]
    assert payload["snapshot"]["quiz"]["title"]
    assert len(payload["snapshot"]["questions"]) >= 1
