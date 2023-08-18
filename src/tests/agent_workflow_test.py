import unittest

from agentware import hub
from agentware.base import PromptProcessor
from agentware.agent import Agent
from agentware.agent_logger import Logger
from utils import DbClient, FakeCoreEngine, SummarizerCoreEngine, FactCoreEngine
logger = Logger()

AGENT_ID = "test agent"
PROMPT_PROCESSOR = PromptProcessor(
    "You are DarthJaja, an AI assistant who lives in the universe of Star Wars series and knows everything about this world", "")


class AgentWorkflowTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_client = DbClient()
        cls.main_core_engine = FakeCoreEngine("software " * 200)
        cls.summarizer_core_engine = FakeCoreEngine(
            "{\"summary\": \"this is a summary\"}")

    def setUp(self):
        self.db_client.client.flushall()

    def tearDown(self):
        pass

    def test_register_agent(self):
        agent_id = "some agent idz"
        hub.register_agent(agent_id)
        agent_ids = hub.list_agents()
        print('agents are', agent_ids)
        assert agent_ids[0] == agent_id

    def test_duplicate_register_fail(self):
        agent_id = "some_agent_id"
        hub.register_agent(agent_id)
        self.assertRaises(ValueError, hub.register_agent, agent_id)

    def test_fail_to_fetch_unexist(self):
        self.assertRaises(ValueError, Agent.pull, "some/unexisted")

    def test_register_and_push_and_fetch_and_run_agent(self):
        agent = Agent(AGENT_ID)
        agent.register()
        agent.push()
        agents = hub.list_agents()
        print("agents are", agents)
        assert agents[0] == AGENT_ID
        updated_agent = Agent.pull(AGENT_ID)
        assert updated_agent.get_id() == AGENT_ID

    def test_agent_exist_remove(self):
        agent_id = "some_agent_name"
        assert not hub.agent_exists(agent_id)
        agent = Agent()
        agent.register(agent_id)
        assert agent.exists()
        # 还需要删除milvus
        agent.remove()
        assert not agent.exists()

    def test_memory_compression(self):
        agent = Agent(TEST_CFG)
        agent.set_core_engine(self.main_core_engine)
        agent._memory._helper_agents["summarizer"].set_core_engine(
            SummarizerCoreEngine())
        agent._memory._helper_agents["fact"].set_core_engine(
            FactCoreEngine())
        for i in range(10):
            agent.run("What is your name?")

    def test_agent_reflection_run_in_update_mode(self):
        agent = Agent(AGENT_ID, PROMPT_PROCESSOR)
        assert agent._update_mode == False
        with agent.update():
            assert agent._update_mode == True
            agent.run("What is your name?")
        assert agent._update_mode == False


if __name__ == '__main__':
    unittest.main()
