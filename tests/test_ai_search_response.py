from tools._response import (
    build_markdown_summary,
    build_smart_search_payload,
    build_web_search_payload,
    normalize_search_results,
    normalize_smart_search_output,
)


def test_build_web_search_payload_clamps_top_k() -> None:
    payload = build_web_search_payload("北京天气", 99)
    assert payload["resource_type_filter"] == [{"type": "web", "top_k": 10}]


def test_build_smart_search_payload_uses_fixed_model() -> None:
    payload = build_smart_search_payload("北京天气", 3)
    assert payload["model"] == "ernie-5.0"
    assert payload["resource_type_filter"] == [{"type": "web", "top_k": 3}]


def test_normalize_search_results_keeps_stable_fields() -> None:
    payload = {
        "results": [
            {
                "title": "百度",
                "url": "https://www.baidu.com",
                "snippet": "搜索引擎",
                "source": "baidu.com",
            },
            {
                "name": "示例站点",
                "link": "https://example.com/article",
                "description": "示例摘要",
            },
            {
                "content": "只有内容",
            },
        ]
    }

    assert normalize_search_results(payload) == [
        {
            "title": "百度",
            "url": "https://www.baidu.com",
            "snippet": "搜索引擎",
            "source": "baidu.com",
        },
        {
            "title": "示例站点",
            "url": "https://example.com/article",
            "snippet": "示例摘要",
            "source": "example.com",
        },
        {
            "title": "未命名结果",
            "url": "",
            "snippet": "只有内容",
            "source": "",
        },
    ]


def test_build_markdown_summary_contains_citations() -> None:
    markdown = build_markdown_summary(
        "这是总结。",
        [
            {
                "title": "来源一",
                "url": "https://example.com/1",
                "snippet": "摘要一",
                "source": "example.com",
            }
        ],
    )

    assert "这是总结。" in markdown
    assert "[来源一](https://example.com/1)" in markdown


def test_normalize_smart_search_output_handles_chat_completion_shape() -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": "北京今日多云。",
                    "references": [
                        {
                            "title": "天气预报",
                            "url": "https://example.com/weather",
                            "snippet": "今天多云",
                            "source": "example.com",
                        }
                    ],
                }
            }
        ]
    }

    output = normalize_smart_search_output(payload)
    assert output["summary_markdown"].startswith("北京今日多云。")
    assert output["citations"] == [
        {
            "title": "天气预报",
            "url": "https://example.com/weather",
            "snippet": "今天多云",
            "source": "example.com",
        }
    ]
