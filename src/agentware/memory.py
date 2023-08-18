from typing import Dict, List, Tuple
from agentware.base import MemoryUnit, Knowledge, Connector, OneshotAgent, BaseAgent, PromptProcessor
from agentware.helper_agents import summarizer_agent, attribute_question_agent, attribute_agent, conflict_detector_agent
from agentware.agent_logger import Logger
from agentware import HELPER_AGENT_CONFIGS_DIR_NAME

import copy
import time
import json
import os

logger = Logger()


class Memory():
    MAX_NUM_TOKENS_CONTEXT = 1000
    MAX_NUM_TOKENS_MEMORY = 1000
    MAX_NUM_TOKENS_KNOWLEDGE = 200

    def __init__(self, agent: BaseAgent):
        self._reflections = []
        self._commands = []
        self._domain_knowledge = []
        self._memory = []
        self._num_tokens_memory = 0
        self._num_tokens_context = 0
        self._num_tokens_domain_knowledge = 0
        self._agent = agent
        self.connector = Connector()

    @classmethod
    def pull(cls, agent_id: int, agent):
        connector = Connector()
        try:
            agent_config, memory_data = connector.get_agent(
                agent_id)
            memory = cls.init(agent_config, memory_data, agent)
        except Exception as e:
            raise e
        return memory

    @classmethod
    def init(cls,
             agent_config: Dict[any, any],
             working_memory: List[MemoryUnit],
             agent: BaseAgent):
        logger.debug("initializing memory")
        memory = cls(agent)
        memory._memory = working_memory
        prompt_processor = None
        if agent_config:
            prompt_processor = PromptProcessor.from_config(agent_config)
        agent.init(prompt_processor)
        return memory

    def create_helper_agents(self) -> Dict[str, OneshotAgent]:
        config_dir_absolute_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), HELPER_AGENT_CONFIGS_DIR_NAME)
        facts_agent_config_path = f"{config_dir_absolute_path}/facts.json"
        ref_q_agent_config_path = f"{config_dir_absolute_path}/reflection_question.json"
        ref_agent_config_path = f"{config_dir_absolute_path}/reflection.json"
        summarize_agent_config_path = f"{config_dir_absolute_path}/summarize.json"
        tool_query_agent_config_path = f"{config_dir_absolute_path}/tool_query.json"
        conflict_resolver_agent_config_path = f"{config_dir_absolute_path}/conflict_resolver.json"

        agents = dict()
        fact_agent_config = None
        with open(facts_agent_config_path, "r") as f:
            fact_agent_config = json.loads(f.read())
        agents["fact"] = OneshotAgent(fact_agent_config)
        # Summarize agent
        summarizer_agent_config = None
        with open(summarize_agent_config_path, "r") as f:
            summarizer_agent_config = json.loads(f.read())
        agents["summarizer"] = summarizer_agent
        # Reflection question
        ref_q_agent_config = None
        with open(ref_q_agent_config_path, "r") as f:
            ref_q_agent_config = json.loads(f.read())
        # Reflection
        ref_agent_config = None
        with open(ref_agent_config_path, "r") as f:
            ref_agent_config = json.loads(f.read())
        agents["reflection"] = OneshotAgent(ref_agent_config)
        # Tool query
        tool_query_agent_config = None
        with open(tool_query_agent_config_path, "r") as f:
            tool_query_agent_config = json.loads(f.read())
        agents["tool_query"] = OneshotAgent(tool_query_agent_config)
        conflict_resolver_agent_config = None
        with open(conflict_resolver_agent_config_path, "r") as f:
            conflict_resolver_agent_config = json.loads(f.read())
        agents["conflict_resolver"] = OneshotAgent(
            conflict_resolver_agent_config)
        return agents

    def get_num_tokens_memory(self):
        return self._num_tokens_memory

    def get_domain_knowledge(self) -> List[Knowledge]:
        return self._domain_knowledge

    def get_commands(self) -> List[str]:
        return self._commands

    def get_reflections(self) -> List[Knowledge]:
        return self._reflections

    def get_memory(self) -> List[MemoryUnit]:
        return self._memory

    def get_query_term(self, seed) -> str:
        """ Extract search keywords from the query sentence.
        """
        return seed

    def update_context(self, prompt: str):
        logger.info(
            f"Preparing for running prompt {prompt}")
        # Get relevant knowledge
        keyword = self.get_query_term(prompt)
        logger.debug(f"search keywords for knowledge retrieval: {keyword}")
        new_knowledges = []
        if keyword:
            new_knowledges = self.connector.search_knowledge(
                self._agent.id, self._agent.get_embeds(keyword), token_limit=self.MAX_NUM_TOKENS_KNOWLEDGE)
        else:
            logger.debug(
                "Keyword is empty, fetching most recent knowledge instead")
            new_knowledges = self.connector.get_recent_knowledge(
                self._agent.id)
        self.update_local_knowledge(new_knowledges)
        # query for commands
        # self._commands = self.connector.search_commands(self._agent.get_embeds(keyword))
        # logger.debug("commands are", self._commands)

    def reflect(self, memory_text, context=None) -> List[Knowledge]:
        # context gives information on what job the agent is doing.
        logger.debug(f"Making reflection from {memory_text}")
        # Make reflection on compressed memory
        # Step1: Get attributes
        objects_attributes = attribute_question_agent.run(
            observations=memory_text)
        # Step2: Get attribute values
        attribute_values = attribute_agent.run(
            observations=memory_text, object_attributes=objects_attributes)
        observations = [
            f'{r["object"]} {r["attribute"]} {r["value"]}' for r in attribute_values]
        logger.info(f"observations are {observations}")
        new_knowledges = [Knowledge(int(time.time()), fact)
                          for fact in observations]
        # Get keywords from memory text
        keyword = self.get_query_term(memory_text)
        relevant_knowledges = self.connector.search_knowledge(
            self._agent.id, self._agent.get_embeds(keyword), token_limit=self.MAX_NUM_TOKENS_KNOWLEDGE)
        # Compare the facts in memory with the relevant knowledge, mark the ones that need to be updated
        knowledge_ids_to_remove = []
        if relevant_knowledges:
            observations_and_records = {
                "observations": ".".join(observations),
                "records": [k.to_json() for k in relevant_knowledges]
            }
            knowledges_to_remove = conflict_detector_agent.run(
                observations_and_records=observations_and_records)
            knowledge_ids_to_remove = [k["id"] for k in knowledges_to_remove]
        return new_knowledges, knowledge_ids_to_remove

    def _compress_memory(self, reflect=False) -> Tuple[List[MemoryUnit], List[Knowledge]]:
        """ Compress memory and maybe do reflection

        Reflection is implemented in a similar way as the Stanford paper
        """
        # Let LLM summarize the first half of the memory
        # context and domain knowledge should not be changed
        # compress half of the user <-> assistant interaction
        # locate the half memory point
        logger.info("memory before compressing is")
        logger.info(self.__str__())
        compress_until_index = 0
        current_num_tokens = 0
        for i, m in enumerate(self._memory):
            current_num_tokens += m.num_tokens
            if current_num_tokens > self._num_tokens_memory/2:
                compress_until_index = i
                break
        num_tokens_not_compressed = self._num_tokens_memory - current_num_tokens
        logger.debug(
            f"From {len(self._memory)} memory units, compressing from 0 to {compress_until_index}")
        memory_to_compress = self._memory[:(compress_until_index+1)]
        # Format memory to text
        memory_text = ""
        for m in memory_to_compress:
            memory_text += f"{m.role}: {m.content}\n"
        compressed_memory_content = summarizer_agent.run(
            text_to_summarize=memory_text)
        compressed_memory = MemoryUnit(
            "user",  f"A summary of our past conversation: {compressed_memory_content}")
        self._memory = [compressed_memory] + \
            self._memory[compress_until_index:]
        self._num_tokens_memory = num_tokens_not_compressed + compressed_memory.num_tokens
        logger.info("memory after compressing is")
        logger.info(self.__str__())
        self.extract_and_update_knowledge(memory_text)

        # reflections, ids_to_remove = self.reflect(memory_text)
        # # Remove knowledges
        # logger.debug(f"Removing ids {ids_to_remove} from knowledge base")
        # try:
        #     self.connector.remove_knowledge(self._agent.id, ids_to_remove)
        # except Exception as e:
        #     logger.warning(f"Failed to remove ids with error {e}")
        # # Save agent and add to knowledge
        # assert self.connector
        # for i, knowledge in enumerate(reflections):
        #     if knowledge.embeds:
        #         continue
        #     embeds = self._agent.get_embeds(knowledge.content)
        #     reflections[i].update_embeds(embeds)
        # self.connector.save_knowledge(self._agent.id, reflections)

        self.connector.update_longterm_memory(
            self._agent.id, memory_to_compress)
        # Update current agent
        self.update_agent()
        return memory_to_compress

    def extract_and_update_knowledge(self, data: str):
        """ Extracts knowledge from data and save it
        """
        logger.debug(f"Making reflection from data {data}")
        reflections, ids_to_remove = self.reflect(data)
        # Remove knowledges
        logger.debug(f"Removing ids {ids_to_remove} from knowledge base")
        try:
            self.connector.remove_knowledge(self._agent.id, ids_to_remove)
        except Exception as e:
            logger.warning(f"Failed to remove ids with error {e}")
        # Save agent and add to knowledge
        assert self.connector
        for i, knowledge in enumerate(reflections):
            if knowledge.embeds:
                continue
            embeds = self._agent.get_embeds(knowledge.content)
            reflections[i].update_embeds(embeds)
        self.connector.save_knowledge(self._agent.id, reflections)

    def update_agent(self):
        self.connector.update_agent(
            self._agent.id,
            self._agent.config,
            self._memory)

    def add_memory(self, memory: Dict[str, str]):
        new_memory = MemoryUnit(memory["role"], memory["content"])
        self._memory.append(new_memory)
        self._num_tokens_memory += new_memory.num_tokens
        if self._num_tokens_memory > self.MAX_NUM_TOKENS_MEMORY:
            self._compress_memory(reflect=True)

    def update_local_knowledge(self, knowledges: List[Knowledge]):
        for k in knowledges:
            self._num_tokens_domain_knowledge += k.num_tokens
            self._domain_knowledge.append(k)
            if self._num_tokens_domain_knowledge > self.MAX_NUM_TOKENS_KNOWLEDGE:
                break

    def delete_memory(self, memory_index: int):
        if memory_index >= len(self._memory):
            logger.debug(
                f"Deleting index {memory_index} out of range of 0-{len(self._memory)-1}")
            return
        if memory_index < 0:
            if memory_index + len(self._memory) - 1 < 0:
                logger.debug(
                    f"Deleting index {memory_index} out of range of 0-{len(self._memory)-1}")
                return
        self._num_tokens_memory -= self._memory[memory_index].num_tokens
        del self._memory[memory_index]

    def clear(self):
        self._memory = []

    def to_messages(self):
        domain_knowledge_str = ""
        if self._domain_knowledge:
            domain_knowledge_str = f"Your domain knowledge is between the below triple backsticks: ```{';'.join([k.content for k in self._domain_knowledge])}```"
        commands_str = ""
        # TODO: Maybe it shouldn't be pronounced as
        if self._commands:
            commands_str = f"""The external tools you can use is between the below triple backsticks```{
                ';'.join([c.to_prompt() for c in self._commands])
            }```"""
        commands_str = ""
        messages = []
        if self._agent.get_conversation_setup():
            messages.append({
                "role": "system",
                "content": self._agent.get_conversation_setup()
            })
        if domain_knowledge_str:
            messages.append({
                "role": "system",
                "content": domain_knowledge_str
            })
        if commands_str:
            messages.append({
                "role": "system",
                "content": commands_str
            })
        messages += [
            {
                "role": memory_unit.role,
                "content": memory_unit.content
            }
            for memory_unit in self._memory
        ]
        return messages

    def __str__(self) -> str:
        prefix = f'\n************* Memory({self._num_tokens_memory + self._num_tokens_context + self._num_tokens_domain_knowledge} tokens) *************\n'
        suffix = f'\n************* End of Memory *************\n'
        context_str = f'\n<context> [{self._num_tokens_context} tokens]: {self._agent.get_conversation_setup()}\n'
        knowledge_str = f"\n<knowledge>: [{self._num_tokens_domain_knowledge}]\n" + "\n----------------------\n".join(
            [k.__str__() for k in self.get_domain_knowledge()])
        memory_str = f"<memory> [{self._num_tokens_memory} tokens]:\n" + "\n----------------------\n".join(
            [m.__str__() for m in self.get_memory()])
        return prefix + context_str + knowledge_str + memory_str + suffix

    def __repr__(self):
        return self.__str__()

    def __deepcopy__(self, memodict={}):
        cpyobj = type(self)(self._agent)  # shallow copy of whole object
        cpyobj._domain_knowledge = copy.deepcopy(
            self._domain_knowledge, memodict)
        cpyobj._commands = copy.deepcopy(
            self._commands, memodict)
        cpyobj._memory = copy.deepcopy(self._memory, memodict)
        return cpyobj
