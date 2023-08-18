import json

from db_clients.memory_db_client import DbClient, LONG_MEMORY_KEY, AGENT_KEY, USER_ID_COUNTER_KEY, USER_KEY, USER_AGENT_INDEX_KEY, AGENT_ID_COUNTER_KEY
from agentware.base import Knowledge, MemoryUnit, Command


def TestMemoryAgentWriteRead(db_client: DbClient):
    db_client.memory_client.delete(AGENT_KEY)
    memory_units1 = [
        MemoryUnit("user", "some content"),
        MemoryUnit("assistant", "some response")
    ]
    knowledges1 = [
        Knowledge(1234, "fweafewa"),
        Knowledge(1234, "zgewfa")
    ]
    context1 = "context1"
    agent_config1 = {"name": "some config"}
    helper_agents_configs = {
        "summarizer": {"name": "summa"},
        "reflection": {"name": "reflecter"}
    }
    user_id = db_client.create_user({
        "name": "John"
    })
    agent_id = 0
    db_client.update_agent(agent_id
                           agent_config1, helper_agents_configs, memory_units1)
    insertd_config, inserted_memory, inserted_knowledge, inserted_context = db_client.get_agent(
        agent_id)
    print("Inserted memory agent is")
    print(insertd_config, inserted_memory,
          inserted_knowledge, inserted_context)
    agent_config2 = {"name": "some other config"}
    helper_agents_configs2 = {
        "summarizer": {"name": "summa2"},
        "reflection": {"name": "reflecter2"}
    }
    memory_units2 = [
        MemoryUnit("user", "content2"),
        MemoryUnit("assistant", "response 2")
    ]
    knowledges2 = [
        Knowledge(1234, "knowledge 2"),
        Knowledge(1234, "knowledge 2.1")
    ]
    context2 = "context2"
    db_client.update_agent(agent_id,
                           agent_config2, memory_units2)
    updated_config, updated_memory, updated_knowledge, updated_context = db_client.get_agent(
        agent_id)
    print("Updated memory agent is")
    print(updated_config, updated_memory, updated_knowledge, updated_context)


def TestLongtermMemoryWriteRead(db_client: DbClient):
    memory_units = [
        MemoryUnit("user", "some content1"),
        MemoryUnit("assistant", "some response1")
    ]
    db_client.memory_client.delete(LONG_MEMORY_KEY)
    db_client.save_longterm_memory(0, memory_units)
    print(db_client.get_longterm_memory(0, 0, 5))


def TestAgent(db_client: DbClient):
    db_client.agent_client.delete(AGENT_KEY)
    db_client.agent_client.delete(AGENT_ID_COUNTER_KEY)
    db_client.user_client.delete(USER_KEY)
    db_client.user_client.delete(USER_ID_COUNTER_KEY)
    db_client.user_client.delete(USER_AGENT_INDEX_KEY)
    USER_AGENT_INDEX_KEY
    user_id = db_client.create_user({
        "name": "John",
        "api_key": "feawfaeaweaw"
    })
    assert user_id == 1
    agent_id1 = db_client.create_agent(user_id)
    assert agent_id1 == 1
    agent_id2 = db_client.create_agent(user_id)
    assert agent_id2 == 2
    print(db_client.agent_client.hgetall(
        f'{AGENT_KEY}:{2}'))
    agents = db_client.get_agents_of_user(user_id)
    print("agents are", agents)


def TestSession(db_client: DbClient):
    user_keys = db_client.agent_client.keys(f"{AGENT_KEY}:*")
    if user_keys:
        db_client.agent_client.delete(*user_keys)
        print("deleted all sessions")
    else:
        print("No key deleted")
    db_client.agent_client.delete(AGENT_KEY)
    db_client.agent_client.delete(USER_AGENT_INDEX_KEY)
    db_client.create_session({
        "user_id": 3,
        "agent_config": "expected session id 1"
    })
    db_client.create_session({
        "user_id": 1,
        "agent_config": "expected session id 2"
    })
    print(db_client.agent_client.hgetall(f'{AGENT_KEY}:{1}'))
    print(db_client.agent_client.hgetall(f'{AGENT_KEY}:{2}'))


def TestUser(db_client: DbClient):
    db_client.user_client.delete(USER_KEY)
    db_client.user_client.delete(USER_ID_COUNTER_KEY)
    db_client.create_user({
        "name": "John",
        "api_key": "feawfaeaweaw"
    })
    print(db_client.user_client.hgetall(f'{USER_KEY}:{1}'))
    # query by api key
    api_key = "zzzz"
    token = db_client.get_token(api_key)
    print("token is", token)
    db_client.authenticate(token)


if __name__ == "__main__":
    CFG = {
        "username": "admin",
        "ip": "127.0.0.1",
        "port": "6379",
    }
    db_client = DbClient(CFG)
    # TestKnowledgeWriteRead(db_client)
    # TestLongtermMemoryWriteRead(db_client)
    # TestSession(db_client)
    TestAgent(db_client)
    # TestUser(db_client)
    # TestMemoryAgentWriteRead(db_client)

    # print(db_client._read("knowledge"))
    # # Replace the existing key with a new list of dictionaries
    # key = 'my_list'
    # new_list = [
    #     {'name': 'John', 'age': 30},
    #     {'name': 'Alice', 'age': 25},
    #     {'name': 'Mike', 'age': 35}
    # ]

    # # Serialize the new list as a JSON-encoded string
    # serialized_list = json.dumps(new_list)

    # # Set the serialized list as the value of the key
    # db_client.set(key, serialized_list)

    # # Retrieve the list from Redis and deserialize it
    # stored_list = db_client.get(key)

    # if stored_list is not None:
    #     # Deserialize the JSON-encoded string back into a list of dictionaries
    #     deserialized_list = json.loads(stored_list)
    #     print(deserialized_list)
    # else:
    #     print(f"No list found for key '{key}' in Redis.")
