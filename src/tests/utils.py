import redis
import random
import os
import random
import json

from agentware.core_engines import CoreEngineBase
from agentware import EMBEDDING_DIM

EMBEDS_FNAME = "data/embeds.json"


class FakeCoreEngine(CoreEngineBase):
    def __init__(self, response: str = "") -> None:
        super().__init__()
        embeds_fpath = os.path.join(os.path.abspath(
            os.path.dirname(__file__)), EMBEDS_FNAME)
        with open(embeds_fpath, "r") as f:
            self._embeddings = json.loads(f.read())
        self.response = response

    def get_embeds(self, text: str):
        if not text in self._embeddings:
            self._embeddings[text] = [
                random.uniform(-1, 1) for i in range(EMBEDDING_DIM)]
        return self._embeddings[text]

    def get_sentences(self):
        return self._embeddings.keys()

    def run(self, prompt):
        return f"{self.response}"


class SummarizerCoreEngine(CoreEngineBase):

    def run(self, prompt):
        return "{\"summary\": \"this is a summary\"}"


class ReflectionCoreEngine(CoreEngineBase):

    def run(self, prompt):
        return "{\"reflections\": \"this is a summary\"}"


class FactCoreEngine(CoreEngineBase):

    def run(self, prompt):
        return "{\"facts\": [\"fact1\", \"fact2\"]}"


class DbClient:
    def __init__(self):
        self.redis_host = "localhost"
        self.redis_port = 6379

        self.client = redis.Redis(
            host=self.redis_host, port=self.redis_port)
