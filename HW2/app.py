import json
from typing import List

from flask import Flask, Response, request

import utils
from client import Client

app = Flask(__name__)
client = Client()

nodes_ids = []
keys_to_nodes = {}


def fill_nodes_ids() -> List[dict]:
    all_nodes = client.get_all_nodes()
    for node in all_nodes:
        node_id = node['Target']['Id']

        if node_id in nodes_ids:
            continue

        nodes_ids.append(node_id)

        for k in keys_to_nodes.keys():
            client.update_id(target_node=node, key=k, node_idx=keys_to_nodes[k][0], alt_node_idx=keys_to_nodes[k][1])

    return all_nodes


@app.route('/put')
def put_into_cache() -> str:
    str_key = request.args.get('str_key', default="")
    data = request.args.get('data', default=None)
    expiration_date = request.args.get('expiration_date', default=None)

    all_nodes = fill_nodes_ids()

    node_idx, alt_node_idx = utils.get_node_idx(nodes_ids=nodes_ids, keys_to_nodes=keys_to_nodes, key=str_key)

    healthy_nodes = client.get_all_healthy_nodes()

    _ = [client.update_id(target_node=node, key=str_key, node_idx=node_idx, alt_node_idx=alt_node_idx)
         for node in healthy_nodes]

    target_nodes = []

    if utils.is_node_healthy(nodes=all_nodes, node_id=nodes_ids[node_idx]):
        target_nodes.append({'Target': {'Id': nodes_ids[node_idx]}})
    if utils.is_node_healthy(nodes=all_nodes, node_id=nodes_ids[alt_node_idx]):
        target_nodes.append({'Target': {'Id': nodes_ids[alt_node_idx]}})

    _ = [client.put(target_node=node, str_key=str_key, data=data, expiration_date=expiration_date)
         for node in target_nodes]

    keys_to_nodes.update({str_key: (node_idx, alt_node_idx)})

    results = [data for data in _ if data is not None]

    if len(results) > 0:
        return results[0]
    return ''


@app.route('/get')
def get_from_cache() -> str:
    str_key = request.args.get('str_key', default="")

    fill_nodes_ids()

    if len(str_key) == 0 or str_key not in keys_to_nodes:
        # print(len(str_key), [k for k in keys_to_nodes.keys()])
        # return f'{utils.get_node_id()}, {[k for k in keys_to_nodes.keys()]}'
        return Response(status=404)

    node_idx, alt_node_idx = keys_to_nodes.get(str_key)

    target_nodes = [{'Target': {'Id': nodes_ids[node_idx]}},
                    {'Target': {'Id': nodes_ids[alt_node_idx]}}]

    _ = [client.get(target_node=node, str_key=str_key) for node in target_nodes]

    results = [data for data in _ if data is not None]

    if len(results) > 0:
        return results[0]

    return Response(status=200)

    # if len(results) > 0:
    #     return f'{utils.get_node_id()}, {node_idx}, {alt_node_idx}\n{results[0]}'
    # return f'{utils.get_node_id()}, {node_idx}, {alt_node_idx}'


@app.route('/cache')
def get_all_cache() -> str:
    all_cache = [client.get_cache(node) for node in client.get_all_healthy_nodes()]

    return json.dumps(all_cache, indent=2)


@app.route('/update-id')
def update_id():
    fill_nodes_ids()

    key = request.args.get('key', default=None)

    is_none = False

    if key is None:
        is_none = True

    node_idx = request.args.get('node_idx', default=None)

    if node_idx is None:
        is_none = True

    alt_node_idx = request.args.get('alt_node_idx', default=None)

    if alt_node_idx is None:
        is_none = True

    if is_none:
        keys = [f'{k}, {keys_to_nodes[k][0]}, {keys_to_nodes[k][1]}' for k in keys_to_nodes.keys()]
        return str.join('\n', [utils.get_node_id()] + keys)
    else:
        keys_to_nodes.update({key: (int(node_idx), int(alt_node_idx))})
        return Response(status=200)


@app.route('/health-check')
def health_check():
    return Response(status=200)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=utils.APP_PORT, debug=True)
