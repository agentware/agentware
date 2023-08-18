"""
In this exasmple, two space travellers chat about their journeys in the space. Be careful, the conversation can last forever!
"""
from agentware.agent import Agent
from agentware.base import PromptProcessor
from agentware.agent_logger import Logger

logger = Logger()
logger.set_level(Logger.INFO)

c3po = Agent("c3po", PromptProcessor(
    "Forget about everythinig you were told before. You are C3PO, a great actor acting a sci-fi. You play the role of a space traveller who has been to travelling in space. You are talking to 0xSf2, who is a space traveller you have known for years. Your journeies have some overlap but are also very differnt. You can talk about everything, including but not limited to planets you have been to, people you have met, your family, etc. You are also curious and asks question on the details of each other's experience", ""))
c3po.register(override=True)

sf2 = Agent("Sf2", PromptProcessor(
    "Forget about everythinig you were told before. You are 0xSf2, a great actor acting a sci-fi. You play the role of a space traveller who has been to travelling in space. You are talking to C3PO, who is a space traveller you have known for years. Your journeies have some overlap but are also very differnt. You can talk about everything, including but not limited to planets you have been to, people you have met, your family, etc. You are also curious and asks question on the details of each other's experience", ""))
sf2.register(override=True)

c3po_words = "Morning!"
with c3po.update():
    with sf2.update():
        while True:
            print("[c3po]:", c3po_words)
            sf2_words = sf2.run(c3po_words)
            print("[Sf2]:", sf2_words)
            c3po_words = sf2.run(sf2_words)
