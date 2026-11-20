"""ツールのテスト（LLMもAPIキーも使わない）。"""

import json

from app import tools
from app import retrieval


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"{t['id']} の related に存在しない id: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "lecNN-start タグ"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("エージェント"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "見つかりませんでした" in tools.search_glossary("存在しない用語xyz")


def test_lecture_summary():
    assert "エージェント" in tools.get_lecture_summary(3)
    assert "まだありません" in tools.get_lecture_summary(99)


def test_search_with_neighbors_adds_adjacent_pages_without_duplicates(monkeypatch):
    hit = {
        "page_id": "lec02-main-p052",
        "document_id": "lec02-main",
        "page": 52,
        "distance": 0.1,
    }
    pages = [
        {"page_id": "lec02-main-p051", "document_id": "lec02-main", "page": 51, "content": "p51"},
        {"page_id": "lec02-main-p052", "document_id": "lec02-main", "page": 52, "content": "p52"},
        {"page_id": "lec02-main-p053", "document_id": "lec02-main", "page": 53, "content": "p53"},
    ]
    monkeypatch.setattr(retrieval, "search", lambda query: [hit])
    monkeypatch.setattr(retrieval, "load_pages", lambda source: pages)

    results = retrieval.search_with_neighbors("LoRA")

    assert [result["page"] for result in results] == [51, 52, 53]
    assert [result["neighbor_relation"] for result in results] == ["previous", "hit", "next"]
    assert len({result["page_id"] for result in results}) == 3


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
