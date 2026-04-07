#!/usr/bin/env python3
"""
Base Agent - Foundation for A-RAG Agent System

Provides:
- BaseAgent: Abstract base class for all agents
- Tool: Decorator and class for defining agent tools
- AgentResult: Standardized result format
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

from app.utils.logger import get_logger

logger = get_logger("Agents")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AgentResult:
    """
    Standardized result from any agent execution.

    Attributes:
        success: Whether the execution was successful
        data: The actual result data
        error: Error message if failed
        execution_time_ms: Time taken in milliseconds
        metadata: Additional metadata about the execution
    """
    success: bool = True
    data: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.success


@dataclass
class ToolCall:
    """
    Record of a tool invocation.

    Attributes:
        tool_name: Name of the tool called
        arguments: Arguments passed to the tool
        result: Result from the tool
        duration_ms: Time taken in milliseconds
    """
    tool_name: str
    arguments: dict[str, Any]
    result: Any = None
    duration_ms: float = 0.0


@dataclass
class Tool:
    """
    Definition of an agent tool.

    Attributes:
        name: Unique tool name
        description: Description for the LLM
        function: The actual function to execute
        parameters: Parameter schema for validation
    """
    name: str
    description: str
    function: Callable
    parameters: dict[str, Any] = field(default_factory=dict)

    def __call__(self, *args, **kwargs) -> Any:
        return self.function(*args, **kwargs)


# =============================================================================
# Tool Decorator
# =============================================================================

def tool(name: str = None, description: str = ""):
    """
    Decorator to mark a method as an agent tool.

    Usage:
        @tool(name="search", description="Search for content")
        def search_content(self, query: str) -> List[Dict]:
            ...
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Store tool metadata on the function
        wrapper._is_tool = True
        wrapper._tool_name = tool_name
        wrapper._tool_description = description or func.__doc__ or ""

        return wrapper

    return decorator


# =============================================================================
# Base Agent
# =============================================================================

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the A-RAG system.

    Features:
    - Automatic tool discovery from decorated methods
    - Execution timing and logging
    - Standardized result format
    - Error handling

    Subclasses should:
    - Implement the `execute` method
    - Define tools using the @tool decorator
    """

    def __init__(self, name: str = None):
        """Initialize the agent."""
        self.name = name or self.__class__.__name__
        self.tools: dict[str, Tool] = {}
        self.tool_calls: list[ToolCall] = []
        self.logger = get_logger(self.name)

        # Discover tools from decorated methods
        self._discover_tools()

    def _discover_tools(self) -> None:
        """Find all methods decorated with @tool and register them."""
        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue

            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, '_is_tool'):
                tool_obj = Tool(
                    name=attr._tool_name,
                    description=attr._tool_description,
                    function=attr
                )
                self.tools[tool_obj.name] = tool_obj
                self.logger.debug(f"Registered tool: {tool_obj.name}")

    def get_tools(self) -> list[Tool]:
        """Get list of available tools."""
        return list(self.tools.values())

    def get_tool_descriptions(self) -> str:
        """Get formatted descriptions of all tools for LLM prompt."""
        lines = []
        for tool in self.tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool

        Returns:
            Tool result

        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")

        tool = self.tools[tool_name]
        start_time = time.time()

        try:
            result = tool(**kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # Record the call
            self.tool_calls.append(ToolCall(
                tool_name=tool_name,
                arguments=kwargs,
                result=result,
                duration_ms=duration_ms
            ))

            self.logger.debug(f"Tool {tool_name} executed in {duration_ms:.1f}ms")
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Tool {tool_name} failed: {e}")

            self.tool_calls.append(ToolCall(
                tool_name=tool_name,
                arguments=kwargs,
                result=None,
                duration_ms=duration_ms
            ))

            raise

    def run(self, *args, **kwargs) -> AgentResult:
        """
        Execute the agent with timing and error handling.

        Args:
            *args, **kwargs: Arguments passed to execute()

        Returns:
            AgentResult with success/failure info
        """
        start_time = time.time()
        self.tool_calls = []  # Reset tool calls

        try:
            result = self.execute(*args, **kwargs)
            execution_time_ms = (time.time() - start_time) * 1000

            return AgentResult(
                success=True,
                data=result,
                execution_time_ms=execution_time_ms,
                metadata={
                    "tool_calls": len(self.tool_calls),
                    "agent": self.name
                }
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Agent execution failed: {e}", exc_info=True)

            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
                metadata={
                    "tool_calls": len(self.tool_calls),
                    "agent": self.name
                }
            )

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the agent's main task.

        Subclasses must implement this method.

        Returns:
            Agent-specific result data
        """
        pass

    def clear_history(self) -> None:
        """Clear tool call history."""
        self.tool_calls = []
