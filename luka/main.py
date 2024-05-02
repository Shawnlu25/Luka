import instructor
from litellm import completion
from enum import Enum

from luka.state import Plan, Task, TaskState
from luka import AGENT_REGISTRY

SYSTEM_PROMPT = """
You are a project manager and your task is to decompose the user's objective into actionable tasks. You are provided agents with the following capabilities:

$capabilities

The assignees for each task should be one of: [$agent_names]

When generating the plan, beware that:
* The tasks would be completed in order with no concurrent tasks.
* Task state should always be `open`.
* Keep the completed tasks for record.

You might be provided with a previous plan and additional information that you can built upon. In that case:
* If no plan is provided, generate a brand new plan.
* You don't need to repeat the tasks that have been completed, they have already been done. Only generate subsequent tasks to bring us closer to completing the objective. 
* The new tasks you generated would replace the old tasks starting from the first incompleted (open / in-progress) task.
* If the most recent task is abandoned, modify the plan based on new information and provide new tasks in order to achieve the objective.
* If you think there is no need for modifying the current plan, return an empty list of tasks.

Now please generate a plan to achieve the user's objective.
"""

USER_PROMPT = """
OBJECTIVE: 
$objective

CURRENT_PLAN:
$plan
"""

class Orchestrator():
    def __init__(self):
        self._client = instructor.from_litellm(completion)
        self._model = "gpt-4-turbo"
        self.reset()
    
    def reset(self):        
        self._dynamic_enum = Enum("AgentEnum", {k: k for k in AGENT_REGISTRY.keys()}, type=str)
        self._plan = Plan[self._dynamic_enum]()
        capabilities_str = "\n".join([f"* {k} - {v['description']}" for k,v in AGENT_REGISTRY.items()])

        self._system_prompt = SYSTEM_PROMPT.replace("$capabilities", capabilities_str)
        self._system_prompt = self._system_prompt.replace("$agent_names", ", ".join(AGENT_REGISTRY.keys()))
        self._agents = {k: v["cls"]() for k,v in AGENT_REGISTRY.items()}

    def run(self, objective):
        prev_info = ""
        while True:
            user_prompt = USER_PROMPT.replace('$objective', objective)
            user_prompt = user_prompt.replace('$plan', str(self._plan) if self._plan else 'None')

            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": self._system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                response_model=Plan,
            )
            
            self._plan.merge(resp)
            print("CURRENT PLAN:")
            print(self._plan)
            self._plan.conform_state()

            next_task = self._plan.get_next_task()
            if next_task is None:
                break
            
            
            next_task.state = TaskState.in_progress
            print("EXECUTING NEXT TASK:")
            print(next_task.to_string())
            print(next_task.description)

            assignee = self._agents[next_task.assignee]
            prev_info = assignee.run(next_task.description, info=prev_info)

            next_task.state = TaskState.completed
            self._plan.conform_state()
            print("TASK COMPLETED")
            print(next_task.to_string())


if __name__ == "__main__":
    orchestrator = Orchestrator()
    print("Please enter your objective:")
    objective = input('> ')
    orchestrator.run(objective)
