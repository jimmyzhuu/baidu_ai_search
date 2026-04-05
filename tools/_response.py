from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


DEFAULT_TOP_K = 5
MAX_TOP_K = 10


def sanitize_top_k(value: Any) -> int:
    try:
        top_k = int(value)
    except (TypeError, ValueError):
        return DEFAULT_TOP_K

    return max(1, min(MAX_TOP_K, top_k))


def build_web_search_payload(query: str, top_k: Any) -> dict[str, Any]:
    return {
        "messages": [
            {
                "content": query,
                "role": "user",
            }
        ],
        "search_source": "baidu_search_v2",
        "resource_type_filter": [
            {
                "type": "web",
                "top_k": sanitize_top_k(top_k),
            }
        ],
    }


def build_smart_search_payload(query: str, top_k: Any) -> dict[str, Any]:
    return {
        "messages": [
            {
                "content": query,
                "role": "user",
            }
        ],
        "model": "ernie-5.0",
        "resource_type_filter": [
            {
                "type": "web",
                "top_k": sanitize_top_k(top_k),
            }
        ],
    }


def _extract_string(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text.strip())
        return "\n".join(part for part in parts if part).strip()
    return ""


def _iter_candidate_lists(payload: Any) -> list[list[Any]]:
    candidate_lists: list[list[Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, list):
            if value and all(isinstance(item, dict) for item in value):
                candidate_lists.append(value)
            for item in value:
                if isinstance(item, (dict, list)):
                    visit(item)
        elif isinstance(value, dict):
            for key in (
                "results",
                "items",
                "data",
                "result",
                "references",
                "citations",
                "search_results",
                "documents",
                "message",
                "choices",
            ):
                if key in value:
                    visit(value[key])

    visit(payload)
    return candidate_lists


def _first_non_empty(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _infer_source(url: str) -> str:
    if not url:
        return ""
    return urlparse(url).netloc


def normalize_search_results(payload: Any) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for candidate_list in _iter_candidate_lists(payload):
        for item in candidate_list:
            if not isinstance(item, dict):
                continue

            title = _first_non_empty(item, ("title", "name", "page_title"))
            url = _first_non_empty(item, ("url", "link", "source_url", "page_url"))
            snippet = _first_non_empty(item, ("snippet", "summary", "description", "content", "text", "abstract"))
            source = _first_non_empty(item, ("source", "site_name", "display_source", "domain", "hostname"))
            source = source or _infer_source(url)

            if not any((title, url, snippet, source)):
                continue

            if not title:
                title = source or url or "未命名结果"

            row = {
                "title": title,
                "url": url,
                "snippet": snippet,
                "source": source,
            }
            signature = (row["title"], row["url"], row["snippet"])
            if signature in seen:
                continue
            seen.add(signature)
            normalized.append(row)

    return normalized


def extract_summary(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("summary", "answer", "result", "output_text", "text", "content"):
            value = payload.get(key)
            text = _extract_string(value)
            if text:
                return text
            if isinstance(value, dict):
                nested_text = extract_summary(value)
                if nested_text:
                    return nested_text

        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict):
                    text = _extract_string(message.get("content"))
                    if text:
                        return text

        data = payload.get("data")
        if isinstance(data, dict):
            return extract_summary(data)

    return ""


def build_markdown_summary(summary: str, citations: list[dict[str, str]]) -> str:
    clean_summary = summary.strip() or "未检索到可总结的内容。"
    if not citations:
        return clean_summary

    citation_lines = []
    for index, item in enumerate(citations, start=1):
        title = item["title"] or item["source"] or item["url"] or f"来源 {index}"
        if item["url"]:
            citation_lines.append(f"{index}. [{title}]({item['url']})")
        else:
            citation_lines.append(f"{index}. {title}")

    return f"{clean_summary}\n\n参考来源\n" + "\n".join(citation_lines)


def normalize_smart_search_output(payload: Any) -> dict[str, Any]:
    citations = normalize_search_results(payload)
    summary = extract_summary(payload)
    return {
        "summary_markdown": build_markdown_summary(summary, citations),
        "citations": citations,
    }
