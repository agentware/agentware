from agentware.agent_logger import Logger
from neo4j import GraphDatabase
from typing import List, Dict, Tuple
from pymilvus import Collection, DataType, FieldSchema, CollectionSchema, connections, utility
from server.vector_db_clients.knowledge_graph_index_vector_db import KnowledgeGraphIndexVectorStore
from agentware.base import Node
from agentware.utils.num_token_utils import get_num_tokens

logger = Logger()


class KnowledgeGraphClient:
    def __init__(self, config: Dict):
        # Create vector db client
        vector_db_config = config['vector_db_config']
        self.vector_db_client = KnowledgeGraphIndexVectorStore(
            vector_db_config)
        # Create Neo4j client
        neo4j_config = config['neo4j']
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_config['uri'], auth=tuple(neo4j_config['auth']))

    def _get_or_insert_node(self, node: Node, collection_name, get_embedding_func):
        vector_store_id = self.vector_db_client.get_node_id(
            node, collection_name)
        if vector_store_id:
            logger.debug(
                f"node {node} already existed with id {vector_store_id}")
            return vector_store_id
        else:
            logger.debug(f"node {node} doesn't exist, inserting new")
        node.embeds = get_embedding_func(node.name)
        vector_store_id = self.vector_db_client.insert_node(
            node, collection_name)
        with self.neo4j_driver.session() as session:
            # Store Milvus ID in Neo4j
            session.run("""
            MERGE (n:Node {name: $node, collection_name: $collection_name})
            SET n.vector_store_id = $vector_store_id
            """, {"node": node.name, "vector_store_id": vector_store_id, "collection_name": collection_name})
            logger.debug(
                f"Inserted node {node} with vector store id: {vector_store_id}")
            return vector_store_id

    def insert_relation(self, triplet: Tuple[Node, str, Node], collection_name, get_embedding_func):
        node1, relation, node2 = triplet
        # Ensure the nodes exist and retrieve their Milvus IDs
        self._get_or_insert_node(node1, collection_name, get_embedding_func)
        self._get_or_insert_node(node2, collection_name, get_embedding_func)
        # Add the relation
        with self.neo4j_driver.session() as session:
            session.run("""
            MATCH (n1:Node {name: $node1, collection_name: $collection_name})
            MATCH (n2:Node {name: $node2, collection_name: $collection_name})
            MERGE (n1)-[r:RELATION {type: $relation}]->(n2)
            """, {"node1": node1.name, "node2": node2.name, "relation": relation, "collection_name": collection_name})

    def delete_relation(self, triplet: Tuple[Node, str, Node], database_name, collection_name):
        node1, relation, node2 = triplet

        with self.neo4j_driver.session(database=database_name) as session:
            # Delete the relation
            session.run("""
            MATCH (n1:Node {name: $node1, collection_name: $collection_name})-[r:RELATION {type: $relation}]->(n2:Node {name: $node2, collection_name: $collection_name})
            DELETE r
            """, {"node1": node1, "node2": node2, "relation": relation, "collection_name": collection_name})

            # For each node, if it has no relations left, delete it
            for node in [node1, node2]:
                relations = session.run("""
                MATCH (n:Node {name: $node, collection_name: $collection_name})-[r]-()
                RETURN COUNT(r) AS relations
                """, {"node": node, "collection_name": collection_name})

                if relations.peek()['relations'] == 0:
                    # Get Milvus ID before deleting the node
                    vector_store_id = session.run("""
                    MATCH (n:Node {name: $node, collection_name: $collection_name})
                    RETURN n.vector_store_id AS vector_store_id
                    """, {"node": node, "collection_name": collection_name}).single()['vector_store_id']

                    # Delete the node
                    session.run("""
                    MATCH (n:Node {name: $node, collection_name: $collection_name})
                    DELETE n
                    """, {"node": node, "collection_name": collection_name})

                    # Delete the vector in Milvus
                    connections.get_connection().delete_entity_by_id(
                        collection_name, [vector_store_id])

    def keyword_search(self, query_vector: List[float], collection_name, token_limit=100, topn=2):
        search_results = self.vector_db_client.search_node(
            collection_name, query_vector)
        logger.debug(
            f"Similarity search result is {[r['name'] for r in search_results]}")
        vector_store_ids = [result["id"] for result in search_results][:topn]
        # Retrieve the nodes in Neo4j and find paths
        with self.neo4j_driver.session() as session:
            paths = session.run("""
            UNWIND $ids AS id
            MATCH path = (n1:Node {vector_store_id: id, collection_name: $collection_name})-[r*..3]-(n2:Node {collection_name: $collection_name})
            WHERE n1 <> n2
            RETURN path
            """, {"ids": vector_store_ids, "collection_name": collection_name})
            records = list(paths)
        paths = []
        seen_paths = []
        total_num_tokens = 0
        for record in records:
            path = record["path"]
            logger.debug(f"path is {path}")
            relationships = path.relationships
            for rel in relationships:
                node1 = rel.nodes[0]['name']
                node2 = rel.nodes[1]['name']
                relation = rel['type']
                if f"{node1}{relation}{node2}" in seen_paths:
                    continue
                path = f"{node1} {relation} {node2}"
                total_num_tokens += get_num_tokens(path)
                logger.debug(f"all paths have {total_num_tokens} tokens")
                if total_num_tokens > token_limit:
                    break
                seen_paths.append(f"{node1}{relation}{node2}")
                paths.append(path)
        return paths
