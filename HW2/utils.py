import urllib.request
from typing import List, Tuple

import jump
import xxhash

APP_PORT = 8080
VPC_PORT = 8081
RING_NODES_N = 1024


def get_node_id() -> str:
    return urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read().decode()


def get_node_idx(nodes_ids: List[str], keys_to_nodes: dict, key: str) -> Tuple[int, int]:
    if key in keys_to_nodes:
        return keys_to_nodes[key]

    v_node_id = xxhash.xxh64(key).intdigest() % RING_NODES_N
    node_idx = jump.hash(v_node_id, len(nodes_ids))

    alt_node_idx = node_idx + 1

    if alt_node_idx == len(nodes_ids):
        alt_node_idx -= 2

    keys_to_nodes.update({key: (node_idx, alt_node_idx)})

    return keys_to_nodes[key]


def get_node_target_id(target: dict) -> str:
    return target['Target']['Id']


def is_node_healthy(nodes: List[dict], node_id: str) -> bool:
    for node in nodes:
        if str(node['Target']['Id']).__eq__(node_id):
            if str(node['TargetHealth']['State']).__eq__('healthy'):
                return True
            else:
                return False

    return False


def filter_healthy_nodes(target: dict) -> bool:
    return str(target['TargetHealth']['State']).__eq__('healthy')


def filter_other_healthy(instance_id: str, targets: List[dict]) -> List[dict]:
    return list(filter(filter_healthy_nodes, [t for t in targets if not get_node_target_id(t).__eq__(instance_id)]))
