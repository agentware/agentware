from autogpt.logs import logger
from typing import Any, Dict
from logging import Logger

logger = Logger("debug")


def fix_json_using_multiple_techniques(assistant_reply: str) -> Dict[Any, Any]:
    from json_fixes.parsing import attempt_to_fix_json_by_finding_outermost_brackets

    from json_fixes.parsing import fix_and_parse_json

    # Parse and print Assistant response
    assistant_reply_json = fix_and_parse_json(assistant_reply)
    if assistant_reply_json == {}:
        assistant_reply_json = attempt_to_fix_json_by_finding_outermost_brackets(
            assistant_reply
        )

    if assistant_reply_json != {}:
        return assistant_reply_json

    logger.error(
        "Error: The following AI output couldn't be converted to a JSON:\n", assistant_reply)
    return {}
