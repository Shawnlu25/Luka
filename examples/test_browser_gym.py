import gymnasium as gym

import base64
import io
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from luka.tools.browser import TextualBrowserEnv
from termcolor import colored

env = TextualBrowserEnv()
obs, info = env.reset(options={"url": "https://www.google.com"})

while True:
    img = mpimg.imread(io.BytesIO(base64.b64decode(obs["screenshot_base64"])))
    plt.imshow(img)

    print(obs["page_text"])
    print(obs["url"])
    print(obs["scroll_status"])

    print(img.shape)    
    
    plt.show()

    command = input(colored("> ", "green", attrs=["bold"]))

    obs, info = env.step({"command": "click", "args": ["a"]})
    