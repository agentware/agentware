from agentware.utils.json_fixes.parsing import fix_and_parse_json
from agentware.utils.json_validation.validate_json import validate_json
from typing import List, Dict
from agentware.utils.num_token_utils import count_message_tokens
from agentware.core_engines import OpenAICoreEngine
from agentware import KNOWLEDGE_BASE_IDENTIFIER_PREFIX
from datetime import datetime
from agentware.agent_logger import Logger
from pymilvus import Milvus, connections, utility
import os
import time
import json
import requests
import openai
import agentware
import copy
import pystache

from typing import List, Dict, Tuple
from pymilvus import Collection, DataType, FieldSchema, CollectionSchema


logger = Logger()


class AgentConfig:
    def __init__(self, config: Dict[str, any]):
        assert "name" in config
        self.name = config['name']
        assert "conversation_setup" in config
        assert "prompt_prefix" in config
        if "output_format" in config:
            assert "instruction" in config

        # "name": "tool_query",
        # "conversation_setup": "You will be given a json file that has two keys 'observations' and 'facts', each containing a list. The 'observations' field is a list of new observations, while the 'facts' field contains the facts before the observations, each with and id. Your job is to help find out which of the facts are no longer true, give the ids of the them, and the updated facts that are true given the observations",
        # "prompt_prefix": "List the ids of the facts if they are wrong given the observations:",
        # "output_format": {
        #     "instruction": "Your output MUST be a json that has a field named \"wrong_facts\".",
        #     "examples": [
        #         {
        #             "condition": "",
        #             "output": "{\"wrong_facts\": [{\"id\": <int id of the wrong fact, must be in accordance with the facts in question>, <another id>, ...]}"
        #         }
        #     ],
        #     "output_schema":
        #     {
        #         "$schema": "http://json-schema.org/draft-07/schema#",
        #         "type": "object",
        #         "properties": {
        #             "wrong_facts": {
        #                 "type": "array",
        #                 "items": {
        #                     "type": "integer"
        #                 }
        #             }
        #         },
        #         "required": ["wrong_facts"],
        #         "additionalProperties": false
        #     },
        #     "termination_observation": "wrong_facts"
        # }


class Node:
    def __init__(self, node_name: str, embedding: List[float] = []):
        self.name = node_name
        self.embeds = embedding
        self.created_at = int(time.time())

    def __repr__(self):
        return self.name


class Command:
    def __init__(self, name: str, description: str, endpoint: str, input_schema: str, output_schema: str):
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.input_schema = input_schema
        self._output_schema = output_schema
        self.created_at = int(time.time())\


    def to_prompt(self) -> str:
        return f"""{self.name}: {self.description}
input must strictly be a json following this schema:
{self.input_schema}"""

    def __repr__(self):
        return f"{self.name}: {self.description}"

    def update_embeds(self, embeds: List[float]) -> None:
        self.embeds = embeds


class MemoryUnit:
    def __init__(self, role, content) -> None:
        assert role == "user" or role == "system" or role == "assistant"
        self.role = role
        self.content = content
        self.num_tokens = count_message_tokens({
            "role": role,
            "content": content
        })

    @classmethod
    def from_json(cls, data: Dict[str, str]):
        return cls(data["role"], data["content"])

    def to_json(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content
        }

    def __repr__(self) -> str:
        return f"<{self.role}>: {self.content}[{self.num_tokens} tokens]"

    def __str__(self) -> str:
        return f"<{self.role}>: {self.content}[{self.num_tokens} tokens]"


class Knowledge:

    def __init__(self, created_at: int, content: str, embeds: List = [], id="", num_tokens: int = 0):
        self.created_at = int(created_at)
        self.content = content
        self.embeds = embeds
        self.id = id
        if num_tokens <= 0:
            self.num_tokens = count_message_tokens({
                "content": content
            })
        else:
            self.num_tokens = num_tokens

    @classmethod
    def from_json(cls, knowledge_json: Dict):
        embeds = []
        if "embeds" in knowledge_json:
            embeds = knowledge_json["embeds"]
        id = ""
        if "id" in knowledge_json:
            id = knowledge_json["id"]
        return cls(knowledge_json["created_at"], knowledge_json["content"], embeds, id)

    def to_json(self):
        return {
            "created_at": self.created_at,
            "content": self.content,
            "embeds": self.embeds,
            "id": self.id
        }

    def _to_str(self, created_at: int, content: str) -> str:
        return f"knowledge created at {datetime.fromtimestamp(created_at)}. content: {content}"

    def __repr__(self):
        return f"knowledge({self.content}, created at {self.created_at}, id {self.id})"

    def update_embeds(self, embeds: List[float]) -> None:
        self.embeds = embeds


