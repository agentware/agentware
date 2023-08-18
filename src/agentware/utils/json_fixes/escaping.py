""" Fix invalid escape sequences in JSON strings. """
import json
from agentware.utils.json_fixes.utilities import extract_char_position

debug_mode = True


def fix_invalid_escape(json_to_load: str, error_message: str) -> str:
    """Fix invalid escape sequences in JSON strings.

    Args:
        json_to_load (str): The JSON string.
        error_message (str): The error message from the JSONDecodeError
          exception.

    Returns:
        str: The JSON string with invalid escape sequences fixed.
    """
    while error_message.startswith("Invalid \\escape"):
        bad_escape_location = extract_char_position(error_message)
        json_to_load = (
            json_to_load[:bad_escape_location] +
            json_to_load[bad_escape_location + 1:]
        )
        try:
            json.loads(json_to_load)
            return json_to_load
        except json.JSONDecodeError as e:
            if debug_mode:
                print("json loads error - fix invalid escape", e)
            error_message = str(e)
    return json_to_load
