import gymnasium as gym
import browsergym.core  # register the openended task as a gym environment


env = gym.make(
    'browsergym/openended',
    task_kwargs={'start_url': 'about:blank'},
    wait_for_user_message=False,
    headless=False,
    disable_env_checker=True,
)
obs, info = env.reset()
done = False
print(obs)
exit()
while not done:
    action = None
    obs, reward, terminated, truncated, info = env.step(action)
    