class BaseAgent:
    """
        Base agent class with
        - config initialization
        - parse and retry
    """
    MODEL_NAME = "gpt-3.5-turbo-16k-0613"
    MAX_NUM_RETRIES = 3

    def __init__(self, id, prompt_processor=None):
        self.id = id
        if not prompt_processor:
            self._prompt_processor = PromptProcessor("", "", "")
        self.init(prompt_processor)
        openai.api_key = agentware.openai_api_key
        self._core_engine = OpenAICoreEngine()

    def init(self, prompt_processor=None):
        config = dict()
        if prompt_processor:
            self.set_prompt_processor(prompt_processor)
            config = prompt_processor.to_config()
        self.set_config(config)

    def get_conversation_setup(self):
        return self._prompt_processor.get_conversation_setup()

    def set_prompt_processor(self, prompt_processor):
        self._prompt_processor = prompt_processor

    def set_config(self, cfg: dict):
        self.config = cfg

    def set_core_engine(self, core_engine):
        logger.debug(f"Setting core engine to {core_engine}")
        self._core_engine = core_engine

    def get_embeds(self, text: str) -> List[float]:
        return self._core_engine.get_embeds(text)

    # def set_config(self, cfg: Dict[str, any]):
    #     assert "name" in cfg
    #     assert "conversation_setup" in cfg
    #     assert "prompt_processor" in cfg
    #     self._config = cfg
    #     self.id = cfg["name"]
    #     self._prompt_processor = PromptProcessor(cfg["prompt_processor"])

        # # output format
        # if "output_format" in cfg:
        #     self._format_instruction = ""
        #     if "instruction" in cfg["output_format"]:
        #         self._format_instruction = cfg["output_format"]["instruction"]
        #     self._output_schema = ""
        #     if "output_schema" in cfg["output_format"]:
        #         self._output_schema = cfg["output_format"]["output_schema"]
        #     if "examples" in cfg["output_format"]:
        #         self._format_examples = ""
        #         for example in cfg["output_format"]["examples"]:
        #             example_output = example["output"]
        #             if example["condition"]:
        #                 condition = example["condition"]
        #                 self._format_examples += f"In the case of {condition}, output in the form of {example_output}"
        #             else:
        #                 self._format_examples += f"Output in the form of {example_output}"
        #                 # Empty condition means one output format for all cases
        #                 break
        #     self._format_instruction += self._format_examples
        #     self._termination_observation = ""
        #     if "termination_observation" in cfg["output_format"]:
        #         self._termination_observation = cfg["output_format"]["termination_observation"]
        if "prompt_prefix" in cfg:
            self.prompt_prefix = cfg["prompt_prefix"]

    def _messages_to_str(self, messages: List[Dict[str, str]]) -> str:
        message_prefix = "\n************* Conversation *************\n"
        message_suffix = "\n********* End of Conversation *********\n"
        message_str = "\n---------------------------------\n".join(
            [f"<{m['role']}>: {m['content']}" for m in messages])
        return message_prefix + message_str + message_suffix

    def _run(self, messages: List[Dict[str, str]]) -> str:
        logger.debug(
            f"Sending raw messages: {self._messages_to_str(messages)}")
        self._core_engine.run(messages)
        raw_output = self._core_engine.run(messages)
        # completion = openai.ChatCompletion.create(
        #     model=self.MODEL_NAME, messages=messages)
        # raw_output = completion.choices[0].message.content
        logger.debug(f"Raw output: {raw_output}")
        return raw_output

    def run(self, prompt: str):
        raise Exception("Not Implemented")

    def __repr__(self) -> str:
        return f""


