# 百度 AI 搜索

这是一个面向 Dify 的百度 AI 搜索工具插件，目标是给 Agent 一条“开箱即用”的百度外部信息补充路径。

首发只保留两个工具：

- `web_search`
- `smart_search`

## 使用方式

1. 到百度千帆控制台创建 `API Key`
2. 在 Dify 中安装插件
3. 只填写一个凭据：`api_key`
4. 在 Agent 或工作流工具节点中直接调用

获取 API Key：
[百度千帆 AI Search API Key](https://console.bce.baidu.com/qianfan/ais/console/apiKey)

## 工具说明

### web_search

用于直接查网页结果，返回固定结构：

- `title`
- `url`
- `snippet`
- `source`

适合：

- 查最新网页信息
- 给 Agent 提供可追溯链接
- 做轻量检索补充

### smart_search

用于做“搜索 + 总结”，返回两个字段：

- `summary_markdown`
- `citations`

适合：

- 给 Agent 提供一段可直接复用的总结
- 同时保留引用来源，方便后续追溯

## 参数设计

两个工具都只保留最小参数：

- `query`
- `top_k`

默认只查网页结果，避免暴露过多底层选项。
