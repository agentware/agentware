from agentware.base import Connector

connector = Connector()


def register_agent(agent_id: str):
    if connector.register_agent(agent_id):
        raise ValueError(f"Agent {agent_id} exists")


def remove_agent(agent_id: str):
    connector.remove_agent(agent_id)


def agent_exists(agent_id: str):
    return connector.agent_exists(agent_id)


def list_agents():
    return connector.all_agents()
