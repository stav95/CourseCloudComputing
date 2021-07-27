from typing import List

import boto3
import requests

import utils


# noinspection PyTypeChecker
class Client:
    def __init__(self):
        self.client = boto3.client('ec2')
        self.elb_client = boto3.client('elbv2')
        self.instance_id = utils.get_node_id()
        self.target_group_arn = self.elb_client.describe_target_groups()['TargetGroups'][0]['TargetGroupArn']

    def get_node_ip(self, target_node: dict) -> str:
        try:
            target_node_id = utils.get_node_target_id(target=target_node)

            node_ip = self.client.describe_instances(InstanceIds=[target_node_id])['Reservations'][0]['Instances'][0][
                'PrivateIpAddress']

            return node_ip
        except:
            return None

    # noinspection PyTypeChecker
    def get(self, target_node: dict, str_key: str) -> str:
        node_ip = self.get_node_ip(target_node=target_node)

        if node_ip is None:
            return None

        try:
            response = requests.get(f'http://{node_ip}:{utils.VPC_PORT}/get', params={'str_key': str_key})
        except:
            return None

        return response.text

    # noinspection PyTypeChecker
    def put(self, target_node: dict, str_key: str, data: object, expiration_date: str) -> str:
        node_ip = self.get_node_ip(target_node=target_node)

        if node_ip is None:
            return None

        try:
            response = requests.post(f'http://{node_ip}:{utils.VPC_PORT}/put',
                                     params={'str_key': str_key,
                                             'data': data,
                                             'expiration_date': expiration_date})
        except:
            return None

        return response.text

    def update_id(self, target_node: dict, key: str, node_idx: int, alt_node_idx: int):
        node_ip = self.get_node_ip(target_node=target_node)

        if node_ip is None:
            return None

        try:
            requests.get(f'http://{node_ip}:{utils.APP_PORT}/update-id',
                         params={'key': key,
                                 'node_idx': node_idx,
                                 'alt_node_idx': alt_node_idx})
        except:
            return None

        return

    def get_all_nodes(self) -> List[dict]:
        return self.elb_client.describe_target_health(TargetGroupArn=self.target_group_arn)[
            'TargetHealthDescriptions']

    def get_all_healthy_nodes(self) -> List[dict]:
        all_targets = self.get_all_nodes()
        healthy_targets = list(filter(utils.filter_healthy_nodes, all_targets))
        return healthy_targets

    def get_cache(self, target_node: dict) -> str:
        node_ip = self.get_node_ip(target_node=target_node)

        if node_ip is None:
            return None

        response = requests.get(f'http://{node_ip}:{utils.VPC_PORT}/cache')

        return None if response.status_code != 200 else response.json()
