from agentware.agent_logger import Logger
from agentware.memory import Memory
from agentware.base import BaseAgent
from agentware.hub import register_agent, remove_agent, agent_exists
import openai
import json
import copy
from functools import reduce
import traceback
import agentware


logger = Logger()


class Agent(BaseAgent):
    LEARN_TEXT_CHUN_SIZE = 1000

    @classmethod
    def pull(cls, agent_id: int):
        agent = cls(agent_id)
        memory = Memory.pull(agent_id, agent)
        logger.info(f"Pulled agent config is {agent.config}")
        agent.memory = memory
        return agent

    def __init__(self, id, prompt_processor=None):
        """ Creates a new agent instead of fetching from connector
        """
        super().__init__(id, prompt_processor)
        self._memory = Memory(self)
        self._update_mode = False

    def set_id(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def update(self):
        return self.UpdateContext(self)

    class UpdateContext:
        def __init__(self, obj):
            self.obj = obj

        def __enter__(self):
            self.obj._update_mode = True
            return self.obj

        def __exit__(self, exc_type, exc_val, exc_tb):
            # update knowledge
            self.obj.push()
            self.obj._update_mode = False

    def run(self, *args, **kwargs):
        output_valid = False
        num_retries = 0
        raw_output = ""
        # send values to domain knowledge search
        prompt = self._prompt_processor.format(*args, **kwargs)
        self._memory.update_context(prompt)
        self._memory.add_memory({
            "role": "user",
            "content": prompt
        })
        memory_with_error = copy.deepcopy(self._memory)
        logger.info(f"Copy of memory made: {memory_with_error}")
        while True:
            if num_retries > 0:
                logger.debug(f"Retrying for the {num_retries} time")
            try:
                messages = memory_with_error.to_messages()
                raw_output = self._run(messages)
                try:
                    output = self._prompt_processor.parse_output(raw_output)
                    logger.debug(f"Adding response to memory: {output}")
                    self._memory.add_memory({
                        "role": "assistant",
                        "content": output
                    })
                    output_valid = True
                    return output
                except Exception as err:
                    logger.warning(f"Error parsing with exception {err}")

                    traceback.print_exc()
                    if num_retries >= 1:
                        # Delete the previous error information
                        memory_with_error.delete_memory(-1)
                        memory_with_error.delete_memory(-1)
                    memory_with_error.add_memory({
                        "role": "assistant",
                        "content": raw_output
                    })
                    memory_with_error.add_memory({
                        "role": "user",
                        "content": "Failed to parse output. Your content is great, regenerate with the same content in a format that aligns with the requirements and example schema."
                    })
            except Exception as e:
                logger.warning(f"Error getting agent output with error {e}")
            if output_valid or num_retries >= self.MAX_NUM_RETRIES:
                break
            num_retries += 1

    def clear_memory(self):
        self._memory.clear()

    def register(self, override=False):
        if agent_exists(self.id):
            if override:
                remove_agent(self.id)
            else:
                raise ValueError(f"Agent with id {self.id} exists")
        register_agent(self.id)

    def learn(self, text: str):
        for i in range(0, self.LEARN_TEXT_CHUN_SIZE, len(text)):
            chunk = text[i:(i+self.LEARN_TEXT_CHUN_SIZE)]
            logger.debug("Adding chunk to memory")
            self._memory.add_memory({
                "role": "user",
                "content": chunk
            })
        memory_text = ""
        for m in self._memory.get_memory():
            memory_text += f"{m.role}: {m.content}\n"
        self._memory.extract_and_update_knowledge(memory_text)
        self._memory.update_agent()
        self._memory.clear()

    def push(self):
        # Check agent id valid
        assert self.id
        logger.debug(
            f"Pushing agent {self.id} wth memory {self._memory.get_memory()}")
        # Digest memory
        memory_text = ""
        for m in self._memory.get_memory():
            memory_text += f"{m.role}: {m.content}\n"
        logger.debug(f"Memory text is {memory_text}")
        self._memory.extract_and_update_knowledge(memory_text)
        logger.debug(f"Pushing agent with name {self.id}")
        self._memory.update_agent()
        self._memory.clear()
