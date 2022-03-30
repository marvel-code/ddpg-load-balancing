import numpy as np

from stable_baselines3 import DDPG
from stable_baselines3.common.env_checker import check_env

class Agent:
    
    def __init__(self, env):
        check_env(env)
        model = DDPG("CnnPolicy", env, verbose=1)
        model.learn(total_timesteps=10000, log_interval=10)
        model.save("ddpg_pendulum")
        env = model.get_env()

        del model # remove to demonstrate saving and loading

        model = DDPG.load("ddpg_pendulum")

        obs = env.reset()
        while True:
            action, _states = model.predict(obs)
            obs, rewards, dones, info = env.step(action)
            env.render()

    
