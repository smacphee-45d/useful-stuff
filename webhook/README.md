#Alertmanager Webhook

This webhook recieves an alert from alertmanager and triggers a script. It utilizes Redis-Sentinel to allow multiple webhook servers to exist simulatenous and be available. Distributed locks are then used to ensure that only one webhook actually runs the script. 

#Prereqs 

- Redis-Sentinel 
- Alertmanager 
- Python3

#Installation 

- install Redis/Redis-Sentinel 
- modify alertmanager to with webhook recievers
- modify alertmanager with a route for given alert to the webhook servers
- configure redis/redis-sentinel on each node 
- run web server 

