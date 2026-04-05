"""Web search tool for Baidu AI Search."""

from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._response import build_web_search_payload, normalize_search_results

WEB_SEARCH_API_URL = "https://qianfan.baidubce.com/v2/ai_search/web_search"
REQUEST_TIMEOUT = (10, 60)


class BaiduWebSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        query = str(tool_parameters.get("query") or "").strip()
        if not query:
            yield self.create_text_message("搜索查询不能为空。")
            return

        api_key = str(self.runtime.credentials.get("api_key") or "").replace("Bearer", "").strip()
        if not api_key:
            yield self.create_text_message("未配置有效的 API Key。")
            return

        headers = {
            "Content-Type": "application/json",
            "X-Appbuilder-Authorization": f"Bearer {api_key}",
            "X-Appbuilder-From": "dify",
        }
        payload = build_web_search_payload(query, tool_parameters.get("top_k"))

        try:
            response = requests.post(WEB_SEARCH_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            yield self.create_text_message("百度 AI 搜索请求超时，请稍后重试。")
            return
        except requests.exceptions.HTTPError:
            status_code = response.status_code
            if status_code in (401, 403):
                yield self.create_text_message("百度 AI 搜索鉴权失败，请检查 API Key 是否正确。")
            elif status_code >= 500:
                yield self.create_text_message("百度 AI 搜索服务暂时不可用，请稍后重试。")
            else:
                yield self.create_text_message(f"百度 AI 搜索请求失败，状态码：{status_code}。")
            return
        except requests.exceptions.RequestException as exc:
            yield self.create_text_message(f"百度 AI 搜索请求失败：{exc}")
            return

        yield self.create_json_message({"results": normalize_search_results(response.json())})
