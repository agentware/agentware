from typing import Dict, List
from pymilvus import Collection, DataType, FieldSchema, CollectionSchema
from agentware import EMBEDDING_DIM
from agentware.base import BaseMilvusStore, Command
from agentware.utils.num_token_utils import get_num_tokens


class CommandsVectorStore(BaseMilvusStore):
    def __init__(self) -> None:
        super().__init__()

    def __init__(self, cfg: Dict[str, any]) -> None:
        super().__init__(cfg)

    def _create_collection(self, collection_name: str) -> Collection:
        id_field = FieldSchema(name="id", dtype=DataType.INT64,
                               is_primary=True, description="auto id")
        name_field = FieldSchema(
            name="name", dtype=DataType.VARCHAR, max_length=65535, description="name of this command")
        description_field = FieldSchema(
            name="description", dtype=DataType.VARCHAR, max_length=65535, description="description of this command")
        endpoint_field = FieldSchema(
            name="endpoint", dtype=DataType.VARCHAR, max_length=65535, description="http endpoint of this tool")
        input_field = FieldSchema(
            name="input_schema", dtype=DataType.VARCHAR, max_length=65535, description="The required json schema of the input data")
        output_field = FieldSchema(
            name="output_schema", dtype=DataType.VARCHAR, max_length=65535, description="The required json schema of the output data")
        created_at_field = FieldSchema(
            name="created_at", dtype=DataType.INT64,  description="unix seconds, publish time")
        vector_field = FieldSchema(
            name="vector", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)

        schema = CollectionSchema(fields=[id_field, name_field, description_field, endpoint_field, input_field, output_field, created_at_field, vector_field],
                                  auto_id=True,
                                  description="The collection that stores all the information of commands")
        collection = Collection(
            name=collection_name, schema=schema)
        index_params = {"index_type": "IVF_FLAT",
                        "metric_type": "L2", "params": {"nlist": self.nlist}}
        collection.create_index(
            field_name=vector_field.name, index_params=index_params)
        return collection

    def insert_commands(self, command_list: List[Command], collection_name: str):
        self.check_and_maybe_create_collection(collection_name)
        print(
            f"Inserting commands {[c.name for c in command_list]}")
        if not command_list:
            return
        try:
            print("command is", command_list[0].created_at)
            name = [command.name for command in command_list]
            description = [command.description for command in command_list]
            endpoint = [command.endpoint for command in command_list]
            input_schema = [command.input_schema for command in command_list]
            output_schema = [command.output_schema for command in command_list]
            created_at = [command.created_at for command in command_list]
            embeds = [command.embeds for command in command_list]
            entities = [name, description, endpoint, input_schema,
                        output_schema, created_at, embeds]
            c = Collection(collection_name)
            ins_resp = c.insert(entities)
            print(ins_resp)
        except Exception as err:
            print("get err {}".format(err))
            return err

    def search_command(self, collection_name: str, query_embeds: List[float], token_limit) -> List[Dict]:
        self.check_and_maybe_create_collection(collection_name)
        results = self._similarity_query(
            query_embeds, collection_name, ["name", "description", "endpoint", "input_schema", "output_schema"])
        retrieved_commands = []
        total_num_tokens = 0
        for result in results[0]:
            name = result.entity.get('name')
            description = result.entity.get('description')
            endpoint = result.entity.get('endpoint')
            input_schema = result.entity.get('input_schema')
            output_schema = result.entity.get('output_schema')
            print("command name is", name)
            num_tokens = get_num_tokens(name)
            total_num_tokens += num_tokens
            print("num tokens, total", num_tokens, total_num_tokens)
            if total_num_tokens > token_limit:
                break
            retrieved_commands.append(
                Command(name, description, endpoint, input_schema, output_schema))
        return retrieved_commands

    def query_by_name(self, url: str, collection_name: str) -> bool:
        self.check_and_maybe_create_collection(collection_name)
        c = Collection(collection_name)
        # query_embedding = None
        # search_params = {“nprobe”: 16}
        results = c.query(
            expr='name == "{}"'.format(url),
            output_fields=["id", "name", "description", "created_at", "vector"])
        if results:
            return results[0]
        return None

    def query_after_create_time(self, since_time: int) -> List[any]:
        c = Collection(collection_name)
        # query_embedding = None
        # search_params = {“nprobe”: 16}
        results = c.query(
            expr='created_at > {}'.format(since_time),
            output_fields=["id", "url", "content", "published_at"])
        if results:
            return results
        return []
