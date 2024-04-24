from luka.sandbox import DockerSandbox
from litellm import completion
import os

SYSTEM_PROMPT = """
You are an agent controlling a bash terminal. You are given:
    1. an objective that you are trying to achieve
    2. the content on the terminal

You can issue the following commands to the terminal:
    1. Any bash command that you believe will get you closer to achieving your goal, one command at a time
    2. CTRL-<Key>, where <Key> can be any character from a to z, to send a special key to the terminal, one key at a time.
    3. COMPLETE <TEXT> - indicate that you have completed the objective, and provide any comments you have in <TEXT>
    4. HOLD - indicate that you are not sending any command for now, and wait for the system to provide you with more information

Based on your given objective, issue whatever command you believe will get you closest to achieving your goal. If you want to check the current directory, you can use the `pwd` command. If you want to check environment variables, you can use `env` command. 

Note that the content of current terminal has a buffer size. If you think the content is too long, try use `less`, `head`, `tail` commands to view the content with pipes.

The objective and the content of terminal follow, please issue your next command to the terminal.
"""

USER_PROMPT = """
TERMINAL SCREEN
===============================
$content
===============================
OBJECTIVE: $objective
YOUR COMMAND:
"""

class TTYAgent():
    def __init__(self):
        self._sandbox = DockerSandbox()
        self._model = "gpt-4-turbo"
        self._openai_key = os.getenv("OPENAI_API_KEY")
    
    def reset(self):
        self._sandbox = DockerSandbox()
    
    def run(self, objective):
        
        pass
    
if __name__ == "__main__":
    agent = TTYAgent()
    while True:
        objective = input("Please enter your objective (type `exit` to exit): ") 


