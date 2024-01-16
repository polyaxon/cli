from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field, StrictStr, validator

from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon._schemas.base import BaseSchemaModel


class V1Environment(BaseSchemaModel):
    """The environment section allows to alter the
    configuration of the runtime of your jobs, experiments, and services.

    Based on this section you can define several information
    that will be injected into the pod running on Kubernetes, e.g. the node selector.

    Args:
        labels: Dict, optional
        annotations: Dict, optional
        node_selector: Dict, optional
        affinity: V1Affinity, optional
        tolerations: List[V1Toleration], optional
        node_name: str, optional
        service_account_name: str, optional
        host_aliases: V1HostAlias, optional
        security_context: V1SecurityContext, optional
        image_pull_secrets: List[str], optional
        host_network: bool, optional
        host_pid: bool, optional
        dns_policy: str, optional
        dns_config: V1PodDNSConfig, optional
        scheduler_name: str, optional
        priority_class_name: str, optional
        priority: int, optional
        restart_policy: str, optional

    ## YAML usage

    ```yaml
    >>> environment:
    >>>   labels:
    >>>   annotations:
    >>>   nodeSelector:
    >>>   affinity:
    >>>   tolerations:
    >>>   nodeName:
    >>>   serviceAccountName:
    >>>   hostAliases:
    >>>   securityContext:
    >>>   imagePullSecrets:
    >>>   hostNetwork:
    >>>   hostPID:
    >>>   dnsPolicy:
    >>>   dnsConfig:
    >>>   schedulerName:
    >>>   priorityClassName:
    >>>   priority:
    >>>   restartPolicy:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Environment
    >>> from polyaxon import k8s
    >>> environment = V1Environment(
    >>>     labels={
    >>>         "key1" : "value1",
    >>>         "key2" : "value2"
    >>>     },
    >>>     annotations={
    >>>         "key1" : "value1",
    >>>         "key2" : "value2"
    >>>     },
    >>>     node_selector={
    >>>         "node_label": "node_value"
    >>>     },
    >>>     affinity=k8s_schemas.V1Affinity(...),
    >>>     tolerations=k8s_schemas.V1Affinity(...),
    >>>     node_name="name",
    >>>     service_account_name="name",
    >>>     host_aliases=k8s_schemas.V1HostAlias(...),
    >>>     security_context=k8s_schemas.V1SecurityContext(...),
    >>>     image_pull_secrets=["secret1", "secret2", ...],
    >>>     host_network=False,
    >>>     host_pid=False,
    >>>     dns_policy="Default",
    >>>     dns_config=k8s_schemas.V1PodDNSConfig(...),
    >>>     scheduler_name="name",
    >>>     priority_class_name="name",
    >>>     priority=0,
    >>>     restart_policy="Never",
    >>> )
    ```

    ## Fields

    ### labels

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)  # noqa

    > Labels are key/value pairs that are attached to objects, such as pods.
    > Labels are intended to be used to specify identifying attributes of objects that
    > are meaningful and relevant to users, but do not directly imply semantics to the core system.

    Polyaxon injects several labels to all operations it manages,
    users can leverage those labels or extend them.

    ```yaml
    >>> environment:
    >>>   labels:
    >>>     key1: "label1"
    >>>     key2: "label2"
    ```

    ### annotations

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations/)  # noqa

    > You can use Kubernetes annotations to attach arbitrary non-identifying metadata to objects.
    > Clients such as tools and libraries can retrieve this metadata.

    ```yaml
    >>> environment:
    >>>   annotations:
    >>>     key1: "value1"
    >>>     key2: "value2"
    ```

    ### nodeSelector

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector)  # noqa

    > nodeSelector is the simplest recommended form of node selection constraint.
    > nodeSelector is a field of PodSpec. It specifies a map of key-value pairs.
    > For the pod to be eligible to run on a node, the node must have each of
    > the indicated key-value pairs as labels (it can have additional labels as well).
    > The most common usage is one key-value pair.

    ```yaml
    >>> environment:
    >>>   nodeSelector:
    >>>     node_label: node_value
    ```

    ### affinity

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)  # noqa

    > The affinity/anti-affinity feature, greatly expands the types of constraints you can express.

    The affinity to use for scheduling the job.

    ```yaml
    >>> environment:
    >>>   affinity:
    >>>     podAffinity:
    >>>       preferredDuringSchedulingIgnoredDuringExecution:
    >>>         ...
    ```


    ### tolerations

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)  # noqa

    > Tolerations are applied to pods, and allow (but do not require)
    > the pods to schedule onto nodes with matching taints.

    ```yaml
    >>> environment:
    >>>   tolerations:
    >>>     - key: "key"
    >>>       operator: "Exists"
    >>>       effect: "NoSchedule"
    ```

    ### nodeName

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodename)  # noqa

    > nodeName is the simplest form of node selection constraint,
    > but due to its limitations it is typically not used. nodeName is a field of PodSpec.
    > If it is non-empty, the scheduler ignores the pod and the kubelet running on the named
    > node tries to run the pod. Thus, if nodeName is provided in the PodSpec,
    > it takes precedence over the above methods for node selection.

    ```yaml
    >>> environment:
    >>>   nodeName: kube-01
    ```

    ### serviceAccountName

    From [Kubernetes docs](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)  # noqa

    > A service account provides an identity for processes that run in a Pod.

    ```yaml
    >>> environment:
    >>>   serviceAccountName: build-robot
    ```

    In order for the custom service account to function correctly
    with Polyaxon sidecars/initializers, we recommend to include these rules in your custom service accounts:

    ```yaml
    >>> rules:
    >>>   - apiGroups: [""]
    >>>     resources: ["pods", "services", "events", "pods/status", "pods/log"]
    >>>     verbs: ["get", "watch", "list"]
    >>>   - apiGroups: ["metrics.k8s.io"]
    >>>     resources: ["pods", "nodes"]
    >>>     verbs: ["get", "list", "watch"]
    >>>   - apiGroups: ["core.polyaxon.com"]
    >>>     resources: ["operations"]
    >>>     verbs: ["get", "watch", "list"]
    ```

    ### hostAliases

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/services-networking/add-entries-to-pod-etc-hosts-with-host-aliases/)  # noqa

    > Adding entries to a Pod’s /etc/hosts file provides Pod-level override of hostname resolution
    > when DNS and other options are not applicable. In 1.7,
    > users can add these custom entries with the HostAliases field in PodSpec.

    ```yaml
    >>> environment:
    >>>   hostAliases:
    >>>   - ip: "127.0.0.1"
    >>>     hostnames:
    >>>     - "foo.local"
    >>>     - "bar.local"
    ```


    ### securityContext

    From [Kubernetes docs](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)  # noqa

    > A security context defines privilege and access control settings for a Pod or Container.

    ```yaml
    >>> environment:
    >>>   securityContext:
    >>>     runAsUser: 1000
    >>>     runAsGroup: 3000
    >>>     runAsNonRoot: true
    ```

    ### imagePullSecrets

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/containers/images/#specifying-imagepullsecrets-on-a-pod)  # noqa

    > ImagePullSecrets is a list of references to secrets in the same namespace
    > to use for pulling any images in pods that reference this ServiceAccount.
    > ImagePullSecrets are distinct from Secrets because Secrets can be mounted in the pod,
    > but ImagePullSecrets are only accessed by the kubelet.

    ```yaml
    >>> environment:
    >>>   imagePullSecrets: ['secret1', 'secret2']
    ```

    ### hostNetwork

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/policy/pod-security-policy/#host-namespaces)  # noqa

    > Controls whether the pod may use the node network namespace.
    > Gives the pod access to the loopback device, services listening on localhost,
    > and could be used to snoop on network activity of other pods on the same node.

    ```yaml
    >>> environment:
    >>>   hostNetwork: false
    ```

    ### hostPID

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/policy/pod-security-policy/#host-namespaces)  # noqa

    > Controls whether the pod containers can share the host process ID namespace.
    > Note that when paired with ptrace this can be used to escalate privileges outside
    > of the container (ptrace is forbidden by default).

    ```yaml
    >>> environment:
    >>>   hostPID: false
    ```

    ### dnsPolicy

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pods-dns-policy)  # noqa

    > Set DNS policy for the pod.
    > Defaults to "ClusterFirst".
    > Valid values are 'ClusterFirstWithHostNet', 'ClusterFirst', 'Default' or 'None'.
    > DNS parameters given in DNSConfig will be merged with the policy selected with DNSPolicy.
    > To have DNS options set along with hostNetwork, you have to specify DNS policy
    > explicitly to 'ClusterFirstWithHostNet'.

    ```yaml
    >>> environment:
    >>>   dnsPolicy: ClusterFirst
    ```

    ### dnsConfig

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pods-dns-config)  # noqa

    > Pod’s DNS Config allows users more control on the DNS settings for a Pod.

    ```yaml
    >>> environment:
    >>>   dnsConfig:
    >>>     nameservers:
    >>>       - 1.2.3.4
    >>>     searches:
    >>>       - ns1.svc.cluster-domain.example
    >>>       - my.dns.search.suffix
    >>>     options:
    >>>       - name: ndots
    >>>         value: "2"
    >>>       - name: edns0
    ```

    ### schedulerName

    From [Kubernetes docs](https://kubernetes.io/docs/tasks/administer-cluster/configure-multiple-schedulers/)  # noqa

    > If specified, the pod will be dispatched by the specified scheduler.
    > Or it will be dispatched by workflow scope scheduler if specified.
    > If neither specified, the pod will be dispatched by default scheduler.

    ```yaml
    >>> environment:
    >>>   schedulerName: default-scheduler
    ```

    ### priorityClassName

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/configuration/pod-priority-preemption/)  # noqa

    > Pods can have priority.
    > Priority indicates the importance of a Pod relative to other Pods.
    > If a Pod cannot be scheduled, the scheduler tries to preempt (evict)
    > lower priority Pods to make scheduling of the pending Pod possible.

    ```yaml
    >>> environment:
    >>>   priorityClassName: high
    ```

    ### priority

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/configuration/pod-priority-preemption/)  # noqa

    > Pods can have priority.
    > Priority indicates the importance of a Pod relative to other Pods.
    > If a Pod cannot be scheduled, the scheduler tries to preempt (evict)
    > lower priority Pods to make scheduling of the pending Pod possible.

    ```yaml
    >>> environment:
    >>>   priority: 10
    ```

    ### restartPolicy

    From [Kubernetes docs](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#restart-policy)  # noqa

    > A PodSpec has a restartPolicy field with possible values Always, OnFailure, and Never.
    > The default value is Always.


    ```yaml
    >>> environment:
    >>>   restartPolicy: Never
    ```
    """

    _IDENTIFIER = "environment"
    _SWAGGER_FIELDS = [
        "affinity",
        "tolerations",
        "securityContext",
        "hostAliases",
        "dnsConfig",
    ]

    labels: Optional[Dict[StrictStr, StrictStr]]
    annotations: Optional[Dict[StrictStr, StrictStr]]
    node_selector: Optional[Dict[StrictStr, StrictStr]] = Field(alias="nodeSelector")
    affinity: Optional[Union[k8s_schemas.V1Affinity, Dict]]
    tolerations: Optional[List[Union[k8s_schemas.V1Toleration, Dict]]]
    node_name: Optional[StrictStr] = Field(alias="nodeName")
    service_account_name: Optional[StrictStr] = Field(alias="serviceAccountName")
    host_aliases: Optional[List[k8s_schemas.V1HostAlias]] = Field(alias="hostAliases")
    security_context: Optional[Union[k8s_schemas.V1SecurityContext, Dict]] = Field(
        alias="securityContext"
    )
    image_pull_secrets: Optional[List[StrictStr]] = Field(alias="imagePullSecrets")
    host_network: Optional[bool] = Field(alias="hostNetwork")
    host_pid: Optional[bool] = Field(alias="hostPID")
    dns_policy: Optional[StrictStr] = Field(alias="dnsPolicy")
    dns_config: Optional[k8s_schemas.V1PodDNSConfig] = Field(alias="dnsConfig")
    scheduler_name: Optional[StrictStr] = Field(alias="schedulerName")
    priority_class_name: Optional[StrictStr] = Field(alias="priorityClassName")
    priority: Optional[int]
    restart_policy: Optional[Literal["Always", "OnFailure", "Never"]] = Field(
        alias="restartPolicy"
    )

    @validator("affinity", always=True, pre=True)
    def validate_affinity(cls, v):
        return k8s_validation.validate_k8s_affinity(v)

    @validator("tolerations", always=True, pre=True)
    def validate_tolerations(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_toleration(vi) for vi in v]

    @validator("host_aliases", always=True, pre=True)
    def validate_host_aliases(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_host_alias(vi) for vi in v]

    @validator("security_context", always=True, pre=True)
    def validate_security_context(cls, v):
        if not v:
            return v
        return k8s_validation.validate_k8s_security_context(v)

    @validator("dns_config", always=True, pre=True)
    def validate_dns_config(cls, v):
        if not v:
            return v
        return k8s_validation.validate_k8s_pod_dns_config(v)
