
from time import time
from _config import PACKET_SIZE_KB

class Flowlet:
    """ Часть потока. """

    def __init__(self, size):
        # Размер flowlet в пакетах.
        self.size = size
        # Время прибытия первого пакета.
        self.arrival_timestamp = None
        # Время отправки первого пакета
        self.departure_timestamp = None
        # Маршрут
        self.route = None

    def arrive():
        pass
    
    def send():
        pass