class OneshotAgent(BaseAgent):
    def __init__(self, prompt_processor=None):
        super().__init__("", prompt_processor)

    def run(self, *args, **kwargs) -> str:
        num_retries = 0
        raw_output = ""
        messages = []
        conversation_setup = self._prompt_processor.get_conversation_setup()
        if conversation_setup:
            messages += [{
                "role": "system",
                "content": conversation_setup
            }]
        prompt = self._prompt_processor.format(*args, **kwargs)
        logger.debug(f"prompt is {prompt}")
        messages += [{
            "role": "user",
            "content": prompt
        }]
        original_messages = copy.deepcopy(messages)
        messages_with_error = original_messages
        output = ""
        while True:
            try:
                raw_output = self._run(messages_with_error)
                logger.debug(f"Raw output is {raw_output}")
                try:
                    output = self._prompt_processor.parse_output(raw_output)
                    logger.debug(f"parsed output is {output}")
                    return output
                except Exception as e:
                    logger.warning(f"Error parsing output with error. {e}")
                    messages_with_error = original_messages + [
                        {
                            "role": "assistant",
                            "content": raw_output
                        },
                        {
                            "role": "user",
                            "content": f"Failed to parse output. Your content is great, regenerate with the same content in a format that aligns with the requirements and example schema."
                        },
                    ]
            except Exception as e:
                logger.warning(f"Error running prompt with error {e}")
            if num_retries >= self.MAX_NUM_RETRIES:
                if num_retries >= self.MAX_NUM_RETRIES:
                    logger.debug("Max number of retries exceeded")
                output = "Sorry, I failed to generate the required json schema"
                break
            num_retries += 1
        return output


class BaseMilvusStore():
    def _create_collection(self, collection_name: str) -> Collection:
        raise Exception("Not Implemented")

    def __init__(self, cfg: dict[str, any]) -> None:
        if not cfg:
            raise BaseException("Invalid config")
        try:
            self.milvus_uri = cfg['uri']
            self.user = cfg['user']
            self.port = cfg['port']
            self.nprobe = int(cfg['nprobe'])
            self.nlist = int(cfg['nlist'])
        except ValueError as e:
            raise BaseException(f"Missing key in config caused error {e}")

        self.connect = connections.connect(
            alias="default",
            host=self.milvus_uri,
            port=self.port
        )
        logger.debug(f"Connected to vector store: {self.milvus_uri}")

    def check_and_maybe_create_collection(self, collection_name: str):
        if utility.has_collection(collection_name):
            return
        logger.debug(
            f"default collection {collection_name} not found. Creating one.")
        collection = self._create_collection(collection_name)
        logger.debug(
            f"Creating default collection: {collection_name}")

        collection.load()

    def _similarity_query(self, query_vector, collection_name, output_fields: List[str]):
        try:
            search_params = {"metric_type": "L2",
                             "params": {"nprobe": self.nprobe}}
            c = Collection(collection_name)
            results = c.search([query_vector],
                               anns_field="vector",
                               param=search_params,
                               round_decimal=-1,
                               output_fields=output_fields,
                               limit=999)
            return results
        except Exception as err:
            logger.debug("get err {}".format(err))
            return err

    def remove_by_ids(self, ids_to_delete: List[int], collection_name: str):
        c = Collection(collection_name)
        expr = f"id in {ids_to_delete}"
        c.delete(expr)

    def remove_collection(self, knowledge_base_collection_id):
        utility.drop_collection(knowledge_base_collection_id)


class PromptProcessor:
    def __init__(self, conversation_setup: str, template: str, output_schema=None) -> None:
        self._template = template
        self._conversation_setup = conversation_setup
        self._output_schema = output_schema
        # TODO: check output schema to make sure the first layer key is "output"

    @classmethod
    def from_config(cls, cfg: dict):
        return cls(cfg["conversation_setup"], cfg["template"], cfg["output_schema"])

    def get_conversation_setup(self):
        return self._conversation_setup

    def get_template(self):
        return self._template

    def to_config(self):
        return {
            "conversation_setup": self._conversation_setup,
            "template": self._template,
            "output_schema": self._output_schema
        }

    def format(self, *args, **kwargs):
        if not self._template:
            if not len(args) == 1:
                raise BaseException(
                    "One and only one arg is required to format for empty template")
            return args[0]
        return pystache.render(self._template, kwargs)

    def parse_output(self, raw_output):
        if self._output_schema:
            logger.debug(f'parsing {raw_output}')
            parsed_output = fix_and_parse_json(raw_output)
            logger.debug(f"parse success, output is {parsed_output}")
            logger.debug(f"validating with schema {self._output_schema}")
            validated_output = validate_json(
                parsed_output, self._output_schema)
            return validated_output["output"]
        else:
            return raw_output


