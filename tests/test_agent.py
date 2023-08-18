from GoogleNews import GoogleNews
from newspaper import Article, ArticleException
import json
import time
import math
import copy
from agentware.agent import Agent
from agentware.base import Connector
from agentware.memory import Memory
from agentware.agent_logger import Logger
from test_memory import create_memory

logger = Logger()


def get_news_links(query, lang="en", region="US", pages=1, max_links=100000):
    googlenews = GoogleNews(lang=lang, region=region)
    googlenews.search(query)
    all_urls = []
    for page in range(pages):
        googlenews.get_page(page)
        all_urls += googlenews.get_links()
    return list(set(all_urls))[:max_links]


def get_article(url):
    article = Article(url)
    article.download()
    article.parse()
    return article


def get_chunks(text: str, span_length: int):
    num_tokens = len(text)
    print(f"Input has {num_tokens} tokens")
    num_spans = math.ceil(num_tokens / span_length)
    print(f"Input has {num_spans} spans")
    overlap = math.ceil((num_spans * span_length - num_tokens) /
                        max(num_spans - 1, 1))
    spans_boundaries = []
    start = 0
    for i in range(num_spans):
        spans_boundaries.append([start + span_length * i,
                                 start + span_length * (i + 1)])
        start -= overlap
    chunks = []
    for boundary in spans_boundaries:
        chunks.append({
            "text": text[boundary[0]:boundary[1]],
            "boundary": boundary
        })
    return chunks


def RunDocumentReaderFromScratch():
    agent_cfg_path = "./test_dataconfigsdocument_reader.json"
    agent_config = None
    with open(agent_cfg_path, "r") as f:
        agent_config = json.loads(f.read())
    connector_cfg_path = "test_data/connector_configs/sample_connector.json"
    connector_cfg = None
    with open(connector_cfg_path, "r") as f:
        connector_cfg = json.loads(f.read())
    connector = Connector(connector_cfg)
    memory = create_memory(agent_cfg_path, connector)
    agent = Agent(memory, connector, None)
    # # Get document feed
    # links = get_news_links("Google", pages=1, max_links=3)
    # for url in links:
    #     try:
    #         print("getting article")
    #         article = get_article(url)
    #     except:
    #         print(f"failed to get article from {url}")
    #         continue
    #     chunks = get_chunks(article.text, 2000)
    #     config = {
    #         "article_title": article.title,
    #         "article_publish_date": article.publish_date
    #     }
    #     for chunk in chunks:
    #         output = agent.run(
    #             f"Given the text, ```{chunk['text']}```, please summarize the text in the quotes above")
    #         print("response is ", output)

    # Get local text
    text = ""
    with open("capital_theory.txt", "r") as f:
        text = f.read()
    chunks = get_chunks(text, 400)
    for chunk in chunks:
        output = agent.run(
            f"Given the text, ```{chunk['text']}```, please summarize the text in the quotes above")
        print("response is ", output)


def RunDocumentReaderFromConnector(agent_id):
    cfg_path = "./test_dataconfigsdocument_reader.json"
    cfg = None
    with open(cfg_path, "r") as f:
        cfg = json.loads(f.read())
    connector_cfg_path = "./test_data/connector_configs/sample_connector.json"
    connector_cfg = None
    with open(connector_cfg_path, "r") as f:
        connector_cfg = json.loads(f.read())
    connector = Connector(1, connector_cfg)
    agents = connector.all_agents(user_id=1)
    print("agents are", agents)
    connector.connect(agent_id)
    agent = Agent.from_connector(connector)
    # agent = Agent.from_connector(
    #     connector, selected_agent_id, agent_graph)
    # memory = create_memory(cfg_path, connector)
    # agent = Agent(cfg, memory, connector)
    # # Get document feed
    # links = get_news_links("Google", pages=1, max_links=3)
    # for url in links:
    #     try:
    #         print("getting article")
    #         article = get_article(url)
    #     except:
    #         print(f"failed to get article from {url}")
    #         continue
    #     chunks = get_chunks(article.text, 2000)
    #     config = {
    #         "article_title": article.title,
    #         "article_publish_date": article.publish_date
    #     }
    #     for chunk in chunks:
    #         output = agent.run(
    #             f"Given the text, ```{chunk['text']}```, please summarize the text in the quotes above")
    #         print("response is ", output)

    # Get local text
    text = ""
    with open("capital_theory.txt", "r") as f:
        text = f.read()
    chunks = get_chunks(text, 400)
    for chunk in chunks:
        output = agent.run(
            f"Given the text, ```{chunk['text']}```, please summarize the text in the quotes above")
        print("response is ", output)


def RunDfsExecutor():
    # TODO:
    # 1. 现在需要继续改agent的constructor. 需要决定哪些是输入参数。要测试session graph的维护
    # 2. connector的读写需要加多线程锁
    cfg_path = "./test_dataconfigsgraph_executor.json"
    cfg = None
    with open(cfg_path, "r") as f:
        cfg = json.loads(f.read())
    connector = Connector(1)
    sessions = connector.list_sessions(user_id=1)
    print("sessions are", sessions)
    selected_agent_id = 3
    connector.connect(selected_agent_id)
    # agent = Agent.from_connector(
    #     connector, selected_agent_id, agent_graph)
    memory = create_memory(cfg_path, connector)
    agent = Agent(cfg, memory, connector)

    output = agent.run(
        f"What is the sum of the square of houston's population and the square root of austin's population?")
    print("output is ", output)


def TestCreateAgent():
    connector = Connector(1)
    agent_id = 2
    agent_config, memory_units, work_exp, context, session_data = connector.get_agent(
        agent_id)

    memory = create_memory("./test_dataconfigsdocument_reader.json")


if __name__ == "__main__":
    # RunDfsExecutor()
    RunDocumentReaderFromScratch()
    # RunDocumentReaderFromConnector(1)
