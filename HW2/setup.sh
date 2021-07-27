sudo pip install -r requirements.txt

chmod +x ./add_new_node.sh

VPC_CIDR=$(aws ec2 describe-vpcs | jq -r '.Vpcs[0].CidrBlock')
echo "VPC CIDR: $VPC_CIDR"

INSTANCE_ACCESS_SEC_GROUP="instance_access-$(date +'%s')"

echo "Setup a firewall $INSTANCE_ACCESS_SEC_GROUP"
aws ec2 create-security-group --group-name "$INSTANCE_ACCESS_SEC_GROUP" --description "Instances communications"

MY_IP=$(curl ipinfo.io/ip)
echo "My own IP: $MY_IP"

echo "Setup a rule to allow SSH access to only my IP, $MY_IP"
aws ec2 authorize-security-group-ingress --group-name "$INSTANCE_ACCESS_SEC_GROUP" --port 22 --protocol tcp --cidr $MY_IP/32

echo 'Starting to configurate ELB'
python3 elb.py

echo 'Adding first node'
./add_new_node.sh

echo 'Adding second node'
./add_new_node.sh

echo 'Adding third node'
./add_new_node.sh

echo '\n\nEndpoint URL:'
aws elbv2 describe-load-balancers | jq -r '.LoadBalancers[0].DNSName'