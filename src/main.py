from agent import agent
import gym

if __name__ == '__main__':
    env = gym.make('Pendulum-v0')
    a = agent.Agent(env)

