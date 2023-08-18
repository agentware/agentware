from agentware.utils.num_token_utils import get_num_tokens
from typing import Dict, List
from pymilvus import Collection, DataType, FieldSchema, CollectionSchema
from agentware import EMBEDDING_DIM
from agentware.base import BaseMilvusStore, Node
from agentware.agent_logger import Logger

logger = Logger()


class KnowledgeGraphIndexVectorStore(BaseMilvusStore):
    def __init__(self) -> None:
        super().__init__()

    def __init__(self, cfg: Dict[str, any]) -> None:
        super().__init__(cfg)

    def _create_collection(self, collection_name: str) -> Collection:
        id_field = FieldSchema(name="id", dtype=DataType.INT64,
                               is_primary=True, description="auto id", auto_id=True)
        name_field = FieldSchema(
            name="name", dtype=DataType.VARCHAR, max_length=65535, description="name of this command")
        created_at_field = FieldSchema(
            name="created_at", dtype=DataType.INT64,  description="unix seconds, publish time")
        vector_field = FieldSchema(
            name="vector", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)

        schema = CollectionSchema(fields=[id_field, name_field, created_at_field, vector_field],
                                  auto_id=True,
                                  description="The collection that stores all the information of commands")
        collection = Collection(
            name=collection_name, schema=schema)
        index_params = {"index_type": "IVF_FLAT",
                        "metric_type": "L2", "params": {"nlist": self.nlist}}
        collection.create_index(
            field_name=vector_field.name, index_params=index_params)
        return collection

    def get_node_id(self, node: Node, collection_name: str):
        self.check_and_maybe_create_collection(collection_name)
        try:
            c = Collection(collection_name)
            query_expr = f'name == "{node.name}"'
            query_result = c.query(query_expr)
            id = query_result[0]["id"]
            return id
        except:
            return None

    def insert_node(self, node: Node, collection_name: str):
        self.check_and_maybe_create_collection(collection_name)
        print(
            f"Inserting node {node} to collection {collection_name}")
        if not node:
            logger.warning("Node invalid")
            return
        if not node.embeds:
            logger.warning(
                f"node {node} has empty embeds. Insertion must be done with embedding")
            return
        try:
            name = [node.name]
            embeds = [node.embeds]
            created_at = [node.created_at]
            entities = [name, created_at, embeds]
            c = Collection(collection_name)
            c.insert(entities)
            c.flush()
            # Get the inserted id
            query_expr = f'name == "{node.name}"'
            query_result = c.query(query_expr)
            logger.debug(
                f"query result for name {node.name} is {query_result}")
            vector_store_id = query_result[0]["id"]
            logger.debug(
                f"Saved node {node} to collection {collection_name}. id: {vector_store_id}")
            return vector_store_id
        except Exception as err:
            logger.debug(f"Failed to insert node with error {err}")
            return err

    def query_by_name(self, name: str, collection_name: str) -> bool:
        self.check_and_maybe_create_collection(collection_name)
        c = Collection(collection_name)
        results = c.query(
            expr='name == "{}"'.format(name),
            output_fields=["id", "name", "created_at", "vector"])
        if results:
            return results[0]
        return None

    def search_node(self,  collection_name: str, query_embeds: List[float]) -> List[Dict]:
        self.check_and_maybe_create_collection(collection_name)
        results = self._similarity_query(
            query_embeds, collection_name, ["id", "name", "created_at"])
        retrived_nodes = []
        for result in results[0]:
            id = result.entity.get('id')
            name = result.entity.get('name')
            created_at = result.entity.get('created_at')
            retrived_nodes.append(
                {"created_at": created_at, "name": name, "id": id})
        return retrived_nodes
