import redis
import json

from typing import List, Dict, Tuple
from agentware.agent_logger import Logger

LONG_MEMORY_KEY = "memory"
AGENT_KEY = "agent"

AGENT_ID_COUNTER_KEY = "agent_id_counter"

logger = Logger()


class DbClient:
    def __init__(self, config: Dict[str, str]):
        if not config:
            raise BaseException("Invalid db client config")
        # Establish a connection to the Redis server
        self.redis_host = config['ip']
        self.redis_port = int(config['port'])
        self.redis_password = None

        self.client = redis.Redis(
            host=self.redis_host, port=self.redis_port, password=self.redis_password)

    def _create_auto_incr_entry(self, client: redis.Redis, key: str, counter_key: str, value: Dict[any, any]):
        current_entity_id = None
        # Start a Redis transaction
        with client.pipeline() as pipe:
            while True:
                try:
                    # Watch the counter key to detect changes
                    pipe.watch(counter_key)
                    # Get the current value of the counter
                    current_entity_id = pipe.get(counter_key)
                    if current_entity_id is None:
                        # If the counter doesn't exist, initialize it to 1
                        current_entity_id = 1
                    else:
                        # Increment the counter by 1
                        current_entity_id = int(current_entity_id) + 1
                    # Update the counter key with the new value
                    pipe.multi()
                    pipe.set(counter_key, current_entity_id)
                    # Insert user information with the generated ID
                    pipe.hmset(f'{key}:{current_entity_id}', value)
                    # Execute the transaction
                    pipe.execute()
                    # Break out of the loop since the transaction was successful
                    break
                except redis.WatchError:
                    # Another process modified the  key during the transaction
                    continue
        return current_entity_id

    def register_agent(self, agent_id: str):
        agent_exists = self.client.exists(agent_id)
        if agent_exists:
            logger.debug(f"Agent {agent_id} exists")
            return True
        self.client.set(agent_id, "")
        return False

    def agent_exists(self, agent_id: str):
        return self.client.exists(agent_id)

    def remove_agent(self, agent_id: str):
        agent_exists = self.client.exists(agent_id)
        if not agent_exists:
            logger.debug(f"Agent {agent_id} does not exist")
        else:
            self.client.delete(agent_id)

    def all_agents(self):
        return self.client.keys()

    def get_agent(self, agent_id: int) -> Tuple[Dict[any, any], Dict[str, any], List[Dict], List[Dict], str]:
        print("agent id is", agent_id)
        memory_agent_json = self.client.get(agent_id)
        print("memory agent json is", memory_agent_json)
        if memory_agent_json is None:
            return None, None
        memory_agent_json = memory_agent_json.decode()
        if memory_agent_json == '':
            return dict(), []
        memory_agent = json.loads(memory_agent_json)
        return memory_agent["agent_config"], memory_agent["memory"]

    def update_agent(self, agent_id: str, agent_config: Dict[any, any], memory_units: List[Dict]):
        # Working memory is completely replaced
        working_memory = {
            "agent_config": agent_config,
            "memory": memory_units
        }
        print("saved working memory is", working_memory)
        serialized_working_memory = json.dumps(working_memory)
        # Push each serialized dog to the list
        self.client.set(
            agent_id, serialized_working_memory)

    def save_longterm_memory(self, agent_id: int, memory_units: List[Dict]):
        transaction = self.client.pipeline()
        for m in memory_units:
            serialized_memory = json.dumps(m)
            # Push each serialized dog to the list
            transaction.rpush(
                f"{LONG_MEMORY_KEY}:{agent_id}", serialized_memory)
        # Execute the Redis transaction
        transaction.execute()

    def get_longterm_memory(self, agent_id: int, page_number, page_size) -> List[Dict]:
        start_index = page_number * page_size
        end_index = start_index + page_size - 1
        print(f"{start_index} -> {end_index}")
        memory_values = self.client.lrange(
            f"{LONG_MEMORY_KEY}:{agent_id}", start_index, end_index)
        print("memory values is", memory_values)
        return [json.loads(m) for m in memory_values]
