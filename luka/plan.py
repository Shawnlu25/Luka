
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

import instructor
from litellm import completion

class TaskState(str, Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"

class Task(BaseModel):
    id: str = Field(..., title="Unique identifier of the task")
    goal: str = Field(..., title="A short summary of what should be achieved")
    description: str = Field(..., title="Additional details about the task")
    state: TaskState = Field(TaskState.open, title="The current state of the task, default to be open")
    subtasks: Optional[List['Task']] = Field([], title="Subtasks of the current task, to be completed in order")

    def to_string(self, indent=''):
        emoji = ''
        if self.state == TaskState.completed:
            emoji = '✅'
        elif self.state == TaskState.abandoned:
            emoji = '⛔️'
        elif self.state == TaskState.in_progress:
            emoji = '⏳'
        elif self.state == TaskState.open:
            emoji = '🔲'
        result = indent + emoji + ' ' + str(self.id) + ' ' + self.goal + '\n'

        if self.subtasks:
            result += ''.join([s.to_string(indent + '    ') for s in self.subtasks])
        return result

class Plan(BaseModel):
    tasks: List[Task] = Field([], title="A list of tasks to be completed in order")

    def __str__(self):
        return ''.join([t.to_string() for t in self.tasks])
    
    


SYSTEM_PROMPT = """
You are a project manager and your task is to decompose the user's objective into actionable tasks. You are provided with the following capabilities:

* You have access to a web browser to gather information or complete jobs online. 
* You have access to a TTY bash terminal to run commands, modifiy files, and interact with the system.

When generating the plan, beware that:
* The ID of each task should be unique and should reflect the hierarchy of the tasks. For example, task `3.2` is the second subtask of task `3`.
* The tasks would be completed in order with no concurrent tasks.

You might be provided with a previous plan and additional information that you can built upon. In that case:
* If no plan is provided, generate a brand new plan.
* You don't need to repeat the tasks that have been completed, they have already been done. Only generate subsequent tasks to bring us closer to completing the objective. 
* The new tasks you generated would replace the old tasks starting from the first open (incompleted) task.
* If the most recent task is abandoned, modify the plan based on new information and provide new tasks in order to achieve the objective.

Now please generate a plan to achieve the user's objective.
"""

if __name__ == "__main__":
    print("Please enter your objective:")
    objective = input('> ')
    
    client = instructor.from_litellm(completion)
    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": objective,
            }
        ],
        response_model=Plan,
    )
    print(resp)