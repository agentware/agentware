import json
import time

from agentware.base import OneshotAgent, MemoryUnit, Knowledge
from agentware.connector import Connector
from agentware.memory import Memory


def create_memory(main_agent_config_path, connector):
    facts_agent_config_path = "./test_dataconfigsfacts.json"
    ref_q_agent_config_path = "./test_dataconfigsreflection_question.json"
    ref_agent_config_path = "./test_dataconfigsreflection.json"
    summarize_agent_config_path = "./test_dataconfigssummarize.json"
    tool_query_agent_config_path = "./test_dataconfigstool_query.json"

    agents = dict()
    fact_agent_config = None
    with open(facts_agent_config_path, "r") as f:
        fact_agent_config = json.loads(f.read())
    agents["fact"] = OneshotAgent(fact_agent_config)
    # Summarize agent
    summarizer_agent_config = None
    with open(summarize_agent_config_path, "r") as f:
        summarizer_agent_config = json.loads(f.read())
    agents["summarizer"] = OneshotAgent(summarizer_agent_config)
    # Reflection question
    ref_q_agent_config = None
    with open(ref_q_agent_config_path, "r") as f:
        ref_q_agent_config = json.loads(f.read())
    agents["reflection_q"] = OneshotAgent(ref_q_agent_config)
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

    main_agent_config = None
    with open(main_agent_config_path, "r") as f:
        main_agent_config = json.loads(f.read())
    if "conversation_setup" in main_agent_config:
        context = main_agent_config["conversation_setup"]
    domain_knowledge = [
        Knowledge(f"{int(time.time())}",
                  "Commonly used tools are Google, Python"),
        Knowledge(f"{int(time.time())}", "Keep answers short")
    ]
    memory_data = []
    memory = Memory(main_agent_config, agents, context,
                    domain_knowledge, memory_data, connector)
    return memory


def TestSaveLoadMemoryAgent(memory, connector):
    pass


if __name__ == "__main__":
    connector = Connector(1)
    memory = create_memory(
        "./test_dataconfigsdocument_reader.json", connector)
    connector.connect(3)
    helper_agent_configs = {agent_name: agent.get_config()
                            for agent_name, agent in memory._helper_agents.items()}
    print("helpers are", helper_agent_configs)
    connector.update_agent(1,
                           memory.get_main_agent_config(), memory._memory)
    agent_config, helper_configs, memory_data, knowledge_data, context = connector.get_agent(
        connector.get_agent_id())
    print("agent config", agent_config)
    print("helper agent configs", helper_configs)
    print("memory data", memory_data)
    print("knowledge data", knowledge_data)
    print("context", context)
    print("helper agents", memory._helper_agents)
