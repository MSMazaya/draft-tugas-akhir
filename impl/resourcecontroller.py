from kubernetes import client, config
import time
from utils import printd
import json, os
from configuration import KUBERNETES_NAMESPACE, KUBERNETES_DEPLOYMENT_NAME, RESOURCE_CHANGE_COOLDOWN, RSRC_CTRL_DATA_PATH, CPU_LIMIT_IN_MILLI, MEM_LIMIT_IN_MIB

class ResourceController:
    
    def __init__(self):
        config.load_kube_config()
        self.api = client.CoreV1Api()
        self.apps = client.AppsV1Api()

        self.pod = self.api.read_namespaced_pod(name=self.auto_get_podname_from_deployment(), namespace=KUBERNETES_NAMESPACE)
        assert len(self.pod.spec.containers) > 0
        self.container = self.pod.spec.containers[0]
        self.next_change = 0
        self.queue = []
        self.last_cpu = 1000
        self.last_mem = 4096
        self.load()

    def load(self):
        if os.path.exists(RSRC_CTRL_DATA_PATH):
            with open(RSRC_CTRL_DATA_PATH, 'r') as file:
                loaded = dict(json.load(file))
            if 'mem' in loaded.keys():
                self.last_mem = int(loaded['mem'])
            if 'cpu' in loaded.keys():
                self.last_cpu = int(loaded['cpu'])
            if 'queue' in loaded.keys():
                self.queue = loaded['queue']
            if 'next' in loaded.keys():
                self.next_change = loaded['next']
    
    def save(self):
        with open(RSRC_CTRL_DATA_PATH, 'w') as file:
            savedata = {
                'mem': self.last_mem,
                'cpu': self.last_cpu,
                'next': self.next_change,
                'queue': self.queue
            }
            json.dump(savedata, file, indent=4)
    
    def change_resource(self, cpu, memory):
        if (cpu == None and memory == None):
            return
        
        if (cpu == None):
            cpu = self.last_cpu
        else:
            cpu = self.last_cpu + cpu

        if (memory == None):
            memory = self.last_mem
        else:
            memory = self.last_mem + memory

        assert type(cpu) is int and cpu > 0
        assert type(memory) is int and memory > 0
        cpu = max(cpu, CPU_LIMIT_IN_MILLI[0])
        memory = max(memory, MEM_LIMIT_IN_MIB[0])
        cpu = min(cpu, CPU_LIMIT_IN_MILLI[1])
        memory = min(memory, MEM_LIMIT_IN_MIB[1])
        if (cpu == self.last_cpu and memory == self.last_mem):
            return
        
        self.queue.append({'cpu': cpu, 'mem': memory})
        self.save()
        #printd(f"Resource change request queued: {self.queue}")
    
    def tick(self):
        if len(self.queue) > 0 and time.time() > self.next_change:
            current = self.queue.pop(0)
            printd(f"Applying resource change: {current}")
            self.next_change = time.time() + RESOURCE_CHANGE_COOLDOWN
            self.save()
            self.__instant_change_resource(current['cpu'], current['mem'])
            return True
        return False

    def __instant_change_resource(self, cpu, memory):
        assert type(cpu) is int and cpu > 0
        assert type(memory) is int and memory > 0
        self.last_cpu = cpu
        self.last_mem = memory
        self.save()

        self.deployment = self.apps.read_namespaced_deployment(name=KUBERNETES_DEPLOYMENT_NAME, namespace=KUBERNETES_NAMESPACE)
        self.deployment.spec.template.spec.containers[0].resources.requests["cpu"] = f"{cpu}m"
        self.deployment.spec.template.spec.containers[0].resources.requests["memory"] = f"{memory}Mi"
        self.deployment.spec.template.spec.containers[0].resources.limits["cpu"] = f"{cpu}m"
        self.deployment.spec.template.spec.containers[0].resources.limits["memory"] = f"{memory}Mi"
        self.apps.replace_namespaced_deployment(name=KUBERNETES_DEPLOYMENT_NAME, namespace=KUBERNETES_NAMESPACE, body=self.deployment)

    def auto_get_podname_from_deployment(self):
        listPods = self.api.list_namespaced_pod(KUBERNETES_NAMESPACE, label_selector="app=elasticsearch")
        if len(listPods.items) < 1:
            print("Pod with label selector 'app=elasticsearch' not found.")
            exit(0)
        podname = list(listPods.items)[0].metadata.name
        return podname
    
    def __str__(self):
        return f"ResourceController(cpu={self.last_cpu}, mem={self.last_mem}, queue={self.queue}, next_change={self.next_change})"


# rc = ResourceController()
# print(str(rc))
# rc.tick()
# rc.change_resource(800,4000)
# rc.change_resource(1000,5000)
# rc.change_resource(1500,3000)
# while True:
#     rc.tick()
#     time.sleep(1)