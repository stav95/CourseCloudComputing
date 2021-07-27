timestamp=$(date +"%s")

REGION=$(aws ec2 describe-availability-zones | jq -r .AvailabilityZones[0].RegionName)
AWS_ACCOUNT=$(aws sts get-caller-identity  | jq -r .Account)
AWS_ROLE="lambda-role-$timestamp"
FUNC_NAME="my-func-$timestamp"
API_NAME="api-gateway-$timestamp"

echo "Setting up new lambda"
r=$(aws iam create-role --role-name $AWS_ROLE --assume-role-policy-document file://trust-policy.json)

aws iam attach-role-policy --role-name $AWS_ROLE --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

r=$(zip lambda.zip lambda_function.py)

aws iam wait role-exists --role-name $AWS_ROLE
ARN_ROLE=$(aws iam get-role --role-name $AWS_ROLE | jq -r .Role.Arn)

echo "Workaround consistency rules in AWS roles after creation... (sleep 10)"
sleep 10

f=$(aws lambda create-function --function-name $FUNC_NAME --zip-file fileb://lambda.zip --handler lambda_function.lambda_handler --runtime python3.8 --role $ARN_ROLE)

FUNC_ARN=$(aws lambda get-function --function-name $FUNC_NAME | jq -r .Configuration.FunctionArn)

API_CREATED=$(aws apigatewayv2 create-api --name $API_NAME --protocol-type HTTP --target $FUNC_ARN)
API_ID=$(echo $API_CREATED | jq -r .ApiId)
API_ENDPOINT=$(echo $API_CREATED | jq -r .ApiEndpoint)

STMT_ID=$(uuidgen)

p=$(aws lambda add-permission --function-name $FUNC_NAME --statement-id $STMT_ID --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:$REGION:$AWS_ACCOUNT:$API_ID/*")

echo "The creation of new lambda & api endpoint is done."

stack_name="stack$timestamp"
key_pair_name="key_pair_$timestamp"
key_pem="$key_pair_name.pem"

echo "Stack Name:"
echo $stack_name
echo


aws ec2 create-key-pair --key-name $key_pair_name --query 'KeyMaterial' --output text > key_pair_$timestamp.pem
chmod 400 key_pair_$timestamp.pem

stack_id=$(aws cloudformation create-stack --stack-name $stack_name --template-body file://template.json --parameters ParameterKey=KeyPair,ParameterValue=$key_pair_name | jq .StackId | tr -d '"')
echo "Stack ID:"
echo $stack_id
echo

echo 'Wating for stack to be completed...'
aws cloudformation wait stack-create-complete --stack-name $stack_id
echo 'Stack completed'
echo

instance_id=$(aws cloudformation describe-stack-resource --stack-name $stack_name --logical-resource-id WebServerInstance | jq .StackResourceDetail.PhysicalResourceId | tr -d '"')
echo "Instance ID:"
echo $instance_id
echo

public_dns_name=$(aws ec2 describe-instances  --instance-ids $instance_id | jq .Reservations[0].Instances[0].PublicDnsName | tr -d '"')
echo "Public DNS Name:"
echo $public_dns_name
echo

public_ip=$(aws ec2 describe-instances  --instance-ids $instance_id | jq .Reservations[0].Instances[0].PublicIpAddress | tr -d '"')
echo "Public Ip Address:"
echo $public_ip  
echo


ssh -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" -i $key_pem ubuntu@$public_dns_name << EOF
echo $API_ENDPOINT/ >> lambda_endpoint
sudo apt-get -y update
sudo apt-get -y upgrade 
sudo apt install python3-flask -y
sudo apt -y install python3-pip
pip3 install flask requests

git clone https://gist.github.com/26f0bd33edf979d3066bb5b482947682.git app
exit

EOF


ssh -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" -i $key_pem ubuntu@$public_dns_name << EOF
export FLASK_APP=./app/app.py
nohup flask run --host 0.0.0.0  &>/dev/null &
exit

EOF


echo "Public Ip Address:"
echo $public_ip 


