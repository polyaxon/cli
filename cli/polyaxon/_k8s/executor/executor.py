from polyaxon._k8s.executor.base import BaseExecutor
from polyaxon._k8s.manager.manager import K8sManager


class Executor(BaseExecutor):
    def _get_manager(self):
        return K8sManager(
            k8s_config=self.k8s_config,
            namespace=self.namespace,
            in_cluster=self.in_cluster,
        )
