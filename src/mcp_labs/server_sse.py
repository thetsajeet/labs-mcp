"""
MCP Labs: Calculator
uses sse
"""

from mcp.server import MCPServer

# Initialize MCPServer
mcp = MCPServer("mcp_labs: Calculator")

# Register tools
@mcp.tool()
def calculator(expression: str) -> float:
    """
    Evaluates a mathematical expression and returns the result.

    Args:
        expression: A string representing a mathematical expression.

    Returns:
        The result of the evaluation.
    Example:
        >>> calculator("2 + 2")
        4.0
    """
    try:
        # Evaluate the mathematical expression safely
        result = eval(expression, {"__builtins__": None}, {})
        return result
    except Exception as e:
        return f"Error evaluating expression: {e}"