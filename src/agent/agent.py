import numpy as np
from stable_baselines3 import DDPG
from stable_baselines3.common.env_checker import check_env
from log import Log

l = Log('agent')
class Agent:
    
    def __init__(self, env):
        check_env(env)
        self.env = env
        self.model = DDPG("CnnPolicy", env, verbose=1)
        env.reset()

    def step(self):
        action = self.model.predict(self.obs)
        self.env.step(action)
    
    def launch(self):
        self.step()



