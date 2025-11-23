"""
title: Usage Event
author: qingchunnh
git_url: https://github.com/qingchunnh/QC-OpenWebUI-Plugin.git
description: Usage Event
version: 0.0.2
licence: MIT
"""

import logging
import math
import time

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=0, description="filter priority")
        SHOW_TIME: bool = Field(default=True, description="是否显示用时")
        SHOW_TOKENS: bool = Field(default=True, description="是否显示 Tokens 信息")
        SHOW_TPS: bool = Field(default=True, description="是否显示 TPS")
        SHOW_COST: bool = Field(default=True, description="是否显示费用")

    def __init__(self):
        self.valves = self.Valves()
        self.start_time = time.time_ns()

    async def inlet(self, body: dict) -> dict:
        self.start_time = time.time_ns()
        return body

    async def outlet(
        self,
        body: dict,
        __event_emitter__: callable = None,
    ) -> dict:

        # check body
        if not body or not isinstance(body, dict):
            return body

        # load messages
        messages = body.get("messages") or []
        if not messages:
            return body

        # load usage
        message = messages[-1]
        usage = message.get("usage")
        if not usage:
            return body

        # record end time
        end_time = time.time_ns()
        duration = math.ceil((end_time - self.start_time) / 1e9)
        if duration >= 60:
            total_time = "%dm%ds" % (duration // 60, duration % 60)
        else:
            total_time = "%ds" % duration

        # load data
        prompt_tokens = usage.get("prompt_tokens", 0)
        completions_tokens = usage.get("completion_tokens", 0)
        total_cost = usage.get("total_cost", 0)
        total_cost = (
            "无"
            if total_cost == 0
            else ("< 0.01" if total_cost < 0.01 else "%.2f" % total_cost)
        )

        # Collect display items based on settings
        description_parts = []

        # log usage
        if self.valves.SHOW_TIME:
            description_parts.append(f"用时: {total_time}")

        if self.valves.SHOW_TOKENS:
            description_parts.append(f"Tokens: {prompt_tokens} + {completions_tokens}")

        if self.valves.SHOW_TPS and duration > 0:
            tps = completions_tokens / duration
            description_parts.append(f"TPS: {tps:.0f}")

        if self.valves.SHOW_COST:
            description_parts.append(f"费用: {total_cost}")

        # Join all description parts with separator
        description = " | ".join(description_parts)

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": description,
                        "done": True,
                        "hidden": False,
                    },
                }
            )

        return body
