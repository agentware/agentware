from agentware.agent import Agent

if __name__ == "__main__":
    cfg_path = "./autogpt_agent.yaml"
    feedback_agent = Agent(cfg_path)
    # response = feedback_agent.run(
    #     "Determine the steps to take to answer this question: What is the square root of donald trumps age")
    response = feedback_agent.run(
        "Determine the steps to take to answer this question: What is the square root of Houston's populaton in 2023")
    print(response)
