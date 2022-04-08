from typing import Dict, List
from datacollector.datacollector import DataCollector, LinkState
import socket
from log import Log

HOST = '127.0.0.1'
PORT = 50123

l = Log('main')

if __name__ == '__main__':
    # a = Agent(env)
    data_collector = DataCollector()
    
    def processDataCollectorUpdate(msg: str):
        p = msg.split(',')
        time: str = p[0]
        target_node_name: str = p[1]
        utilizations = map(lambda x: x.split('='), p[2:])
        link_states: Dict[str, LinkState] = {}
        for u in utilizations:
            link_states[u[0]] = {
                'utilization': int(u[1]),
            }
        data_collector.update(target_node_name, link_states)


    # Connection to controller
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    while True:
        s.listen(1)
        l.log('Waiting connection...')
        conn, addr = s.accept()
        l.log('Connection: ', addr)
        while True:
            try:
                msg = conn.recv(1000).decode('ascii')
                if conn.fileno() == -1 or not msg:
                    break
                for m in msg.split('\0'):
                    if m:
                        processDataCollectorUpdate(m)
                conn.send(b'ok')
            except Exception as ex:
                l.log('EXCEPTION:', ex)
                conn.close()
                break
        
        data_collector.reset()

