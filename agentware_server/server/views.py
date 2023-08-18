# In views.py
import os
from . import views
from django.urls import path
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from agentware.base import Knowledge
from agentware import error_codes
from server.vector_db_clients.knowledge_vector_db import KnowledgeVectorStore
from server.vector_db_clients.command_vector_db import CommandsVectorStore
from server.knowledge_graph_clients.knowledge_graph_client import KnowledgeGraphClient, Node
from server.db_clients.memory_db_client import DbClient

TOKEN_TIMEOUT = "Authentication error, token timeout"

config = None
with open("./server/configs/server_config.json", "r") as f:
    config = json.loads(f.read())

command_hub_client = CommandsVectorStore(
    config["vector_db_config"])
knowledge_base_client = KnowledgeVectorStore(
    config["vector_db_config"])
kg_client = KnowledgeGraphClient(config)
db_client = DbClient(config["redis_db_config"])


@csrf_exempt
@require_http_methods("GET")
def ping(request, **kwargs):
    return JsonResponse({'response': "pong"})


@csrf_exempt
@require_http_methods("GET")
def get_agent(request, **kwargs):
    try:
        agent_id = request.GET.get('agent_id')
        if not agent_id:
            return JsonResponse({
                "success": False,
                "error_code": error_codes.INVALID_AGENT_ID})
        agent_config, memory_units = db_client.get_agent(
            agent_id)
        if agent_config is None:
            return JsonResponse({
                "success": False,
                "error_code":  error_codes.AGENT_NOT_FOUND.code}, safe=False)
        result = {
            "success": True,
            "agent_config": dict(),
            "memory_units": [],
        }
        if agent_config:
            result["agent_config"] = agent_config
        if memory_units:
            result["memory_units"] = memory_units
        return JsonResponse(result, safe=False)
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("GET")
def get_longterm_memory(request, agent_id: int, **kwargs):
    try:
        page_number = int(request.GET.get('page_number', "0"))
        page_size = int(request.GET.get('page_size', "10"))

        if page_number < 0:
            raise ValueError(f"Invalid page number {page_number}")
        if page_size <= 0:
            raise ValueError(f"Invalid page size {page_size}")
        result = db_client.get_longterm_memory(
            agent_id, page_number, page_size)
        return JsonResponse(result, safe=False)
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("PUT")
def update_longterm_memory(request, agent_id: int, **kwargs):
    try:
        data = json.loads(request.body)
        memory_data = data['memory_data']
        db_client.save_longterm_memory(agent_id, memory_data)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("PUT")
def update_agent(request, agent_id: str, **kwargs):
    try:
        data = json.loads(request.body)
        agent_config = data['agent_config']
        memory_data = data["memory_data"]
        db_client.update_agent(agent_id,
                               agent_config, memory_data)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("PUT")
def save_knowledge(request, collection_name: str, **kwargs):
    try:
        data = json.loads(request.body)
        knowledges_json = data['knowledges']
        knowledges = [Knowledge.from_json(k) for k in knowledges_json]
        knowledge_base_client.insert_knowledge(
            collection_name, knowledges)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("GET")
def search_commands(request, collection_name):
    try:
        data = json.loads(request.body)
        query_embeds = data['query_embeds']
        token_limit = data['token_limit']
        if not query_embeds:
            raise ValueError("Invalid query embeds")
        result = command_hub_client.search_command(
            collection_name, query_embeds, token_limit)
        return JsonResponse(result, safe=False)
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("GET")
def search_knowledge(request, collection_name: str, **kwargs):
    try:
        # query_embeds = request.GET.get('query_embeds', [])
        data = json.loads(request.body)
        query_embeds = data["query_embeds"]
        token_limit = data["token_limit"]
        if not query_embeds:
            raise ValueError(f"query embeds value invalid")
        result = knowledge_base_client.search_knowledge(
            collection_name, query_embeds, token_limit)
        return JsonResponse(result, safe=False)
    except Exception as e:
        print(e)
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("GET")
def get_recent_knowledge(request, collection_name: str, **kwargs):
    try:
        # query_embeds = request.GET.get('query_embeds', [])
        data = json.loads(request.body)
        token_limit = data["token_limit"]
        result = knowledge_base_client.get_recent_knowledge(
            collection_name, token_limit)
        return JsonResponse(result, safe=False)
    except Exception as e:
        print(e)
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("GET")
def search_kg(request, collection_name: str, **kwargs):
    try:
        # query_embeds = request.GET.get('query_embeds', [])
        data = json.loads(request.body)
        query_embeds = data["query_embeds"]
        token_limit = data["token_limit"]
        if not query_embeds:
            raise ValueError(f"query embeds value invalid")
        result = kg_client.keyword_search(
            query_embeds, collection_name)
        return JsonResponse(result, safe=False)
    except Exception as e:
        print(e)
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("PUT")
def register_agent(request, **kwargs):
    try:
        data = json.loads(request.body)
        agent_id = data['agent_id']
        if not agent_id:
            raise ValueError(f"agent id empty")
        result = db_client.register_agent(agent_id)
        return JsonResponse({
            "exists": result
        }, safe=False)
    except Exception as e:
        print(e)
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("GET")
def agent_exists(request, agent_id: int, **kwargs):
    try:
        if not agent_id:
            raise BaseException(f"Invalid agent id {agent_id}")
        return JsonResponse({
            "exists": db_client.agent_exists(agent_id)
        }, safe=False)
    except Exception as e:
        print(e)
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("PUT")
def remove_agent(request, **kwargs):
    try:
        data = json.loads(request.body)
        agent_id = data['agent_id']
        knowledge_base_collection_id = data['knowledge_base_collection_id']
        if not agent_id:
            raise ValueError(f"agent id empty")
        if not knowledge_base_collection_id:
            raise ValueError(f"knowledge_base_collection_id empty")
        db_client.remove_agent(agent_id)
        print("Removing colelction", knowledge_base_collection_id)
        knowledge_base_client.remove_collection(knowledge_base_collection_id)
        return JsonResponse({
            "success": True
        }, safe=False)
    except Exception as e:
        print(e)
        return JsonResponse({
            "success": False,
            "fail_reason": str(e)
        })


@csrf_exempt
@require_http_methods("PUT")
def remove_knowledge(request, **kwargs):
    try:
        data = json.loads(request.body)
        if not "collection_name" in data:
            raise ValueError(f"no collection name")
        if not "ids_to_remove" in data:
            raise ValueError(f"ids to remove is empty")
        collection_name = data['collection_name']
        ids = data['ids_to_remove']
        if not collection_name:
            raise ValueError(f"collection name empty")
        knowledge_base_client.remove_by_ids(ids, collection_name)
        return JsonResponse({
            "success": True
        })
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods("GET")
def all_agents(request):
    try:
        agent_ids_bytes = db_client.all_agents()
        result = [id_bytes.decode() for id_bytes in agent_ids_bytes]
        return JsonResponse(result, safe=False)
    except Exception as e:
        print(e)
        return HttpResponseBadRequest(str(e))
