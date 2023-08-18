from vector_db_clients.command_vector_db import CommandsVectorStore
from agentware.base import Command


def TestCommandStore(command_store: CommandsVectorStore):
    commands = [
        Command(
            "python writer",
            "a tool that writes python code",
            "http://localhost:3000",
            """
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "what you want the code to do"
                    }
                },
                "required": ["task"],
                "additionalProperties": false
            }
            """,
            """
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description: "The code that works for the task"
                    }
                },
                "required": ["code"],
                "additionalProperties": false
            }
            """),
        Command(
            "google",
            "an api that searches google for any keyword",
            "http://localhost:3000",
            """
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "what you want the code to do"
                    }
                },
                "required": ["keyword"],
                "additionalProperties": false
            }
            """,
            """
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "description: "The code that works for the task",
                        "items": {
                            "type": "string",
                            "description": "search result"
                        }
                    }
                },
                "required": ["code"],
                "additionalProperties": false
            }
            """)
    ]
    for c in commands:
        embeds = command_store.get_embeds(f"{c.name} {c.description}")
        c.update_embeds(embeds)
    # command_store.insert_commands(commands)
    commands = command_store.search_command(
        "I need to find some recent news about the hurricane")
    print("searched commands are", commands)


if __name__ == "__main__":
    command_store = CommandsVectorStore(
        collection_name="test_command_store")
    TestCommandStore(command_store)
