import os

from rq import Worker, Queue, Connection

from config import redis

listen = ['high', 'default', 'low']


q = Queue(connection=redis, default_timeout=1500)


if __name__ == '__main__':
    with Connection(redis):
        worker = Worker(map(Queue, listen))
        worker.work()
