from statistics import mean
from typing import Dict, List
from typing_extensions import TypedDict
import gym
from gym import spaces
import numpy as np
import socket
from log import Log

LinkState = TypedDict("LinkState", {
    'utilization': int,
})
                        
HOST = '127.0.0.1'
PORT = 50123

K = int(4) # Pod count
CORE_COUNT = int(K * K / 4)
EDGE_PER_POD_COUNT = int(K / 2)
AGGR_PER_POD_COUNT = int(K / 2)
EDGE_COUNT = K * EDGE_PER_POD_COUNT

PATH_COUNT_TO_OTHER_POD_EDGE = CORE_COUNT * AGGR_PER_POD_COUNT * AGGR_PER_POD_COUNT
PATH_COUNT_TO_SAME_POD_EDGE = CORE_COUNT * AGGR_PER_POD_COUNT * (AGGR_PER_POD_COUNT - 1) + AGGR_PER_POD_COUNT
PATH_COUNT_PER_EDGE = PATH_COUNT_TO_OTHER_POD_EDGE * (K - 1) * EDGE_PER_POD_COUNT + PATH_COUNT_TO_SAME_POD_EDGE * (EDGE_PER_POD_COUNT - 1)

SAME_POD_EDGE_PAIRS = int(K**2 * (K - 2) / 4)
OTHER_POD_EDGE_PAIRS = int(K**3 * (K  - 1) / 4)
PROPS_COUNT = SAME_POD_EDGE_PAIRS * PATH_COUNT_TO_SAME_POD_EDGE + OTHER_POD_EDGE_PAIRS * PATH_COUNT_TO_OTHER_POD_EDGE
SEND_DELIMITERS_COUNT = SAME_POD_EDGE_PAIRS + OTHER_POD_EDGE_PAIRS - 1
SEND_MSG_LEN = PROPS_COUNT + SEND_DELIMITERS_COUNT

LINK_CAPACITY_BPS = int(100 * 1024 * 1024)
AGGR_FLOW_CAPACITY_BPS = LINK_CAPACITY_BPS * AGGR_PER_POD_COUNT

l = Log('env')
class CustomEnv(gym.Env):
    """Custom Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(CustomEnv, self).__init__()
        # Throughput for each aggr flow
        self.observation_space = spaces.Box(low=0, high=AGGR_FLOW_CAPACITY_BPS, 
            shape=(EDGE_COUNT, EDGE_COUNT - 1), dtype=np.uint8)
        # Proportion for each path (not normalized)
        self.action_space = spaces.Box(low=0, high=100, 
            shape=(EDGE_COUNT, PATH_COUNT_PER_EDGE), dtype=np.uint8)
        # Init socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(1)
        l.log('Waiting connection...')
        self.client, addr = s.accept()
        l.log('Connected: ', addr)

    def step(self, action):
        self.send_action(action)
        self.receive_network_state()
        observation = self.aggr_flow_throughputs
        reward = self.calculate_reward()
        done = False
        info = {}
        return observation, reward, done, info

    def reset(self):
        self.aggr_flow_throughputs = [[0] * (EDGE_COUNT - 1) for i in range(EDGE_COUNT)]
        return self.aggr_flow_throughputs
        
    def render(self, mode='human'):
        # ...
        pass

    def close(self):
        self.client.close()

    # Other

    def send_action(self, action: List[List[int]]):
        """
        Send "\x00\x01\x02\xff\x10\x11\x12"
        Where \xXX is proportion, \xff is delimiter between edge pairs
        """
        normalized_action: List[List[int]] = []
        for props in action:
            i = 0
            while i < len(props):
                subaction = props[i:i + PATH_COUNT_TO_OTHER_POD_EDGE]
                s = sum(subaction)
                normalized_action.append(map(lambda x: int(x / s * 100), subaction))
                i += PATH_COUNT_TO_OTHER_POD_EDGE
        
        msg = (b'\xff').join(map(lambda x: b''.join(map(lambda y: y.to_bytes(1, 'big'), x)), normalized_action))
        self.client.send(msg)
        print('Action message length:', len(msg))

    def receive_network_state(self):
        network_state = self.client.recv(1000).decode('ascii')
        if self.client.fileno() == -1 or not network_state:
            exit()
        print(network_state)
        aggr_flow_throughputs, path_utilizations = network_state.split('|')
        self.aggr_flow_throughputs = map(int, aggr_flow_throughputs.split(';'))
        self.path_utilizations = map(lambda paths: map(int, paths.split(',')), path_utilizations.split(';'))

    def calculate_reward(self):
        reward = 0
        for pair_utilizations in self.path_utilizations:
            mean_utilization = mean(pair_utilizations)
            distance_to_mean = 0
            for utilization in pair_utilizations:
                distance_to_mean += abs(utilization - mean_utilization)
            reward += 1 - float(distance_to_mean) / len(pair_utilizations) / 100
        return reward


