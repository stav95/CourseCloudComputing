import sys
from typing import List

import boto3
import utils

ITEMS_PREFIX = f'elb-cache'
SG_INSTANCES_ACCESS = f'{ITEMS_PREFIX}-cache-instance-access'
SG_ELB_ACCESS = f'{ITEMS_PREFIX}-access'

elb = boto3.client('elbv2')
ec2 = boto3.client('ec2')


def init_security_groups(vpc_id: str) -> str:
    try:
        response = ec2.describe_security_groups(GroupNames=[f'{ITEMS_PREFIX}elb-access'])
        elb_access = response['SecurityGroups'][0]
        # response = ec2.describe_security_groups(GroupNames=['{ITEMS_PREFIX}instance-access'])
        # instance_access = response["SecurityGroups"][0]
        return elb_access['GroupId']
        # return elb_access["GroupId"], instance_access["GroupId"]
    except:
        pass

    cidr_block = ec2.describe_vpcs(VpcIds=[vpc_id])['Vpcs'][0]['CidrBlock']

    _sg = ec2.create_security_group(Description='Elastic Load Balancer External Access',
                                    GroupName=SG_ELB_ACCESS,
                                    VpcId=vpc_id)

    elb_sg = boto3.resource('ec2').SecurityGroup(_sg['GroupId'])
    elb_sg.authorize_ingress(CidrIp='0.0.0.0/0', FromPort=utils.APP_PORT, ToPort=utils.APP_PORT, IpProtocol='TCP', )

    instances = ec2.create_security_group(Description='Elastic Load Balancer Allow Instances to Access',
                                          GroupName=SG_INSTANCES_ACCESS,
                                          VpcId=vpc_id)

    for p in [utils.APP_PORT, utils.VPC_PORT]:
        instance_sg = boto3.resource('ec2').SecurityGroup(instances['GroupId'])
        instance_sg.authorize_ingress(CidrIp=cidr_block, FromPort=p, ToPort=p, IpProtocol='TCP')

    return _sg["GroupId"]
    # return _sg["GroupId"], instances["GroupId"]


def get_default_subnets() -> List[str]:
    response = ec2.describe_subnets(Filters=[{'Name': 'default-for-az', 'Values': ['true']}])
    subnet_ids = [s['SubnetId'] for s in response['Subnets']]
    return subnet_ids


def create_elb() -> dict:
    try:
        return elb.describe_load_balancers(Names=[ITEMS_PREFIX])
    except:
        return elb.create_load_balancer(Name=ITEMS_PREFIX,
                                        Scheme='internet-facing',
                                        IpAddressType='ipv4',
                                        Subnets=get_default_subnets())


# creates the ELB as well as the target group
# that it will distribute the requests to
def elb_setup():
    elb_as_dict = create_elb()

    elb_arn = elb_as_dict['LoadBalancers'][0]['LoadBalancerArn']
    vpc_id = elb_as_dict['LoadBalancers'][0]['VpcId']

    elb_access = init_security_groups(vpc_id=vpc_id)
    elb.set_security_groups(LoadBalancerArn=elb_arn, SecurityGroups=[elb_access])
    target_group = None
    try:
        target_group = elb.describe_target_groups(Names=[f'{ITEMS_PREFIX}-tg'], )
    except:
        target_group = elb.create_target_group(Name=f'{ITEMS_PREFIX}-tg',
                                               Protocol='HTTP',
                                               Port=utils.APP_PORT,
                                               VpcId=vpc_id,
                                               HealthCheckProtocol='HTTP',
                                               HealthCheckPort=str(utils.APP_PORT),
                                               HealthCheckPath='/health-check',
                                               TargetType='instance')

    target_group_arn = target_group['TargetGroups'][0]['TargetGroupArn']
    listeners = elb.describe_listeners(LoadBalancerArn=elb_arn)

    if len(listeners['Listeners']) == 0:
        elb.create_listener(LoadBalancerArn=elb_arn,
                            Protocol='HTTP',
                            Port=utils.APP_PORT,
                            DefaultActions=[{
                                'Type': 'forward',
                                'TargetGroupArn': target_group_arn,
                                'Order': 100}])


def register_new_node_to_elb(instance_id: str):
    instance_access_sg = ec2.describe_security_groups(GroupNames=[SG_INSTANCES_ACCESS])['SecurityGroups'][0]['GroupId']
    target_group = elb.describe_target_groups(Names=[f'{ITEMS_PREFIX}-tg'])

    instance = boto3.resource('ec2').Instance(instance_id)

    sgs = [sg['GroupId'] for sg in instance.security_groups]
    sgs.append(instance_access_sg)

    instance.modify_attribute(Groups=sgs)
    target_group_arn = target_group['TargetGroups'][0]['TargetGroupArn']
    elb.register_targets(TargetGroupArn=target_group_arn,
                         Targets=[{'Id': instance_id,
                                   'Port': utils.APP_PORT}])


def get_targets_status() -> (list, dict):
    target_group = elb.describe_target_groups(Names=[f'{ITEMS_PREFIX}-tg'])
    target_group_arn = target_group['TargetGroups'][0]['TargetGroupArn']

    health = elb.describe_target_health(TargetGroupArn=target_group_arn)
    healthy = []
    not_healthy = {}
    for target in health['TargetHealthDescriptions']:
        if str(target['TargetHealth']['State']).__eq__('unhealthy'):
            not_healthy[target['Target']['Id']] = target['TargetHealth']['Description']
        else:
            healthy.append(target['Target']['Id'])

    return healthy, not_healthy


if __name__ == '__main__':
    if len(sys.argv) == 1:
        elb_setup()
    elif sys.argv[1] == 'register_new_node':
        register_new_node_to_elb(sys.argv[2])
