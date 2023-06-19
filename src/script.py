import time
import logging
from kubernetes import client, config
from pprint import pprint
import yaml
import os
import requests, json
import warnings
import urllib3, urllib 
from urllib3.exceptions import InsecureRequestWarning

config.load_incluster_config()

v1 = client.CoreV1Api()

def kube():
    instances = []
    pods = v1.list_pod_for_all_namespaces(watch=False, label_selector=os.environ["LABEL_SELECTOR"])
    for pod in pods.items:
        namespace = pod.metadata.namespace
        nodeName = pod.spec.node_name
        podName = pod.metadata.name
        annotations = pod.metadata.annotations

        if "asset-repository/version" in annotations:
            instance = dict()
            instance["identifier"] = namespace + "-" + podName
            instance["version"] = annotations["asset-repository/version"]
            instance["attributes"] = dict()
            instance["attributes"]["namespace"] = namespace
            instance["attributes"]["pod"] = podName
            instance["attributes"]["node"] = nodeName

            if "asset-repository/asset.identifier" in annotations:
                instance["asset"] = dict()
                instance["asset"]["identifier"] = annotations["asset-repository/asset.identifier"]

            instances.append(instance)
        
        if "asset-repository/container-instances" in annotations:
            trackedContainerName = annotations["asset-repository/container-instances"].split(",")
            for container in pod.spec.containers:
                if container.name in trackedContainerName:
                    containerInstance = dict()
                    image = container.image
                    containerName = container.name
                    
                    containerInstance["identifier"] = namespace + "-" + podName + "-" + containerName

                    imageVersion = image.split(':')
                    if imageVersion[1]:
                        version = imageVersion[1]
                    else:
                        version = image

                    containerInstance["version"] = version
                    containerInstance["attributes"] = dict()
                    containerInstance["attributes"]["namespace"] = namespace
                    containerInstance["attributes"]["pod"] = podName
                    containerInstance["attributes"]["node"] = nodeName

                    if "asset-repository/asset.identifier" in annotations:
                        containerInstance["asset"] = dict()
                        containerInstance["asset"]["identifier"] = annotations["asset-repository/asset.identifier"]

                    instances.append(containerInstance)
    return instances

while True:
    instances = kube()
    pprint(kube())
    time.sleep(2)

    warnings.simplefilter('ignore',InsecureRequestWarning)

    headers = {
        'Content-type': 'application/json',
    }
    
    json_data = {
        'instances': instances,
    }

    response = requests.put(os.environ["ASSET_REPOSITORY_URL"] + "/sources/" + os.environ["SOURCE_IDENTIFIER"] + "/instances", headers=headers, json=json_data, verify=False)
    print(response.text)
