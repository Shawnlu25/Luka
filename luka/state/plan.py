from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, TypeVar, Generic

import instructor
from litellm import completion

class TaskState(str, Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"

T = TypeVar('T', bound=str)

class Task(BaseModel, Generic[T]):
    id: str = Field(..., title="Unique identifier of the task")
    goal: str = Field(..., title="A short summary of what should be achieved")
    description: str = Field(..., title="Additional details about the task")
    state: TaskState = Field(TaskState.open, title="The current state of the task, default to be open")
    assignee: T = Field(..., title="The agent who is responsible for completing the task")
    #subtasks = None #Optional[List['Task']] = Field([], title="Subtasks of the current task, to be completed in order")

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
        result = indent + emoji + ' ' + str(self.id) + ' [' + self.assignee + '] ' + self.goal + '\n'

        #if self.subtasks:
            #result += ''.join([s.to_string(indent + '    ') for s in self.subtasks])
        return result
    
    def conform_state(self):
        return
        if self.subtasks and len(self.subtasks) == 0:
            return
        for task in self.subtasks:
            task.conform_state()

        if any([task.state == TaskState.abandoned for task in self.subtasks]):
            self.state = TaskState.abandoned
        elif all([task.state == TaskState.completed for task in self.subtasks]):
            self.state = TaskState.completed
        elif all([task.state == TaskState.open for task in self.subtasks]):
            self.state = TaskState.open
        else:
            self.state = TaskState.in_progress

    def get_next_task(self):
        #if self.subtasks:
        #    for task in self.subtasks:
        #        next_task = task.get_next_task()
        #        if next_task:
        #            return next_task
        if self.state == TaskState.open:
            return self
        return None


class Plan(BaseModel, Generic[T]):
    tasks: List[Task[T]] = Field([], title="A list of tasks to be completed in order")

    def __str__(self):
        return ''.join([t.to_string() for t in self.tasks])
    
    def conform_state(self):
        for task in self.tasks:
            task.conform_state()
    
    def get_next_task(self):
        for task in self.tasks:
            task = task.get_next_task()
            if task:
                return task
        return None
    
    def merge(self, new_plan):
        if len(new_plan.tasks) == 0:
            return
        if len(self.tasks) == 0:
            self.tasks = new_plan.tasks
            return
        for i, task in enumerate(self.tasks):
            if task.state != TaskState.completed and task.state != TaskState.abandoned:
                self.tasks = self.tasks[:i] + new_plan.tasks
                return


SYSTEM_PROMPT = """
You are a project manager and your task is to decompose the user's objective into actionable tasks. You are provided with the following capabilities:

* You have access to a web browser to gather information or complete jobs online. 
* You have access to a TTY bash terminal to run commands, modifiy files, and interact with the system.

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

if __name__ == "__main__":
    print("Please enter your objective:")
    objective = input('> ')
    plan = None
    client = instructor.from_litellm(completion)

    while True:
        user_prompt = USER_PROMPT.replace('$objective', objective)
        user_prompt = user_prompt.replace('$plan', str(plan) if plan else 'None')
        resp = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            response_model=Plan,
        )
        if plan:
            plan.merge(resp)
        else:
            plan = resp
        print("Generated plan:")
        print(resp)

        print("Merged plan:")
        print(plan)

        print("Next task to execute:")
        next_task = plan.get_next_task()
        print(next_task.to_string())

        next_task.state = TaskState.in_progress
        plan.conform_state()

        print("Set state (`c`omplete, `a`bandon):")
        state = input("> ")
        if state == 'c':
            next_task.state = TaskState.completed
        elif state == 'a':
            next_task.state = TaskState.abandoned
        else:
            next_task.state = TaskState.completed
        plan.conform_state()