# Kubernetes NetworkPolicies

А
Общая информация
Терминология
eBPF
NetworkPolicy + ClusterNetwoorkPolicy
NetworkEditor

B
Общая информация
Терминология
Архитектура
eBPF
Установка 
Конфигурирование
Мониторинг
NetworkPolicy + ClusterNetwoorkPolicy
NetworkEditor



# Общая информация 

Cilium is open source software for transparently securing the network connectivity between application services deployed using Linux container management platforms like Docker and Kubernetes.

At the foundation of Cilium is a new Linux kernel technology called eBPF, which enables the dynamic insertion of powerful security visibility and control logic within Linux itself. Because eBPF runs inside the Linux kernel, Cilium security policies can be applied and updated without any changes to the application code or container configuration.

# Архитектура
Agent

The Cilium agent (`cilium-agent`) runs on each node in the cluster. At a high-level, the agent accepts configuration via Kubernetes or APIs that describes networking, service load-balancing, network policies, and visibility & monitoring requirements.

The Cilium agent listens for events from orchestration systems such as Kubernetes to learn when containers or workloads are started and stopped. It manages the eBPF programs which the Linux kernel uses to control all network access in / out of those containers.

Client (CLI)

The Cilium debug CLI client (`cilium-dbg`) is a command-line tool that is installed along with the Cilium agent. It interacts with the REST API of the Cilium agent running on the same node. The debug CLI allows inspecting the state and status of the local agent. It also provides tooling to directly access the eBPF maps to validate their state.

Operator

The Cilium Operator is responsible for managing duties in the cluster which should logically be handled once for the entire cluster, rather than once for each node in the cluster. The Cilium operator is not in the critical path for any forwarding or network policy decision. A cluster will generally continue to function if the operator is temporarily unavailable. However, depending on the configuration, failure in availability of the operator can lead to:

- Delays in [IP Address Management (IPAM)](https://docs.cilium.io/en/stable/network/concepts/ipam/#address-management) and thus delay in scheduling of new workloads if the operator is required to allocate new IP addresses
    
- Failure to update the kvstore heartbeat key which will lead agents to declare kvstore unhealthiness and restart.
    

CNI Plugin

The CNI plugin (`cilium-cni`) is invoked by Kubernetes when a pod is scheduled or terminated on a node. It interacts with the Cilium API of the node to trigger the necessary datapath configuration to provide networking, load-balancing and network policies for the pod.

# eBPF

eBPF is a Linux kernel bytecode interpreter originally introduced to filter network packets, e.g. tcpdump and socket filters. It has since been extended with additional data structures such as hashtable and arrays as well as additional actions to support packet mangling, forwarding, encapsulation, etc. An in-kernel verifier ensures that eBPF programs are safe to run and a JIT compiler converts the bytecode to CPU architecture specific instructions for native execution efficiency. eBPF programs can be run at various hooking points in the kernel such as for incoming and outgoing packets.

Cilium is capable of probing the Linux kernel for available features and will automatically make use of more recent features as they are detected.

# Terminology
## What is a Label?
A label is a pair of strings consisting of a `key` and `value`. A label can be formatted as a single string with the format `key=value`. The key portion is mandatory and must be unique. This is typically achieved by using the reverse domain name notion, e.g. `io.cilium.mykey=myvalue`. The value portion is optional and can be omitted, e.g. `io.cilium.mykey`.

Key names should typically consist of the character set `[a-z0-9-.]`.

When using labels to select resources, both the key and the value must match, e.g. when a policy should be applied to all endpoints with the label `my.corp.foo` then the label `my.corp.foo=bar` will not match the selector.

### Label Source

A label can be derived from various sources. For example, an [endpoint](https://docs.cilium.io/en/stable/gettingstarted/terminology/#endpoint) will derive the labels associated to the container by the local container runtime as well as the labels associated with the pod as provided by Kubernetes. As these two label namespaces are not aware of each other, this may result in conflicting label keys.

To resolve this potential conflict, Cilium prefixes all label keys with `source:` to indicate the source of the label when importing labels, e.g. `k8s:role=frontend`, `container:user=joe`, `k8s:role=backend`. This means that when you run a Docker container using `docker run [...] -l foo=bar`, the label `container:foo=bar` will appear on the Cilium endpoint representing the container. Similarly, a Kubernetes pod started with the label `foo: bar` will be represented with a Cilium endpoint associated with the label `k8s:foo=bar`. A unique name is allocated for each potential source. The following label sources are currently supported:

- `container:` for labels derived from the local container runtime
    
- `k8s:` for labels derived from Kubernetes
    
- `reserved:` for special reserved labels, see [Special Identities](https://docs.cilium.io/en/stable/gettingstarted/terminology/#reserved-labels).
    
- `unspec:` for labels with unspecified source
    

When using labels to identify other resources, the source can be included to limit matching of labels to a particular type. If no source is provided, the label source defaults to `any:` which will match all labels regardless of their source. If a source is provided, the source of the selecting and matching labels need to match.

## Endpoint

Cilium makes application containers available on the network by assigning them IP addresses. Multiple application containers can share the same IP address; a typical example for this model is a Kubernetes [Pod](https://docs.cilium.io/en/stable/glossary/#term-Pod). All application containers which share a common address are grouped together in what Cilium refers to as an endpoint.

Allocating individual IP addresses enables the use of the entire Layer 4 port range by each endpoint. This essentially allows multiple application containers running on the same cluster node to all bind to well known ports such as `80` without causing any conflicts.

The default behavior of Cilium is to assign both an IPv6 and IPv4 address to every endpoint. However, this behavior can be configured to only allocate an IPv6 address with the `--enable-ipv4=false` option. If both an IPv6 and IPv4 address are assigned, either address can be used to reach the endpoint. The same behavior will apply with regard to policy rules, load-balancing, etc. See [IP Address Management (IPAM)](https://docs.cilium.io/en/stable/network/concepts/ipam/#address-management) for more details.

## Identity

All [Endpoint](https://docs.cilium.io/en/stable/gettingstarted/terminology/#endpoints) are assigned an identity. The identity is what is used to enforce basic connectivity between endpoints. In traditional networking terminology, this would be equivalent to Layer 3 enforcement.

An identity is identified by [Labels](https://docs.cilium.io/en/stable/gettingstarted/terminology/#labels) and is given a cluster wide unique identifier. The endpoint is assigned the identity which matches the endpoint’s [Security Relevant Labels](https://docs.cilium.io/en/stable/gettingstarted/terminology/#security-relevant-labels), i.e. all endpoints which share the same set of [Security Relevant Labels](https://docs.cilium.io/en/stable/gettingstarted/terminology/#security-relevant-labels) will share the same identity. This concept allows to scale policy enforcement to a massive number of endpoints as many individual endpoints will typically share the same set of security [Labels](https://docs.cilium.io/en/stable/gettingstarted/terminology/#labels) as applications are scaled.

### What is an Identity?

The identity of an endpoint is derived based on the [Labels](https://docs.cilium.io/en/stable/gettingstarted/terminology/#labels) associated with the pod or container which are derived to the [endpoint](https://docs.cilium.io/en/stable/gettingstarted/terminology/#endpoint). When a pod or container is started, Cilium will create an [endpoint](https://docs.cilium.io/en/stable/gettingstarted/terminology/#endpoint) based on the event received by the container runtime to represent the pod or container on the network. As a next step, Cilium will resolve the identity of the [endpoint](https://docs.cilium.io/en/stable/gettingstarted/terminology/#endpoint) created. Whenever the [Labels](https://docs.cilium.io/en/stable/gettingstarted/terminology/#labels) of the pod or container change, the identity is reconfirmed and automatically modified as required.

# Конфигурирование


# Configuration

Your Cilium installation is configured by one or more Helm values - see [Helm Reference](https://docs.cilium.io/en/stable/helm-reference/#helm-reference). These helm values are converted to arguments for the individual components of a Cilium installation, such as [cilium-agent](https://docs.cilium.io/en/stable/cmdref/cilium-agent/) and [cilium-operator](https://docs.cilium.io/en/stable/cmdref/cilium-operator/), and stored in a ConfigMap.

## `cilium-config` ConfigMap

These arguments are stored in a shared ConfigMap called `cilium-config` (albeit without the leading `--`). For example, a typical installation may look like

```bash
$ kubectl -n kube-system get configmap cilium-config -o yaml
data:
  agent-not-ready-taint-key: node.cilium.io/agent-not-ready
  arping-refresh-period: 30s
  auto-direct-node-routes: "false"
  (output continues)
```

## Making Changes

You may change the configuration of a running installation in three ways:

1. Via `helm upgrade`
    
    Do so by providing new values to Helm and applying them to the existing installation. By setting the value `rollOutCiliumPods=true`, the agent pods will be gradually restarted.
    
2. Via `cilium config set`
    
    The [Cilium CLI](https://github.com/cilium/cilium-cli/) has the ability to update individual values in the `cilium-config` ConfigMap. By default Cilium Agent pods are restarted when configuration is changed. To gradually restart do `cilium config set --restart=false ...` and manually delete agent pods to pick up the changes.
    
3. Via `CiliumNodeConfig` objects
    
    Cilium also supports configuration on sets of nodes. See the [Per-node configuration](https://docs.cilium.io/en/stable/configuration/per-node-config/#per-node-configuration) page for more details. This requires that pods be manually deleted for changes to take effect.

# Мониторинг


# NetworkPolicy

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-prometheus
  namespace: monitoring
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: prometheus
  ingress:
  - fromEndpoints:
    - matchLabels:
        app.kubernetes.io/instance: ingress-nginx
        io.kubernetes.pod.namespace: ingress-nginx
  egress:
    - toEntities:
      - host
      - remote-node
      - kube-apiserver
    - toEndpoints:
      - matchLabels:
          app.kubernetes.io/instance: ingress-nginx
          io.kubernetes.pod.namespace: ingress-nginx
    - toEndpoints:
      - matchLabels:
          app.kubernetes.io/name: kube-state-metrics
      toPorts:
        - ports:
          - port: "8080"
            protocol: TCP
    - toEndpoints:
      - matchLabels:
          io.kubernetes.pod.namespace: kube-system
          k8s-app: kube-dns
      toPorts:
        - ports:
          - port: "9153"
            protocol: TCP
    - toEndpoints:
      - matchLabels:
          component: kube-scheduler
          io.kubernetes.pod.namespace: kube-system
      toPorts:
        - ports:
          - port: "10259"
            protocol: TCP
          rules:
            http:
            - method: GET
              path: "/metrics"
    - toEndpoints:
      - matchLabels:
          k8s-app: kube-proxy
          io.kubernetes.pod.namespace: kube-system
      toPorts:
        - ports:
          - port: "10249"
            protocol: TCP
          rules:
            http:
            - method: GET
              path: "/metrics"
    - toEndpoints:
      - matchLabels:
          component: etcd
          io.kubernetes.pod.namespace: kube-system
      toPorts:
        - ports:
          - port: "2381"
            protocol: TCP
          rules:
            http:
            - method: GET
              path: "/metrics"
    - toEndpoints:
      - matchLabels:
          component: kube-controller-manager
          io.kubernetes.pod.namespace: kube-system
      toPorts:
        - ports:
          - port: "10257"
            protocol: TCP
          rules:
            http:
            - method: GET
              path: "/metrics"
    - toEndpoints:
      - matchLabels:
          app.kubernetes.io/name: kube-prometheus-stack-prometheus-operator
      toPorts:
        - ports:
          - port: "10250"
            protocol: TCP
          rule:
            http:
            - method: GET
              path: "/metrics"
```
# NetworkPolicy editor

https://editor.networkpolicy.io/



# Ссылки

https://docs.cilium.io/en/stable/gettingstarted/terminology/

https://isovalent.com/books/ebpf/