class Connector():
    """

    modes
    - Use an agent, only have access to newly created
    - Fork an agent that allows access, have access to prefix, prompt prefix and knowledge
    -
    """

    def __init__(self):
        self._agent_id = None

    def verify_endpoint(self):
        if not agentware.endpoint:
            raise ValueError(
                f"Invalid agentware endpoint {agentware.endpoint}")

    def register_agent(self, agent_id: str) -> int:
        # URL to send the request tor
        url = os.path.join(agentware.endpoint, "register_agent")
        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        data = json.dumps({
            "agent_id": agent_id
        })

        response = requests.put(url, headers=headers, data=data)
        # Check the response status code
        if response.status_code == 200:
            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            return data["exists"]
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            return None

    def remove_agent(self, agent_id: str):
        knowledge_base_identifier = self._get_knowledge_base_id(agent_id)
        # URL to send the request tor
        url = os.path.join(agentware.endpoint, "remove_agent")
        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        data = json.dumps({
            "agent_id": agent_id,
            "knowledge_base_collection_id": knowledge_base_identifier
        })
        logger.debug(
            f"Removing agent {agent_id} with its vectors in collection {knowledge_base_identifier}")
        response = requests.put(url, headers=headers, data=data)
        # Check the response status code
        if response.status_code == 200:
            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            if data["success"]:
                return {"success": True}
            else:
                return {"success": False, "fail_reason": data["fail_reason"]}
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            return None

    def agent_exists(self, agent_id: str):
        url = os.path.join(
            agentware.endpoint, "agent_exists", str(agent_id))
        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            logger.debug(f"agent exists {data}")
            if data["exists"]:
                return True
            else:
                return False
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            return None

    def _get_command_hub_id(self) -> str:
        return "command_collection"

    def _get_knowledge_base_id(self, agent_id: int):
        return f"{KNOWLEDGE_BASE_IDENTIFIER_PREFIX}_{agent_id}"

    def _get_knowledge_graph_label(self, agent_id: int):
        return f"knowledge_graph_{agent_id}"

    def all_agents(self) -> List[str]:
        url = os.path.join(
            agentware.endpoint, "all_agents")
        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }

        response = requests.get(url, headers=headers)
        # Check the response status code
        if response.status_code == 200:
            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            return data
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            return None

    def get_longterm_memory(self, agent_id: int, page_number: int, page_size: int) -> List[Dict]:
        url = os.path.join(
            agentware.endpoint, "get_longterm_memory", str(agent_id))
        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        params = {
            'page_number': page_number,
            'page_size': page_size
        }

        response = requests.get(url, headers=headers, params=params)
        # Check the response status code
        if response.status_code == 200:

            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            memory_units = [MemoryUnit.from_json(d) for d in data]
            return memory_units
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            return None

    def update_longterm_memory(self, agent_id: int, memory_units: List[MemoryUnit]):
        url = os.path.join(
            agentware.endpoint, "update_longterm_memory", str(agent_id))
        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        memory_data = json.dumps({
            "memory_data": [m.to_json() for m in memory_units]
        })

        response = requests.put(url, headers=headers, data=memory_data)
        # Check the response status code
        if response.status_code == 200:

            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            return data
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            return None

    def update_agent(self, agent_id: int, agent_config: Dict[any, any], memory_units: List[MemoryUnit]):
        if agent_id is None:
            agent_id = -1
        url = os.path.join(
            agentware.endpoint, "update_agent", str(agent_id))
        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        agent_data = json.dumps({
            "agent_config": agent_config,
            "memory_data":  [m.to_json() for m in memory_units],
        })
        logger.info(
            f"Saving agent {agent_data}")

        response = requests.put(url, headers=headers, data=agent_data)
        # Check the response status code
        if response.status_code == 200:

            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            return data
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            return None

    def get_agent(self, agent_id: str) -> Tuple[Dict[any, any], Dict[str, Dict[any, any]], List[MemoryUnit], List[Knowledge], str]:
        # URL to send the request to
        url = os.path.join(agentware.endpoint, "get_agent")

        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        params = {
            "agent_id": agent_id
        }
        response = requests.get(url, headers=headers, params=params)
        # Check the response status code
        if response.status_code == 200:
            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            if not data["success"]:
                raise ValueError(data["error_code"])
            agent_config = data["agent_config"]
            memory_units = [MemoryUnit.from_json(
                m) for m in data["memory_units"]]
            return agent_config, memory_units
        else:
            print("response is", response.text)
            # Request failed
            logger.debug(
                f'Request failed with code: {response.status_code} error: {response.text}')
            return None, None

    def save_knowledge(self, agent_id: int, knowledges: List[Knowledge]):
        knowledge_base_identifier = self._get_knowledge_base_id(agent_id)
        logger.info(
            f"Saving knowledge: {knowledges} to knowledge base {knowledge_base_identifier}")
        # URL to send the request to
        url = os.path.join(agentware.endpoint, "save_knowledge",
                           knowledge_base_identifier)

        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        data = json.dumps({
            "knowledges": [k.to_json() for k in knowledges]
        })
        response = requests.put(url, headers=headers, data=data)
        # Check the response status code
        if response.status_code == 200:

            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            return data
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            return None

    def search_commands(self, query_embeds: List[float], token_limit=100) -> List[Command]:
        # URL to send the request to
        url = os.path.join(agentware.endpoint, "search_commands",
                           self._get_command_hub_id())

        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        data = json.dumps({
            "query_embeds": query_embeds,
            "token_limit": token_limit
        })
        response = requests.get(url, headers=headers, data=data)
        # Check the response status code
        if response.status_code == 200:

            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            return data
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            logger.debug(response.text)
            return None

    def search_knowledge(self, agent_id: int, query_embeds: List[float], token_limit=100) -> List[Knowledge]:
        # URL to send the request to
        url = os.path.join(agentware.endpoint, "search_knowledge",
                           self._get_knowledge_base_id(agent_id))

        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        data = json.dumps({
            "query_embeds": query_embeds,
            "token_limit": token_limit
        })
        response = requests.get(url, headers=headers, data=data)
        # Check the response status code
        if response.status_code == 200:
            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            logger.debug(f"knowledge data is {data}")
            return [Knowledge.from_json(knowledge_json) for knowledge_json in data]
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            logger.debug(response.text)
            return None

    def remove_knowledge(self, agent_id: int, ids_to_remove: List[int]):
        knowledge_base_identifier = self._get_knowledge_base_id(agent_id)
        # URL to send the request to
        url = os.path.join(agentware.endpoint, "remove_knowledge")

        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        data = json.dumps({
            "xx": 'yy',
            "collection_name": knowledge_base_identifier,
            "ids_to_remove": ids_to_remove
        })
        response = requests.put(url, headers=headers, data=data)
        # Check the response status code
        if response.status_code == 200:
            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            if "success" in data:
                logger.debug(f"Removed ids success? {data}")
                return data["success"]
            else:
                return False
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            logger.debug(response.text)
            return None

    def get_recent_knowledge(self, agent_id: int, token_limit=100) -> List[Knowledge]:
        url = os.path.join(agentware.endpoint, "get_recent_knowledge",
                           self._get_knowledge_base_id(agent_id))

        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        data = json.dumps({
            "token_limit": token_limit
        })
        response = requests.get(url, headers=headers, data=data)
        # Check the response status code
        if response.status_code == 200:
            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            logger.debug(f"knowledge data is {data}")
            return [Knowledge.from_json(knowledge_json) for knowledge_json in data]
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            logger.debug(response.text)
            return None

    def search_kg(self, agent_id: int, query_embeds: List[float], token_limit=100) -> List[Knowledge]:
        # URL to send the request to
        url = os.path.join(agentware.endpoint, "search_kg",
                           self._get_knowledge_graph_label(agent_id))

        headers = {
            'Authorization': f'Bearer {agentware.api_key}'
        }
        data = json.dumps({
            "query_embeds": query_embeds,
            "token_limit": token_limit
        })
        response = requests.get(url, headers=headers, data=data)
        # Check the response status code
        if response.status_code == 200:
            logger.debug(f'Request to {url} was successful')
            data = json.loads(response.text)
            logger.debug(f"knowledge data is {data}")
            return [Knowledge.from_json(knowledge_json) for knowledge_json in data]
        else:
            # Request failed
            logger.debug(
                f'Request failed with status code: {response.status_code}')
            logger.debug(response.text)
            return None
