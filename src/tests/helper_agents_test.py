import unittest
import os
import json

from agentware.base import OneshotAgent
from agentware.agent_logger import Logger
from agentware import HELPER_AGENT_CONFIGS_DIR_NAME
from agentware.core_engines import CoreEngineBase
from agentware.helper_agents import summarizer_agent, attribute_question_agent, attribute_agent
from utils import DbClient, FakeCoreEngine
logger = Logger()


def get_config(config_fname):
    config_dir_absolute_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "agentware", HELPER_AGENT_CONFIGS_DIR_NAME)
    with open(f"{config_dir_absolute_path}/{config_fname}", "r") as f:
        config = json.loads(f.read())
    return config


class HelperAgentTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_client = DbClient()
        cls.fake_core_engine = FakeCoreEngine()

    def setUp(self):
        self.db_client.client.flushall()

    def tearDown(self):
        pass

    def test_summarizer_agent(self):
        expected_output = {
            "output": "summary of text"
        }

        class SummarizerCoreEngine(CoreEngineBase):
            def run(self, prompt):
                return json.dumps(expected_output)
        summarizer_agent.set_core_engine(SummarizerCoreEngine())
        assert summarizer_agent.run(
            text_to_summarize="some text") == expected_output

    def test_attribute_question_agent(self):
        expected_output = {
            "output":
                [
                    {
                        "name": "some name",
                        "attribute": "some attributes",
                        "reason": "the age of old joe is mentioned in the context"
                    }
                ]
        }

        class AttributeQuestionCoreEngine(CoreEngineBase):
            def run(self, prompt):
                return json.dumps(expected_output)
        attribute_question_agent.set_core_engine(AttributeQuestionCoreEngine())
        assert attribute_question_agent.run(
            observations="some text") == expected_output

    def test_attribute_agent(self):
        expected_output = {
            "output":
                [
                    {
                        "name": "some name",
                        "description": "some attributes"
                    }
                ]
        }

        class AttributeCoreEngine(CoreEngineBase):
            def run(self, prompt):
                return json.dumps(expected_output)
        attribute_agent.set_core_engine(AttributeCoreEngine())
        assert attribute_agent.run(
            observations="some text", object_attributes=[{"name": "some object", "attribute": "some attribute"}]) == expected_output

    def test_conflict_resolver_agent(self):
        config = get_config("conflict_resolver.json")
        agent = OneshotAgent(config)

        class ConflictResolverCoreEngine(CoreEngineBase):

            def run(self, prompt):
                return '{"wrong_facts": [2]}'
        agent.set_core_engine(ConflictResolverCoreEngine())
        result = agent.run(
            '{"observations": ["Daenerys bought the dragon"], "facts": [{"id": 2, "fact": "Daenerys has nothing"}, {"id": 3, "fact": "John snow is playing basketball with a dragon"}]}')
        assert result == "[2]"

    def test_status_questions(self):
        config = get_config("attribute_question.json")
        agent = OneshotAgent(config)
        result = agent.run(
            "Mom bought a fish just now. It's on the second layer of the fridge. Dad turned the TV on. Ok, I moved it to a plate on the table. Dad turned the TV off.")
        print("result is", result)

    def test_fact(self):
        config = get_config("detector.json")
        agent = OneshotAgent(config)
        result = agent.run(
            "Mom bought a fish just now. It's on the second layer of the fridge. Dad turned the TV on. Ok, I moved it to a plate on the table. Dad turned the TV off.")
        print("result is", result)


if __name__ == '__main__':
    unittest.main()
