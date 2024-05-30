from .envs import TextualBrowserEnv

from gymnasium.envs.registration import register

register(
    id="luka/TextualBrowser-v0",
    entry_point=TextualBrowserEnv,
    nondeterministic=True,
    max_episode_steps=1000,
)