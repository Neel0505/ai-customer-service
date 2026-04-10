"""Tool registry — maps tool names to async handler functions for LLM function calling."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

# Type alias for tool handler functions
ToolHandler = Callable[..., Awaitable[str]]


class ToolRegistry:
    """Registry of tools that the LLM can invoke via function calling."""

    def __init__(self):
        self._tools: dict[str, ToolHandler] = {}
        self._definitions: list[dict[str, Any]] = []

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: ToolHandler,
    ):
        """Register a tool with its OpenAI function schema and handler."""
        self._tools[name] = handler
        self._definitions.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        })

    def get_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions in OpenAI function calling format."""
        return self._definitions

    async def execute(self, name: str, arguments: str | dict) -> str:
        """Execute a tool by name with the given arguments.

        Arguments come as a JSON string from the LLM — we parse and dispatch.
        Returns a string result for feeding back into the LLM context.
        """
        if name not in self._tools:
            return f"Error: Unknown tool '{name}'"

        # Parse arguments
        if isinstance(arguments, str):
            try:
                args = json.loads(arguments)
            except json.JSONDecodeError:
                return f"Error: Could not parse arguments for tool '{name}'"
        else:
            args = arguments

        try:
            result = await self._tools[name](**args)
            return result
        except Exception as e:
            logger.exception("Tool execution failed: %s", name)
            return f"Error executing {name}: {str(e)}"

    async def execute_all(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Execute all tool calls and return results as messages for the LLM.

        Returns tool result messages in the format expected by OpenAI API.
        """
        results = []
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            arguments = fn.get("arguments", "{}")
            tool_call_id = tc.get("id", "")

            result = await self.execute(name, arguments)
            results.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": name,
                "content": result,
            })

        return results
