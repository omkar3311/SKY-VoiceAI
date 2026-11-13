import uuid
from langchain_core.tools import tool

@tool
def generate_random_uuid() -> str:
    """
    Generate a unique UUID4 string.

    This tool creates a random UUID (Universally Unique Identifier) using the
    UUID4 algorithm, which is based on random numbers. The function returns
    the UUID as a string. No input arguments are required.

    Returns:
        str: A string containing the generated UUID4, e.g. '3f9e2c1a-4b8d-4f6e-9c2b-1a2b3c4d5e6f'.
    """
    try:
        new_uuid = uuid.uuid4()
        return f"Generated UUID4: {new_uuid}"
    except Exception as e:
        return f"Error generating UUID4: {str(e)}"