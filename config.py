import os
import redis as r
from rq import Queue
from worker import conn

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis = r.from_url(redis_url)

q = Queue(connection=conn)

