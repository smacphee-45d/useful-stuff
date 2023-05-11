import redis
import subprocess
import socket
import time
from redis.sentinel import Sentinel

from flask import Flask, request

app = Flask(__name__)
sentinel_1 = "ip here"
sentinel_2 = "ip here"
sentinel_3 = "ip here"
sentinel_port = "sentinel port here"

# define redis and redis sentinel hosts
sentinel = Sentinel([(f'{sentinel_1}', int(sentinel_port)), (f'{sentinel_2}', int(sentinel_port)), (f'{sentinel_3}', int(sentinel_port))], socket_timeout=0.1)
redis_client = sentinel.master_for('mymaster', socket_timeout=0.1)

@app.route('/endpoint', methods=['POST'])
def alert_endpoint():
    alert_data = request.get_json()
    print(f"Received alert data: {alert_data}")

    #Process alert request, check if it has already been processed
    for alert in alert_data['alerts']:
        print(f"Processing alert: {alert}")
        instance = alert['labels']['instance']
        print(f"Instance label value: {instance}")
        last_processed_at = redis_client.get(f'{instance}:last_processed_at')
        if last_processed_at and time.time() - float(last_processed_at) < 300:
            continue

        # store timestamp of most recent request
        redis_client.set(f'{instance}:last_processed_at', time.time())

        # Lock request
        lock = redis_client.lock('script_lock', timeout=60)
        have_lock = lock.acquire(blocking=False)
        if have_lock:
            #run script only if lock is acquired
            try:
                hostname = socket.gethostname()
                print(f"Running script on {hostname}")

                script_path = "/path/to/script/here"
                output = subprocess.check_output([script_path, instance], stderr=subprocess.STDOUT).decode('utf-8')
            finally:
                lock.release()

    return '', 200
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8660)