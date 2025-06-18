from typing import Set, Optional, Dict, List
from pydantic import BaseModel, Field
from dataclasses import dataclass
from kubernetes import client, config
import requests
from urllib.parse import urlparse
import argparse
import pprint


class ImageReference(BaseModel):
    name: str
    registry: str
    pod_name: str
    namespace: str
    tag: Optional[str] = None
    digest: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        return f"{self.registry}/{self.name}" 

def get_pod_images(
    kubernetes_client: client.CoreV1Api, 
    namespace=None
) -> list[ImageReference]:
    """
    Получает информацию об образах из Kubernetes
    """
    if namespace:
        pods = kubernetes_client.list_namespaced_pod(namespace).items
    else:
        pods = kubernetes_client.list_pod_for_all_namespaces().items
    
    images = []
    
    for pod in pods:
        for container in pod.spec.containers:
            images.append(
                parse_image(container.image, container.name, pod.metadata.namespace)
            )
    return images


def parse_image(
    image: str, 
    pod_name: str, 
    namespace: str
) -> ImageReference:
    parsed = urlparse(f"docker://{image}")
    image_path = parsed.path.lstrip('/')
    registry = parsed.netloc
    if '/' not in image_path:
        image_path = f"{parsed.netloc}/{image_path}"
        registry = 'registry-1.io'
    tag = None
    digest = None
    if '@' in image_path:
        splited = image_path.split('@')
        if ':' in splited[0]:
            tag = splited[0].split(':')[1]
            image_path = splited[0].split(':')[0]
        elif ':' not in splited[0]:
            digest = splited[1]
            image_path = splited[0]
        else:
            raise ValueError(image_path)
    elif ':' in image_path:
        splited = image_path.split(':')
        tag = splited[1]
        image_path = splited[0]
    else:
        return ImageReference(
            name=image_path,
            pod_name=pod_name,
            namespace=namespace,
            registry=registry,
            tag=tag,
            digest=digest
        )
    return ImageReference(
        name=image_path,
        pod_name=pod_name,
        namespace=namespace,
        registry=registry,
        tag=tag,
        digest=digest
    )

def request_sha256(image_name:str, registry: str, token: str = None) -> str:
    pass 


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get current image versions of Kubernetes pods')
    parser.add_argument('--namespace', '-n', help='Namespace to check (default: all namespaces)')
    args = parser.parse_args()

    try:
        config.load_kube_config()
    except:
        config.load_incluster_config()
    
    v1 = client.CoreV1Api()
    

    image = 'quay.io/keycloak/keycloak-operator:26.2'
    image_sha = "quay.io/keycloak/keycloak-operator:26.2@sha265:12131sa"
    image_dig = 'quay.io/keycloak/keycloak-operator@sha265:11121sa'
    # print(parse_image(image, 'pod'))
    # print(parse_image(image_sha, 'pod'))
    # print(parse_image(image_dig, 'pod'))
    
    
    images = get_pod_images(
        v1
    )
    
    pprint.pprint(images)
    
    # images = get_pod_images(args.namespace)
    # print_images_table(images)
    # get_digets_from_tag('quay.io', '
