
class Log:

    def __init__(self, prefix: str):
        self.prefix_length = 10
        self.prefix = prefix

    def log(self, *msg):
        print(f'{self.prefix:{self.prefix_length}}', *msg)
