from log import Log
from agent.agent import Agent
from environment.environment import CustomEnv

l = Log('main')

if __name__ == '__main__':
    e = CustomEnv()
    a = Agent(e)
    a.launch()

