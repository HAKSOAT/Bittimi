import io
import json

from flask import Flask, request, jsonify

from utils import fetch, validate, generate_id
from config import redis
from worker import q, registry


app = Flask(__name__)


@app.route('/')
def index():
    return jsonify(success=True)


@app.route('/run', methods=['POST'])
def run():
    if request.method == 'POST':
        errors, data = validate(request.json)
        if errors:
            return jsonify(errors=errors), 400
        
        id_ = generate_id()
        while redis.get(id_):
            id_ = generate_id()

        job_ids = q.get_job_ids()
        print(job_ids)
        rear_id = job_ids[-1] if job_ids else None

        data.update({'depends_on': rear_id})
        queue = q.enqueue(fetch, id_, **data)

        print(dir(queue))

        redis.set(id_, json.dumps({}), ex=900)
        # redis.set('{}_jid'.format(id_), queue, ex=900)
        return jsonify(id = id_)


@app.route('/pull', methods=['GET'])
def pull():
    id_ = request.args.get('id')
    result = redis.get(id_)
    if result is None:
        return jsonify(error='Resource does not exist'), 404
    else:
        return jsonify(result=json.loads(result))


if __name__ == "__main__":
    app.run()