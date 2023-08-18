from agentware.base import OneshotAgent, PromptProcessor

# conversation_setup: str, template: str, output_schema=None
summarizer_agent = OneshotAgent(PromptProcessor(
    "You are a professional writer who is very good at summarizing texts",
    'You will be given a list of conversation between user and assistant. Your task is to make a summary of valuable information from them. Your output must be a json in the following format: {"output": <your summary here>}. Now summarize the text in the triple backticks: ```{{{text_to_summarize}}}```',
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
                "output": {"type": "string"}
        },
        "required": ["output"],
        "additionalProperties": "true"
    }))

attribute_question_agent = OneshotAgent(PromptProcessor(
    "",
    'Given the context of the a list of conversations between user and assistant in triple backsticks: ```{{{observations}}}``` List all the attributes you already know about the the objects mentioned above. Focus more on the words of the user because it is more important. The attributes should reflect the current status of the object, with no duplication. Output must be a json in the following format:{"output": [{"object": <the name of the object>, "attribute": <the name of the attribute>, "reason": <the reason of selecting this attribute>}, ...]}. Your output is:',
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
                "output": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "object": {
                                "type": "string"
                            },
                            "attribute": {
                                "type": "string"
                            },
                            "reason": {
                                "type": "string"
                            }
                        },
                        "required": ["object", "attribute"],
                        "additionalProperties": "true"
                    }
                }
        },
        "required": ["output"],
        "additionalProperties": "true"
    }))

attribute_agent = OneshotAgent(PromptProcessor(
    "",
    'Given the context of the below observations between triple backsticks: ```{{{observations}}}```, Use one short sentence to describe the current status of all the objects: {{{object_attributes}}} For each of the entries above, write the value of its attribute. Output must be a json in the format of {"output": [{"object": < name of the object >, "attribute": "<the attribute>", "value": <the value of the attribute given the status of the object in observations> }, ...(other objects)]}. For example, {"output": [{"object": "old joe", "attribute": "age", "value": "69 years old"}]}. Your output is:',
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
                "output": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "object": {
                                "type": "string"
                            },
                            "attribute": {
                                "type": "string"
                            },
                            "value": {
                                "type": "string"
                            }
                        },
                        "required": ["object", "value"],
                        "additionalProperties": "true"
                    }
                }
        },
        "required": ["output"],
        "additionalProperties": "true"
    }))

conflict_detector_agent = OneshotAgent(PromptProcessor(
    "You are an expert who is good at finding the logic flaw and contrary between past records and present observations.",
    'Given the observations and records data in the triple backsticks below: ```{{{observations_and_records}}}```. The "observations" field is a list of new observations, while the "records" field contains the records before the observations, each with and id. Your job is to help find out which of the records are no longer true on the condition of the observation, give the ids of the them and rough reason. List the ids of the facts if they are wrong given the observations. Do not write any code, simply give the final output. Example output is {"output": [{"id": 1, "reason": "Record 1 shows that flight 484 s normal, but the observation shows it is canceled"}, {"id": 17856839541, "reason": "Record 17856839541 shows that it is going to rain tomorrow. However the observation shows that the weather forcast is sunny"}]}. Your output is:',
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
                "output": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer"
                            },
                            "reason": {
                                "type": "string"
                            }
                        },
                        "required": ["id", "reason"],
                        "additionalProperties": "true"
                    }
                }
        },
        "required": ["output"],
        "additionalProperties": "true"
    }))


#
# For each of the entries above, write the description that corresponds to it
# your output must be a json in the format of
# [{"object": <name of the object>, "description": <the status of the object>}, ...(other objects)]
# For example,
# [{"object": "old joe", "description": "is 69 years old"}]

# agents = dict()
# fact_agent_config = None
# with open(facts_agent_config_path, "r") as f:
#     fact_agent_config = json.loads(f.read())
# agents["fact"] = OneshotAgent(fact_agent_config)
# # Summarize agent
# summarizer_agent_config = None
# with open(summarize_agent_config_path, "r") as f:
#     summarizer_agent_config = json.loads(f.read())
# agents["summarizer"] = OneshotAgent(summarizer_agent_config)
# # Reflection question
# ref_q_agent_config = None
# with open(ref_q_agent_config_path, "r") as f:
#     ref_q_agent_config = json.loads(f.read())
# agents["reflection_q"] = OneshotAgent(ref_q_agent_config)
# # Reflection
# ref_agent_config = None
# with open(ref_agent_config_path, "r") as f:
#     ref_agent_config = json.loads(f.read())
# agents["reflection"] = OneshotAgent(ref_agent_config)
# # Tool query
# tool_query_agent_config = None
# with open(tool_query_agent_config_path, "r") as f:
#     tool_query_agent_config = json.loads(f.read())
# agents["tool_query"] = OneshotAgent(tool_query_agent_config)
# conflict_resolver_agent_config = None
# with open(conflict_resolver_agent_config_path, "r") as f:
#     conflict_resolver_agent_config = json.loads(f.read())
# agents["conflict_resolver"] = OneshotAgent(
#     conflict_resolver_agent_config)
