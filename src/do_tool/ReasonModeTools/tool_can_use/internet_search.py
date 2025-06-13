import json

from src.do_tool.ReasonModeTools.tool_can_use.base_tool import BaseTool, logger
import requests
from src.common.logger import get_module_logger
from ....plugins.config.config import global_config


class InternetSearchTool(BaseTool):
    """互联网搜索工具"""

    logger = get_module_logger("网络搜索工具")

    name = "internet_search"
    description = "通过API执行互联网搜索并返回结果"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "用户的搜索词"},
            "count": {"type": "int", "description": f"搜索数量，搜索数量不要超过{global_config.max_search_results}"},
            "freshness": {
                "type": "string",
                "description": "搜索时间范围，可选值：oneDay, oneWeek, oneMonth, oneYear, noLimit（默认）",
            },
        },
        "required": ["query"],
    }

    # def _decide_search_count(self, ):

    async def execute(self, function_args: dict, message_txt: str = "") -> dict:
        """执行互联网搜索

        Args:
            function_args: 工具参数，包含query（搜索词）、count（搜索数量）和freshness（搜索时间范围）
            message_txt: 原始消息文本，此工具不使用

        Returns:
            Dict: 搜索结果
        """
        api_url = "https://api.bochaai.com/v1/ai-search"
        headers = {
            "Authorization": "Bearer sk-be376e2fe720435987804fb2b6ca5149",
            "Content-Type": "application/json",
        }
        count = min(function_args.get("count"), global_config.max_search_results)
        freshness = function_args.get("freshness", "noLimit")
        valid_freshness_values = {"oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"}
        if freshness not in valid_freshness_values:
            self.logger.warning(f"无效的freshness值: {freshness}，已设置为noLimit")
            freshness = "noLimit"

        payload = {
            "query": function_args.get("query"),
            "freshness": freshness,
            "count": count,
            "answer": False,
            "stream": False,
        }

        logger.info(f"执行联网搜索，搜索数量为{count}")
        logger.info(f"执行联网搜索，时间参数为{freshness}")

        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = json.loads(response.text)

            summaries = []

            # 遍历所有消息
            for message in data.get("messages", []):
                if (
                    message.get("type") == "source"
                    and message.get("content_type") == "webpage"
                    and "content" in message
                ):
                    # 使用JSON解析内容而非正则表达式
                    try:
                        content_json = json.loads(message["content"])
                        # 提取value数组中的summary字段
                        if "value" in content_json:
                            for item in content_json["value"]:
                                if "summary" in item:
                                    summaries.append(item["summary"])
                    except json.JSONDecodeError:
                        self.logger.warning(f"无法解析消息内容为JSON: {message['content']}")
                        continue

            result = {
                "name": "internet_search",
                "content": {"summaries": summaries},
            }
            # self.logger.info(f"搜索成功: {result}")
            return result
        else:
            error_message = f"Error: {response.status_code}, {response.text}"
            self.logger.info(f"搜索失败: {error_message}")
            return {"name": "internet_search", "content": error_message}
