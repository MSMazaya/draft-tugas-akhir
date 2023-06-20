import requests
import time
import json
import copy
from configuration import STREAM_FILE_PATH, FETCHER_INTERVAL_SEC, ELASTICSEARCH_HOST

GIB = 1073741824

LAST_FETCH = {}

def fetch_node_stats():
    url = ELASTICSEARCH_HOST + '/_nodes/stats'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        nodes = data["nodes"]
        nodeTranslated = {}
        for nodeId in nodes.keys():
            curr = nodes[nodeId]
            indices = curr["indices"]
            name = curr["name"]
            nodeTranslated[name] = {
                "id": nodeId,
                "timestamp": curr["timestamp"],
                "name": curr["name"],
                "write_load": indices["indexing"]["write_load"],
                "time": {
                    "index": indices["indexing"]["index_time_in_millis"],
                    "get": indices["get"]["time_in_millis"],
                    "query": indices["search"]["query_time_in_millis"],
                    "fetch": indices["search"]["fetch_time_in_millis"],
                    "scroll": indices["search"]["scroll_time_in_millis"],
                    "suggest": indices["search"]["suggest_time_in_millis"],
                    "bulk": indices["bulk"]["total_time_in_millis"],
                    "flush": indices["flush"]["total_time_in_millis"],
                    "refresh": indices["refresh"]["total_time_in_millis"],
                },
                "total": {
                    "index": indices["indexing"]["index_total"],
                    "get": indices["get"]["total"],
                    "query": indices["search"]["query_total"],
                    "fetch": indices["search"]["fetch_total"],
                    "scroll": indices["search"]["scroll_total"],
                    "suggest": indices["search"]["suggest_total"],
                    "bulk": indices["bulk"]["total_operations"],
                    "flush": indices["flush"]["total"],
                    "refresh": indices["refresh"]["total"],
                },
                "cpu": {
                    "percent": curr["os"]["cpu"]["percent"],
                    "load_avg_1m": curr["os"]["cpu"]["load_average"]["1m"],
                    "load_avg_5m": curr["os"]["cpu"]["load_average"]["5m"],
                    "load_avg_15m": curr["os"]["cpu"]["load_average"]["15m"],
                },
                "mem": {
                    "total_gib": curr["os"]["mem"]["total_in_bytes"]/GIB,
                    "used_percent": curr["os"]["mem"]["used_percent"],
                    "free_percent": curr["os"]["mem"]["free_percent"],
                },
                "delta_time": {
                    "index": 0,
                    "get": 0,
                    "query": 0,
                    "fetch": 0,
                    "scroll": 0,
                    "suggest": 0,
                    "bulk": 0,
                    "flush": 0,
                    "refresh": 0,
                },
                "delta_total": {
                    "index": 0,
                    "get": 0,
                    "query": 0,
                    "fetch": 0,
                    "scroll": 0,
                    "suggest": 0,
                    "bulk": 0,
                    "flush": 0,
                    "refresh": 0,
                }
            }
        if name in LAST_FETCH:
            changed = nodeTranslated[name]
            for each in changed["delta_time"].keys():
                changed["delta_time"][each] = nodeTranslated[name]["time"][each] - LAST_FETCH[name]["time"][each]
            for each in changed["delta_total"].keys():
                changed["delta_total"][each] = nodeTranslated[name]["total"][each] - LAST_FETCH[name]["total"][each]
        LAST_FETCH[name] = nodeTranslated[name]
        with open(STREAM_FILE_PATH, 'a') as file:
            copied = copy.deepcopy(nodeTranslated)
            for unused in ["time", "total"]:
                for each in copied.keys():
                    del copied[each][unused]
            file.write(json.dumps(copied, separators=(',', ':')))
            file.write('\n')
    else:
        print('Failed to fetch node stats')

# def fetch_cluster_stats():
#     url = 'http://localhost:9200/_cluster/stats'
#     response = requests.get(url)

#     if response.status_code == 200:
#         data = response.json()
#         cpu_percent = data['nodes']['process']['cpu']['percent']

#         mem_free = data['nodes']['os']['mem']['free_in_bytes']/GIB
#         mem_used = data['nodes']['os']['mem']['used_in_bytes']/GIB
#         mem_total = data['nodes']['os']['mem']['total_in_bytes']/GIB
#         mem_percent = data['nodes']['os']['mem']['used_percent']

#         print(f'CPU Usage: {cpu_percent}%')
#         print(f'Memory Usage: {mem_percent}% (Used: {mem_used:.2f} GiB, Free: {mem_free:.2f} GiB, Total: {mem_total:.2f} GiB)')
#     else:
#         print('Failed to fetch cluster stats')

# Melakukan permintaan setiap 500ms
while True:
    try:
        fetch_node_stats()
    except ConnectionError:
        print('Connection error')
    time.sleep(FETCHER_INTERVAL_SEC)