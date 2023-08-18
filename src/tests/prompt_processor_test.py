from agentware.base import PromptProcessor, OneshotAgent
from agentware.core_engines import CoreEngineBase

import unittest
import json


class PromptProcessorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_prompt_processor_simple(self):
        conversation_setup = "You are a name machine"
        prompt_template = PromptProcessor(conversation_setup,
                                          "Hi my name is {name}, my phone number is {phone}")
        assert (prompt_template.format(name="John", phone="12345")
                ) == "Hi my name is John, my phone number is 12345"

    def test_run_agent_without_output_schema(self):
        conversation_setup = "You are a name machine"
        prompt_processor = PromptProcessor(conversation_setup,
                                           "My name is {name}, do you know my number?")
        agent = OneshotAgent("name reader", prompt_processor)
        expected_output = "12345"

        class NumberFinderCoreEngine(CoreEngineBase):
            def run(self, prompt):
                return expected_output

        agent.set_core_engine(NumberFinderCoreEngine())
        assert agent.run(name="Joe") == expected_output

    def test_run_agent_with_output_schema(self):
        conversation_setup = "You are a name machine"
        output_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "phone_numbers": {
                    "type": "array",
                    "items": {
                        "type": "integer"
                    }
                }
            },
            "required": ["phone_numbers"],
            "additionalProperties": "false"
        }
        prompt_processor = PromptProcessor(conversation_setup,
                                           "My name is {name}, do you know my number?",
                                           output_schema)
        agent = OneshotAgent("name reader", prompt_processor)
        expected_output = {"phone_numbers": [12345, 678910]}

        class CorrectOutputCoreEngine(CoreEngineBase):
            def run(self, prompt):
                return json.dumps(expected_output)

        agent.set_core_engine(CorrectOutputCoreEngine())
        assert agent.run(name="Joe").items() == expected_output.items()

        class WrongOutputCoreEngine(CoreEngineBase):
            def run(self, prompt):
                return "some output"

        agent.set_core_engine(WrongOutputCoreEngine())
        assert agent.run(
            name="Joe") == "Sorry, I failed to generate the required json schema"


if __name__ == '__main__':
    unittest.main()
