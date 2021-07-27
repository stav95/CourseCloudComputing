ticketId=$(curl "$1:5000/entry?plate=123-123-123&parkingLot=382&timestamp=1620205510")
echo $ticketId

curl "$1:5000/exit?ticketId=$ticketId"
echo "\n\n"


ticketId=$(curl "$1:5000/entry?plate=321-321-321&parkingLot=275&timestamp=1620105510")
echo $ticketId

curl "$1:5000/exit?ticketId=$ticketId"
echo "\n\n"


timestamp=$(date +"%s")
timestamp=$(expr $timestamp - 1000)
ticketId=$(curl "$1:5000/entry?plate=666-666-666&parkingLot=66&timestamp=$timestamp")
echo $ticketId

curl "$1:5000/exit?ticketId=$ticketId"






