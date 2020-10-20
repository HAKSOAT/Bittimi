import os
import redis as r

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis = r.from_url(redis_url)
