INSTANCE_AMI="ami-09e67e426f25ce0d7" # UBUNTU_20_04_AMI
KEY_NAME="cloud-computing-cache-$(date +'%s')"
KEY_PEM="$KEY_NAME.pem"

INSTANCE_ACCESS_SEC_GROUP=$(aws ec2 describe-security-groups --filters Name=group-name,Values=instance_access-* | jq '.SecurityGroups[0].GroupName' | tr -d '"')

echo "Creating new Key-pair $KEY_PEM"
aws ec2 create-key-pair --key-name "$KEY_NAME" | jq -r ".KeyMaterial" >"$KEY_PEM"

chmod 400 "$KEY_PEM"

echo "Creating new instance (Ubuntu 20.04)"
INSTANCE_ID=$(aws ec2 run-instances --image-id $INSTANCE_AMI --instance-type t2.micro --key-name "$KEY_NAME" --security-groups "$INSTANCE_ACCESS_SEC_GROUP" | jq -r '.Instances[0].InstanceId')

aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

PUBLIC_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" | jq -r '.Reservations[0].Instances[0].PublicIpAddress')

echo "New instance ID: $INSTANCE_ID and IP: $PUBLIC_IP"

echo "Adding the instance into the elb target group"
python3 ./elb.py register_new_node "$INSTANCE_ID"

echo "Adding code into the instance"
scp -i "$KEY_PEM" -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=60" -r ~/.aws app.py cache.py client.py utils.py vpc.py requirements.txt ubuntu@"$PUBLIC_IP":/home/ubuntu/

echo "sleep for 5 seconds..."
sleep 5

echo "Setup the new instance"
ssh -i "$KEY_PEM" -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" ubuntu@"$PUBLIC_IP" <<EOF
    sudo apt update -y
    sudo apt-get install python3-pip -y
    sudo apt install net-tools
    sudo pip install -r requirements.txt

    nohup python3 app.py &>/dev/null &
    nohup python3 vpc.py &>/dev/null &

    exit
EOF

echo "The new instance is ready and running."
