import sys
import subprocess
import json
import time
import re

def main():
    hostname = sys.argv[1]
    child_osds = process_json(hostname)
    for osd, weight in child_osds.items():
        command = ["ceph", "osd", "crush", "remove", f"osd.{osd}"]
        result = subprocess.run(command, capture_output=True, text=True)
        print(f'Command output: {result.stdout}')
    wait_for_pg()
    print("PGs back to normal")
    for osd, weight in child_osds.items():
        command = ["ceph", "osd", "crush", "add", f"osd.{osd}", str(weight), "root=default", f"host={hostname}"]
        result = subprocess.run(command, capture_output=True, text=True)
        print(f'Command output: {result.stdout}')
        command = ["ceph", "osd", "crush", "set-device-class", "hdd", f"osd.{osd}"]
        result = subprocess.run(command, capture_output=True, text=True)
        print(f'Command output: {result.stdout}')


def process_json(hostname):
    osd_tree = subprocess.check_output(["ceph", "osd", "tree", "--format", "json-pretty"], stderr=subprocess.STDOUT).decode('utf-8')
    json_data = json.loads(osd_tree)
    osd_weights = {}
    children = None
    for node in json_data['nodes']:
        if node['type'] == 'host' and node['name'] == hostname:
            children = node['children']
        elif children is not None and node['type'] == 'osd' and node['id'] in children: 
            osd_weights[node['id']] = node['crush_weight']
    if not children:
        print(f"No children OSDs found for host {hostname}")
        sys.exit(1)

    return osd_weights

def wait_for_pg():
    stop_state = "active+undersized"
    acceptable_states = ["active+undersized+degraded", "active+undersized+backfill"]
    while True:
        result = subprocess.run(["ceph", "-s", "--format", "json-pretty"], capture_output=True, text=True)
        output = json.loads(result.stdout)
        pgs_by_state = output["pgmap"]["pgs_by_state"]
        undersized_found = False
        for pg in pgs_by_state:
            if pg["state_name"] == stop_state and pg["state_name"] not in acceptable_states:
                undersized_found = True
                break
        if not undersized_found:
            break
        time.sleep(5)


if __name__ == "__main__":
    main()