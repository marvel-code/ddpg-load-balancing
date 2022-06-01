from statistics import mean
from typing import Dict, List
from typing_extensions import TypedDict
import gym
from gym import spaces
import numpy as np
import socket

from random import randint
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
EDGE_PAIRS = EDGE_COUNT * (EDGE_COUNT - 1)

PATH_COUNT = SAME_POD_EDGE_PAIRS * PATH_COUNT_TO_SAME_POD_EDGE + OTHER_POD_EDGE_PAIRS * PATH_COUNT_TO_OTHER_POD_EDGE

AFT_MSG_LEN = 4 * EDGE_PAIRS
REWARD_MSG_LEN = 0
PATH_UTILIZATIONS = PATH_COUNT

SEND_MSG_LEN = PATH_COUNT_PER_EDGE * EDGE_COUNT
RECV_MSG_LEN = AFT_MSG_LEN + REWARD_MSG_LEN + PATH_UTILIZATIONS

LINK_CAPACITY_BPS = int(100 * 1024 * 1024)
AGGR_FLOW_CAPACITY_BPS = LINK_CAPACITY_BPS * AGGR_PER_POD_COUNT

# Agent

OBSERVATION_DTYPE = np.int32
ACTION_DTYPE = np.float32

OBSERVATION_SIZE = EDGE_PAIRS
ACTION_SIZE = EDGE_COUNT * PATH_COUNT_PER_EDGE


def decodeInt(msg: bytes) -> int:
  a = int(msg[0])
  b = int(msg[1] << 8)
  c = int(msg[2] << 16)
  d = int(msg[3] << 24)
  return a + b + c + d


def group_flat_path_utilizations(flat_path_utilizations):
    result = []
    for i in range(EDGE_COUNT):
        edge_path_utilizations = list(map(lambda x: int(x), flat_path_utilizations[i * PATH_COUNT_PER_EDGE: (i+1) * PATH_COUNT_PER_EDGE]))
        for j in range(OTHER_POD_EDGE_PAIRS):
            result.append(edge_path_utilizations[j * PATH_COUNT_TO_OTHER_POD_EDGE: (1+j) * PATH_COUNT_TO_OTHER_POD_EDGE])
        for j in range(SAME_POD_EDGE_PAIRS):
            result.append(edge_path_utilizations[-(1+j) * PATH_COUNT_TO_OTHER_POD_EDGE: len(edge_path_utilizations)-j * PATH_COUNT_TO_SAME_POD_EDGE])
    return result


l = Log('env')
class CustomEnv(gym.Env):
    """Custom Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(CustomEnv, self).__init__()
        # Throughput for each aggr flow
        self.observation_space = spaces.Box(
            low=0, 
            high=AGGR_FLOW_CAPACITY_BPS, 
            shape=(OBSERVATION_SIZE,), 
            dtype=OBSERVATION_DTYPE
        )
        # Proportion for each path (not normalized)
        self.action_space = spaces.Box(
            low=0, 
            high=100, 
            shape=(ACTION_SIZE,), 
            dtype=ACTION_DTYPE
        )
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

        observation = self.get_observation()
        reward = self.calculate_reward()
        done = False
        info = {}
        
        return observation, reward, done, info

    def reset(self):
        self.aggr_flow_throughputs = np.array([0] * OBSERVATION_SIZE, dtype=OBSERVATION_DTYPE)
        return self.aggr_flow_throughputs
        
    def render(self, mode='human'):
        # ...
        pass

    def close(self):
        self.client.close()

    # Other

    def send_action(self, flataction: List[float]):
        # Action per edge
        action = [flataction[i:i+PATH_COUNT_PER_EDGE] for i in range(0, len(flataction), PATH_COUNT_PER_EDGE)]

        # Normalize actions
        normalized_action: List[List[int]] = []
        for edge_action in action:
            i = 0
            while i < len(edge_action):
                edgepair_action = edge_action[i:i + PATH_COUNT_TO_OTHER_POD_EDGE]
                s = sum(edgepair_action)
                if s != 0:
                    norm_action = []
                    ns = 0
                    for x in edgepair_action:
                        p = int(x / s * 100)
                        ns += p
                        norm_action.append(p)
                    
                    # Complete action, for sum(norm_action)==100
                    norm_action[0] = norm_action[0] + 100 - ns
                    
                    normalized_action.append(norm_action)
                else:
                    normalized_action.append([100/PATH_COUNT_PER_EDGE]*PATH_COUNT_PER_EDGE)
                i += PATH_COUNT_TO_OTHER_POD_EDGE

        # Send action
        msg = b''.join(map(lambda x: b''.join(map(lambda y: y.to_bytes(1, 'big'), x)), normalized_action))
        if (len(msg) != SEND_MSG_LEN):
            raise Exception(f'Invalid message length: {len(msg)} != {SEND_MSG_LEN}, {msg}')
        self.client.send(msg)

    def receive_network_state(self):
        network_state_bytes = self.client.recv(RECV_MSG_LEN)
        if self.client.fileno() == -1 or not network_state_bytes:
            exit()

        self.aggr_flow_throughputs = np.array([decodeInt(network_state_bytes[i:i+4]) for i in range(0, EDGE_PAIRS * 4, 4)], dtype=OBSERVATION_DTYPE)
        self.path_utilizations = group_flat_path_utilizations(network_state_bytes[EDGE_PAIRS * 4:])
        print(self.path_utilizations)
        self.received_reward = None#decodeInt(network_state_bytes[EDGE_PAIRS * 4:])

    # Observation
    def get_observation(self):
        return self.aggr_flow_throughputs

    # Reward
    def calculate_reward(self):
        reward = 0
        if self.received_reward:
            # Reward is received from env (omnet++)
            reward = self.received_reward
            self.received_reward = 0
            print('Received reward:', reward)
        else:
            # Calculate reward
            for pair_utilizations in self.path_utilizations:
                mean_utilization = mean(pair_utilizations)
                distance_to_mean = 0
                for utilization in pair_utilizations:
                    distance_to_mean += abs(utilization - mean_utilization)
                reward += 1 - float(distance_to_mean) / len(pair_utilizations) / 100
                
            print('Calculated reward:', reward)
        #print('Reward:', reward)
        return reward


