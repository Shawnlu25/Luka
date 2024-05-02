from luka.sandbox import DockerSandbox
from litellm import completion
import os
import time

SYSTEM_PROMPT = """
You are an agent controlling a bash terminal. You are given:
    1. an objective that you are trying to achieve
    2. the content on the terminal
    3. previous command history

You can issue the following commands to the terminal:
    1. Any bash command that you believe will get you closer to achieving your goal, one command at a time
    2. CTRL-<Key>, where <Key> can be any character from a to z, to send a special key to the terminal, one key at a time.
    3. COMPLETE <TEXT> - indicate that you have completed the objective, and provide any comments you have in <TEXT>
    4. HOLD - indicate that you are not sending any command for now, and wait for the system to provide you with more information
    5. YIELD - indicate that you are not able to make any progress, and yield to the user for action (e.g., when prompted to provide a password for `sudo`)

Based on your given objective, issue whatever command you believe will get you closest to achieving your goal. If you want to check the current directory, you can use the `pwd` command. If you want to check environment variables, you can use `env` command. 

Note that the content of current terminal has a buffer size. If you think the content is too long, try use `less`, `head`, `tail` commands to view the content with pipes.

Sometimes the previous command is still running, please wait for the command to finish before issuing the next command.

The objective and the content of terminal follow, please issue your next command to the terminal.
"""

USER_PROMPT = """
TERMINAL SCREEN
===============================
$content
===============================

LAST 5 COMMANDS
===============================
$commands
===============================
OBJECTIVE: $objective
YOUR COMMAND:
"""

class TTYAgent():
    def __init__(self):
        self._sandbox = DockerSandbox()
        self._model = "gpt-4-turbo"
        self._openai_key = os.getenv("OPENAI_API_KEY")
        self._history = []

        self._buf_size = 2048
        self._buffer = ""
    
    def reset(self):
        self._sandbox = DockerSandbox()

    def _get_content(self):
        data = self._sandbox.fetch_output()
        if len(data) > self._buf_size:
            data = data[-self._buf_size:]
        print(data)
        # append data to buffer, shrink buffer if necessary
        self._buffer = self._buffer[-(self._buf_size-len(data)):] + data
        return self._buffer
    
    def _act(self, command):
        completed = None
        original_command = command

        command = command.strip()
        if command == "YIELD":
            command = input("Please enter your command: ")
            command = command.strip()

        if command.startswith("COMPLETE"):
            command = command.split(" ")
            if len(command) == 1:
                completed = ""
            else:
                completed = " ".join(command[1:])
        elif command.startswith("CTRL-"):
            ch = command.split("-")[1].lower()
            # convert ascii character to control character
            ch = chr(ord(ch) - ord('a') + 1)
            self._sandbox.send_command(ch)
        elif command == "HOLD":
            return
        else:
            self._sandbox.send_command(command+"\n")
        
        self._history.append({
            "command": original_command,
            "completed": completed,
        })
        

    def run(self, objective):
        completed = False
        while not completed:
            user_prompt = USER_PROMPT.replace("$objective", objective)
            
            content = self._get_content()
            user_prompt = user_prompt.replace("$content", content)
            last_commands = "\n".join([h["command"] for h in self._history[-5:]])
            user_prompt = user_prompt.replace("$commands", last_commands)

            response = completion(
                model=self._model,
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
            )
            command = response["choices"][0]["message"]["content"]
            self._act(command)
            time.sleep(0.5)

            if self._history[-1]["completed"]:
                print("Objective completed!")
                print(self._history[-1]["completed"])
                completed = True
        return self._history[-1]["completed"]
    
if __name__ == "__main__":
    agent = TTYAgent()
    while True:
        print("Please enter your objective (type `exit` to exit): ")
        objective = input("> ")
        if objective == "exit":
            break
        agent.run(objective)


