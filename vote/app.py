from flask import Flask, render_template, request, make_response, redirect, g
from redis import Redis
import os
import socket
import random
import json
import logging

option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

@app.route("/", methods=['POST','GET'])
def hello():
    vote_data = {'vote': None, 'voter_id': None}
    vote_cookie = request.cookies.get('vote')
    if vote_cookie:
        vote_data = json.loads(vote_cookie)

    vote = vote_data['vote']
    voter_id = vote_data['voter_id']
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]
        vote_data['voter_id'] = voter_id

    if request.method == 'POST':
        redis = get_redis()
        vote = request.form['vote']
        vote_data['vote'] = vote
        app.logger.info('Received vote for %s', vote)
        data = json.dumps(vote_data)
        redis.rpush('votes', data)
        resp = redirect('/', code=302)
    else:
        resp = make_response(render_template(
            'index.html',
            option_a=option_a,
            option_b=option_b,
            hostname=hostname,
            vote=vote,
        ))

    resp.set_cookie('vote', json.dumps(vote_data))
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
