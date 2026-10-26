# All schemas used by Polyaxon

from polyaxon._vendor.k8s import models


V1Affinity = models.V1Affinity
V1SecurityContext = models.V1SecurityContext
V1PodDNSConfig = models.V1PodDNSConfig
V1Toleration = models.V1Toleration
V1HostAlias = models.V1HostAlias
V1Container = models.V1Container
V1Container.name = ""
V1EnvVar = models.V1EnvVar
V1VolumeMount = models.V1VolumeMount
V1ContainerPort = models.V1ContainerPort
V1ResourceRequirements = models.V1ResourceRequirements
V1EnvFromSource = models.V1EnvFromSource
V1Volume = models.V1Volume
V1ObjectFieldSelector = models.V1ObjectFieldSelector
V1EnvVarSource = models.V1EnvVarSource
V1ConfigMapKeySelector = models.V1ConfigMapKeySelector
V1SecretKeySelector = models.V1SecretKeySelector
V1PodSpec = models.V1PodSpec
V1ObjectMeta = models.V1ObjectMeta
V1PodTemplateSpec = models.V1PodTemplateSpec
V1HostPathVolumeSource = models.V1HostPathVolumeSource
V1EmptyDirVolumeSource = models.V1EmptyDirVolumeSource
V1PersistentVolumeClaimVolumeSource = models.V1PersistentVolumeClaimVolumeSource
V1SecretVolumeSource = models.V1SecretVolumeSource
V1ConfigMapVolumeSource = models.V1ConfigMapVolumeSource
V1LocalObjectReference = models.V1LocalObjectReference
V1PodFailurePolicy = models.V1PodFailurePolicy
V1ExecAction = models.V1ExecAction
V1HTTPGetAction = models.V1HTTPGetAction
V1Probe = models.V1Probe
V1ServiceSpec = models.V1ServiceSpec
V1ServicePort = models.V1ServicePort
