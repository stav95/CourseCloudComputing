**Exercise 2: Caching in the cloud**

Stav Yosef - 316298876

Daniel Sabba - 311500227



To run this exercise, clone this repository & set the default region to "us-east-1"
1. chmod +x ./setup.sh
2. ./setup.sh 



**Simulation:**
1. {DNSName}:8080/cache
2. {DNSName}:8080/put?str_key=key1&data=data1
3. {DNSName}:8080/put?str_key=key2&data=data2
4. {DNSName}:8080/put?str_key=key3&data=data3
5. {DNSName}:8080/put?str_key=key4&data=data4
6. {DNSName}:8080/put?str_key=key5&data=data5
7. {DNSName}:8080/cache
8. Remove a random node and check if all data still available using {DNSName}:8080/get?str_key={key}
9. Add new node using ./add_new_node.sh and play with the system :)
10. Enjoy!
