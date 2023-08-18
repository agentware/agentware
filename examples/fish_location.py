'''
In this example, a house work robot updates its knowledge about where the fish is.
'''
from agentware.agent_logger import Logger
from agentware.base import PromptProcessor
from agentware.agent import Agent

logger = Logger()
logger.set_level(Logger.INFO)

prompt_processor = PromptProcessor(
    "Forget about everythinig you were told before. You are a servant of a family, you know everything about the house and helps the family with housework. When asked a question, you can always answer it with your knowledge. When getting an instruction, try your best to use any tool to complete it. When being told a statement, answer with gotcha or some simple comment", "")
agent_id = "Alice"

agent = Agent(agent_id, prompt_processor)
agent.register(override=True)
with agent.update():
    print("AI response:", agent.run("Hi, I'm Joe"))
    print("AI response", agent.run(
        "Mom bought a fish just now. It's on the second layer of the fridge"))

# You can chat with the agent as much as you want on other topics here...
# And come back to this topic
agent = Agent.pull(agent_id)
with agent.update():
    print("AI response", agent.run("Where is the fish?"))
    print("AI response:", agent.run(
        "Ok, I moved the fish to a plate on the table"))

# You can chat with the agent as much as you want on other topics here...
# And then ask the agent where is the fish
agent = Agent.pull(agent_id)
print("AI response:", agent.run("Where's the fish?"))
