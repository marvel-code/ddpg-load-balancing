import numpy as np
from stable_baselines3 import DDPG, PPO
from stable_baselines3.common.env_checker import check_env
from log import Log

l = Log('agent')
class Agent:
    
    def __init__(self, env):
        check_env(env)
        self.env = env
        self.model = DDPG(
            policy="MlpPolicy", 
            env=env, 
            verbose=1,
        )
        env.reset()

    def step(self):
        obs = self.env.get_observation()
        action = self.model.predict(obs)
        return self.env.step(action)
    
    def launch(self):
        while True:
            self.model.learn(100)



