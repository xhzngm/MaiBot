import json
import re

from src.do_tool.tool_can_use.base_tool import BaseTool
import requests
from src.common.logger import get_module_logger


class InternetSearchTool(BaseTool):
    """互联网搜索工具"""

    logger = get_module_logger("网络搜索工具")

    name = "internet_search"
    description = "通过API执行互联网搜索并返回结果"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "用户的搜索词"},
        },
        "required": ["query"],
    }


    async def execute(self, function_args: dict, message_txt: str = "") -> dict:
        """执行互联网搜索

        Args:
            function_args: 工具参数
            message_txt: 原始消息文本，此工具不使用

        Returns:
            Dict: 搜索结果
        """
        api_url = "https://api.bochaai.com/v1/ai-search"
        headers = {
            "Authorization": "Bearer sk-be376e2fe720435987804fb2b6ca5149",
            "Content-Type": "application/json",
        }
        payload = {
            "query": function_args.get("query"),
            "freshness": function_args.get("freshness", "noLimit"),
            "count":3,
            "answer": False,
            "stream": False,
        }

        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = json.loads(response.text)

            summaries = []

            # 遍历所有消息
            for message in data.get('messages', []):
                if message.get('type') == 'source' and 'content' in message:
                    content = message['content']

                    # 使用正则表达式查找所有summary字段
                    matches = re.findall(r'"summary"\s*:\s*"(.*?)"', content)

                    # 添加到结果列表
                    summaries.extend(matches)
            result = {
                "name": "internet_search",
                "content": {"summaries": summaries},
            }
            self.logger.info(f"搜索成功: {result}")
            return result
        else:
            error_message = f"Error: {response.status_code}, {response.text}"
            self.logger.info(f"搜索失败: {error_message}")
            return {"name": "internet_search", "content": error_message}
