# Insert some demo data into db
from db_clients.memory_db_client import DbClient
from utils import create_memory

if __name__ == "__main__":
    CFG = {
        "username": "admin",
        "ip": "127.0.0.1",
        "port": "6379",
    }
    db_client = DbClient(CFG)
    db_client.user_client.flushdb()
    db_client.user_client.flushdb()

    db_client.create_user({
        "name": "Snow"
    })
    print("user data is", user_data)
    agent_config = dict()
    agent_id = db_client.create_agent(user_data["id"])
    print("New agent id is", agent_id)
    # Create an agent and save to db
