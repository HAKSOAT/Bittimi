import json
import re
import uuid

from flask import Flask, request, jsonify

from utils import place_order, validate, get_status
from config import redis
from worker import q


app = Flask(__name__)

timeout = 1500


@app.route('/')
def index():
    return jsonify(success=True)


@app.route('/run', methods=['POST'])
def run():
    if request.method == 'POST':
        errors, data = validate(request.json)
        if errors:
            return jsonify(errors=errors), 400
        
        id_ = str(uuid.uuid4())
        while redis.get(id_):
            id_ = str(uuid.uuid4())

        rear_id = str(redis.get('rear_id'))

        data.update({'depends_on': rear_id})
        queue = q.enqueue(place_order, id_, **data)

        redis.set('rear_id', queue.id, ex=timeout)
        redis.set(id_, json.dumps({}), ex=timeout)
        return jsonify(id=id_)


@app.route('/pull', methods=['GET'])
def pull():
    id_ = request.args.get('id')
    result = redis.get(id_)
    if result is None:
        return jsonify(error='Resource does not exist'), 404
    else:
        data = json.loads(result)
        if data.get('amount', None):
            data.update({'completed': get_status(id_)})
        return jsonify(data)


@app.route('/email', methods=['POST'])
def email():
    message = request.json.get('message', '')
    code = re.search(r'\b[A-Z\d]{4,}', message).group()
    redis.set('login_code', code, ex=60)
    return jsonify(success=True)


if __name__ == "__main__":
    app.run()
