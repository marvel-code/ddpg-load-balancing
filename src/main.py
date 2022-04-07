from datacollector.datacollector import DataCollector
import socket
from log import Log

HOST = '127.0.0.1'
PORT = 50123

l = Log('main')

if __name__ == '__main__':
    # a = Agent(env)
    data_collector = DataCollector()

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
                msg = conn.recv(1000)
                l.log(msg)
                if conn.fileno() == -1:
                    break
            except Exception as ex:
                l.log('EXCEPTION:', ex)
                conn.close()
                break
        
        data_collector.reset()

