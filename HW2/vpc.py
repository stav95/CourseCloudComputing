from flask import Flask, request

from cache import Cache
import utils

app = Flask(__name__)
cache = Cache()
instance_id = utils.get_node_id()

nodes_ids = []
keys_to_nodes = {}


@app.route('/put', methods=['POST'])
def put_to_cache():
    str_key = request.args.get('str_key', default="")
    data = request.args.get('data', default=None)
    expiration_date = request.args.get('expiration_date', default=None)

    cache.put(str_key, data, expiration_date)
    return f'Success puting data into cache, instance_id: {instance_id}\n'


@app.route('/get', methods=['GET'])
def get_from_cache():
    return cache.get(request.args.get('str_key', default=''))


@app.route('/cache', methods=['GET'])
def get_all_cache():
    data = cache.get_all_cache()
    return {
        'instance_id': instance_id,
        'cache': data
    }


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=utils.VPC_PORT, debug=True)
