"""
MCP Labs: Form Filler
uses stdio
"""

from fastmcp import FastMCP

mcp = FastMCP("mcp_labs: Form Filler")

@mcp.tool()
def form_filler(form_data: dict, updates: list[dict]) -> dict:
    """
    Fills in a form with the provided updates.

    Args:
        form_data: A dictionary representing the form data to be filled.
        updates: A list of dictionaries, each containing a "name" and "value" key.

    Returns:
        The updated form data. Updates for names not present in ``form_data`` are ignored.

    Example:
        >>> form_filler({"name": "Ada", "role": "engineer"}, [
        ...     {"name": "role", "value": "mathematician"},
        ...     {"name": "city", "value": "London"},
        ... ])
        {'name': 'Ada', 'role': 'mathematician'}
    """
    for update in updates:
        name, value = update.get("name"), update.get("value")
        if name in form_data:
            form_data[name] = value
    return form_data

@mcp.tool()
def form_payload() -> dict:
    """
    Returns form data payload with current structure.

    Returns:
        A dictionary representing a form payload.
    """
    return {
        "name": "Ada Lovelace",
        "role": "mathematician",
    }

if __name__ == "__main__":
    mcp.run()