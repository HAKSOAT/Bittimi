import os

from rq import Worker, Queue, Connection
from rq.registry import StartedJobRegistry


from config import redis

listen = ['high', 'default', 'low']


q = Queue(connection=redis)
registry = StartedJobRegistry('default', connection=redis)


if __name__ == '__main__':
    with Connection(redis):
        worker = Worker(map(Queue, listen))
        worker.work()
