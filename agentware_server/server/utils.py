import json
import time

from agentware.base import OneshotAgent
from agentware.memory import Memory, Knowledge


def create_memory(main_agent_config_path, connector):
    facts_agent_config_path = "./test_data/configsfacts.json"
    ref_q_agent_config_path = "./test_data/configsreflection_question.json"
    ref_agent_config_path = "./test_data/configsreflection.json"
    summarize_agent_config_path = "./test_data/configssummarize.json"
    tool_query_agent_config_path = "./test_data/configstool_query.json"

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
