from luka import ReActBrowserAgent

if __name__ == "__main__":
    agent = ReActBrowserAgent()
    while True:
        agent.reset()
        print("Please enter your objective (type `exit` to exit): ")
        objective = input("> ")
        if objective == "exit":
            break
        agent.run(objective)
        input("Press enter to continue...")