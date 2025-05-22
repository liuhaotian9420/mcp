import random

def simple_tool_with_imports(text: str) -> str:
    """
    Simple tool that returns a random number.
    """
    return str(random.randint(0, 100)) + " " + text


