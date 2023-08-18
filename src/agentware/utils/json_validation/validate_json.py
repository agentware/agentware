import json
from jsonschema import Draft7Validator
from agentware.agent_logger import Logger

logger = Logger()


def validate_json(json_object: object, schema: object) -> object:
    """
    :type schema_name: object
    :param schema_name:
    :type json_object: object
    """
    logger.debug("Creating validator")
    validator = Draft7Validator(schema)
    logger.debug(f"validator created {validator}")
    if errors := sorted(validator.iter_errors(json_object), key=lambda e: e.path):
        logger.debug("validator error")
        logger.error("The JSON object is invalid.")
        # Replace 'json_object' with the variable containing the JSON data
        logger.error(json.dumps(json_object, indent=4))
        logger.error("The following issues were found:")

        for error in errors:
            logger.error(f"Error: {error.message}")
        raise Exception("Error validating json with errors:\n" +
                        "\n".join([f"{e.message}"for e in errors]))
    else:
        logger.debug("The JSON object is valid.")
    return json_object
