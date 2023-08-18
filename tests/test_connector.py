from agentware.connector import Connector
from agentware.base import Knowledge, MemoryUnit
from test_memory import create_memory
from db_clients.memory_db_client import AGENT_KEY, AGENT_ID_COUNTER_KEY, USER_KEY, USER_ID_COUNTER_KEY, USER_AGENT_INDEX_KEY
import time
import json


def TestConnectorUpdateAgent(connector):
    connector = Connector(1)
    memory = create_memory(
        "./test_dataconfigsdocument_reader.json", connector)
    connector.connect(3)
    helper_agent_configs = {agent_name: agent.get_config()
                            for agent_name, agent in memory._helper_agents.items()}
    print("helpers are", helper_agent_configs)
    connector.create_agent()
    connector.update_agent(
        memory.get_main_agent_config(), helper_agent_configs, memory._memory)
    agent_config, helper_configs, memory_data, knowledge_data, context = connector.get_agent(
        connector.get_agent_id())
    print("agent config", agent_config)
    print("helper agent configs", helper_configs)
    print("memory data", memory_data)
    print("knowledge data", knowledge_data)
    print("context", context)
    print("helper agents", memory._helper_agents)


def TestGetTokenSuccess(connector: Connector):
    print("token is", connector.get_token())


def TestCreateAgentSuccess(connector: Connector):
    print("create agent id is", connector.create_agent())


def TestGetAgentSuccess(connector: Connector):
    print("Agent data is", connector.get_agent(3))


def TestListAgentsSuccess(connector: Connector):
    print("agent ids are", connector.all_agents())


def TestGetLongtermMemorySuccess(connector: Connector):
    print("longterm memory is", connector.get_longterm_memory(3, 0, 7))


def TestUpdateLongtermMemorySuccess(connector: Connector):
    memory_units = [
        MemoryUnit("user", "hello"),
        MemoryUnit("assistant", "Hi")
    ]
    print("updated longterm memory",
          connector.update_longterm_memory(3, memory_units))


def TestUpdateAgentSuccess(connector: Connector):
    data = {
        "agent_config": {"name": "xx", "conversation_setup": "ppppp"},
        "helper_agent_configs": [{"name": "summarizer"}],
        "memory_data": [MemoryUnit("assistant", "some memory")],
        "knowledge": [Knowledge(112358, "some content")],
        "context": "some context"
    }
    agent_config = data["agent_config"]
    helper_agent_configs = data["helper_agent_configs"]
    memory_data = data["memory_data"]
    print("update agent result is", connector.update_agent(
        agent_config, helper_agent_configs, memory_data))


def TestSaveKnowledgeSuccess(connector: Connector):
    knowledges = [
        Knowledge(12345, "some knowledge"),
        Knowledge(678910, "a secret")
    ]
    print("save knowledge result is",
          connector.save_knowledge(3, knowledges))


def TestSearchKnowledge(connector: Connector):
    print("search knowledge result is",
          connector.search_knowledge(3, "Karl Marx", 100))


def TestSearchCommand(connector: Connector):
    print("seaarch command result is",
          connector.search_commands("java", 100))


if __name__ == "__main__":
    # knowledges = [
    #     Knowledge(time.time(), "some knowledge")
    # ]
    config = None
    with open("test_data/connector_configs/sample_connector.json", "r") as f:
        config = json.loads(f.read())
    connector = Connector(config)
    TestGetTokenSuccess(connector)
    TestCreateAgentSuccess(connector)
    TestListAgentsSuccess(connector)
    TestUpdateLongtermMemorySuccess(connector)
    TestGetLongtermMemorySuccess(connector)
    TestUpdateAgentSuccess(connector)
    TestGetAgentSuccess(connector)
    TestSaveKnowledgeSuccess(connector)
    TestSearchKnowledge(connector)
    # connector._db_client.agent_client.delete(AGENT_KEY)
    # connector._db_client.agent_client.delete(AGENT_ID_COUNTER_KEY)
    # connector._db_client.user_client.delete(USER_KEY)
    # connector._db_client.user_client.delete(USER_ID_COUNTER_KEY)
    # connector._db_client.user_client.delete(USER_AGENT_INDEX_KEY)
    # user_id = connector._db_client.create_user({
    #     "name": "John",
    #     "api_key": "feawfaeaweaw"
    # })
    # assert user_id == 1
    # agent_id = connector._db_client.create_agent(user_id)
    # agents = connector.all_agents(user_id)
    # print("agents are", agents)
    # selected_agent_id = agents[0]["id"]
    # connector.connect(selected_agent_id)
