import sys
import subprocess
import json
import time
import re

def main():
    #pass hostname command arg and use in json function
    if len(sys.argv) != 2:
        print("Only one hostname can be provided")
        sys.exit(1)
    hostname = sys.argv[1]
    if " " in hostname:
        print("Spaces cannot be in hostnames")
        sys.exit(1)
    child_osds = process_json(hostname)
    #remove each found osd child from crushmap
    for osd, weight in child_osds.items():
        command = ["ceph", "osd", "crush", "remove", f"osd.{osd}"]
        subprocess.run(command, capture_output=True, text=True)
    #wait for all PGs to be in an acceptable state
    wait_for_pg()
    print("PGs back to normal")
    #readd all OSDs at original weights
    for osd, weight in child_osds.items():
        command = ["ceph", "osd", "crush", "add", f"osd.{osd}", str(weight), "root=default", f"host={hostname}"]
        subprocess.run(command, capture_output=True, text=True)
        command = ["ceph", "osd", "crush", "set-device-class", "hdd", f"osd.{osd}"]
        subprocess.run(command, capture_output=True, text=True)

#pull OSDs and OSD weights from ceph osd tree by hostname
def process_json(hostname):
    osd_tree = subprocess.check_output(["ceph", "osd", "tree", "--format", "json-pretty"], stderr=subprocess.STDOUT).decode('utf-8')
    json_data = json.loads(osd_tree)
    osd_weights = {}
    for node in json_data['nodes']:
        if node['type'] == 'host' and node['name'] == hostname:
            children = node['children']
        elif node['type'] == 'osd' and node['id'] in children:
            osd_weights[node['id']] = node['crush_weight']
    return osd_weights

#wait for all PGs to not be active+undersized only
def wait_for_pg():
    stop_state = "active+undersized"
    #
    valid_states = ["active+undersized+degraded", "active+undersized+backfill"]
    while True:
        result = subprocess.run(["ceph", "-s", "--format", "json-pretty"], capture_output=True, text=True)
        output = json.loads(result.stdout)
        pgs_by_state = output["pgmap"]["pgs_by_state"]
        undersized_pg = False
        for pg in pgs_by_state:
            if pg["state_name"] == stop_state and pg["state_name"] not in valid_states:
                undersized_pg = True
                break
        if not undersized_pg:
            break
        time.sleep(5)


if __name__ == "__main__":
    main()