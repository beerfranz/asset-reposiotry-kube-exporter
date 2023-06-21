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

KUBE_LABEL_SELECTOR = os.environ["LABEL_SELECTOR"]
KUBE_ANNOTATION_ASSET_IDENTIFIER = "asset-repository/asset.identifier"
KUBE_ANNOTATION_VERSION = "asset-repository/version"
KUBE_ANNOTATION_CONTAINERS = "asset-repository/container-instances"


def extractContainerInfos(container, baseIdentifier, commonAttributes, annotations):
    info = dict()

    image = container.image
    imageVersion = image.split(':')
    if imageVersion[1]:
        info["version"] = imageVersion[1]
    else:
        info["version"] = image

    info["name"] = container.name
    info["identifier"] = baseIdentifier + "-" + container.name
    info["attributes"] = commonAttributes

    container_asset_identifier = KUBE_ANNOTATION_ASSET_IDENTIFIER + "." + container.name

    # Asset: use annotation container-specific
    if container_asset_identifier in annotations:
        info["asset"] = dict()
        info["asset"]["identifier"] = annotations[container_asset_identifier]
    elif KUBE_ANNOTATION_ASSET_IDENTIFIER in annotations:
        info["asset"] = dict()
        info["asset"]["identifier"] = annotations[KUBE_ANNOTATION_ASSET_IDENTIFIER]

    return info


def kube():
    instances = []

    pods = v1.list_pod_for_all_namespaces(watch=False, label_selector=KUBE_LABEL_SELECTOR)

    for pod in pods.items:
        namespace = pod.metadata.namespace
        nodeName = pod.spec.node_name
        podName = pod.metadata.name
        annotations = pod.metadata.annotations

        commonAttributes = dict()
        commonAttributes["pod"] = podName
        commonAttributes["node"] = nodeName
        commonAttributes["namespace"] = namespace

        baseIdentifier = namespace + "-" + podName

        if not annotations:
            annotations = dict()

        # If containers to check are identified in annotations
        if KUBE_ANNOTATION_CONTAINERS in annotations:
            trackedContainerName = annotations[KUBE_ANNOTATION_CONTAINERS].split(",")
            for container in pod.spec.containers:
                if container.name in trackedContainerName:
                    containerInstance = extractContainerInfos(container, baseIdentifier, commonAttributes, annotations)
                    instances.append(containerInstance)
        else:
            for container in pod.spec.containers:
                containerInstance = extractContainerInfos(container, baseIdentifier, commonAttributes, annotations)
                instances.append(containerInstance)
        
    return instances

while True:
    instances = kube()
    
    warnings.simplefilter('ignore',InsecureRequestWarning)

    headers = {
        'Content-type': 'application/json',
    }
    
    json_data = {
        'instances': instances,
    }

    try:
        response = requests.put(os.environ["ASSET_REPOSITORY_URL"] + "/sources/" + os.environ["SOURCE_IDENTIFIER"] + "/instances", headers=headers, json=json_data, verify=False)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)

    time.sleep(int(os.environ["SLEEP"]))
