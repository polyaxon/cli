import shutil
import time

from typing import Dict, Optional

import click

from clipped.formatting import Printer

from polyaxon import settings
from polyaxon._deploy.operators.compose import ComposeOperator
from polyaxon._deploy.operators.docker import DockerOperator
from polyaxon._deploy.operators.helm import HelmOperator
from polyaxon._deploy.operators.kubectl import KubectlOperator
from polyaxon._deploy.schemas.deployment import DeploymentConfig
from polyaxon._deploy.schemas.deployment_types import DeploymentCharts, DeploymentTypes
from polyaxon._k8s.namespace import DEFAULT_NAMESPACE
from polyaxon._managers.compose import ComposeConfigManager
from polyaxon.exceptions import PolyaxonException, PolyaxonOperatorException


class DeployConfigManager:
    _SLEEP_TIME = 5

    def __init__(
        self,
        config: DeploymentConfig = None,
        filepath: Optional[str] = None,
        deployment_type: bool = False,
        manager_path: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.config = config
        self.filepath = filepath
        self.type = deployment_type
        self.manager_path = manager_path
        self.dry_run = dry_run
        self.kubectl = KubectlOperator()
        self.helm = HelmOperator()
        self.docker = DockerOperator()
        self.compose = ComposeOperator()

    @property
    def deployment_type(self) -> str:
        if self.type:
            return self.type
        if self.config and self.config.deployment_type:
            return self.config.deployment_type
        return DeploymentTypes.KUBERNETES

    @property
    def deployment_version(self) -> Optional[str]:
        if self.config and self.config.deployment_version:
            return self.config.deployment_version
        return "latest"

    @property
    def deployment_namespace(self) -> str:
        if self.config and self.config.namespace:
            return self.config.namespace
        return DEFAULT_NAMESPACE

    @property
    def k8s_chart(self) -> str:
        deployment_chart = DeploymentCharts.PLATFORM
        if self.config and self.config.deployment_chart:
            deployment_chart = self.config.deployment_chart
        if deployment_chart == DeploymentCharts.PLATFORM:
            return "polyaxon/polyaxon"
        else:
            return "polyaxon/agent"

    @property
    def release_name(self) -> str:
        if self.config and self.config.release_name:
            return self.config.release_name
        deployment_chart = DeploymentCharts.PLATFORM
        if self.config and self.config.deployment_chart:
            deployment_chart = self.config.deployment_chart
        if deployment_chart == DeploymentCharts.PLATFORM:
            return "polyaxon"
        else:
            return "agent"

    @property
    def is_kubernetes(self) -> bool:
        return self.deployment_type in {
            DeploymentTypes.KUBERNETES,
            DeploymentTypes.MINIKUBE,
            DeploymentTypes.MICRO_K8S,
        }

    @property
    def is_docker_compose(self) -> bool:
        return self.deployment_type == DeploymentTypes.DOCKER_COMPOSE

    @property
    def is_docker(self) -> bool:
        return self.deployment_type == DeploymentTypes.DOCKER

    @property
    def is_heroku(self) -> bool:
        return self.deployment_type == DeploymentTypes.HEROKU

    @property
    def is_valid(self) -> bool:
        return self.deployment_type in DeploymentTypes.to_list()

    def check_for_kubernetes(self) -> bool:
        # Deployment on k8s requires helm & kubectl to be installed
        if not self.kubectl.check():
            raise PolyaxonException("kubectl is required to run this command.")
        Printer.success("kubectl is installed")

        if not self.helm.check():
            raise PolyaxonException("helm is required to run this command.")
        Printer.success("helm is installed")

        # Check that polyaxon/polyaxon is set and up-to date
        self.helm.execute(
            args=["repo", "add", "polyaxon", "https://charts.polyaxon.com"]
        )
        self.helm.execute(args=["repo", "update"])
        return True

    def check_for_docker_compose(self) -> bool:
        # Deployment on docker compose requires Docker & Docker Compose to be installed
        if not self.docker.check():
            raise PolyaxonException("Docker is required to run this command.")
        Printer.success("Docker is installed")

        if not self.compose.check():
            raise PolyaxonException("Docker Compose is required to run this command.")
        Printer.success("Docker Compose is installed")

        # Check that .polyaxon/.compose is set and up-to date
        if ComposeConfigManager.is_initialized():
            Printer.success("Docker Compose deployment is initialised.")
        return True

    def check_for_docker(self) -> bool:
        if not self.docker.check():
            raise PolyaxonException("Docker is required to run this command.")
        return True

    def check_for_heroku(self) -> bool:
        return True

    def nvidia_device_plugin(self) -> str:
        return "https://github.com/NVIDIA/k8s-device-plugin/blob/v1.10/nvidia-device-plugin.yml"

    def check(self) -> None:
        """Add platform specific checks"""
        if not self.is_valid:
            raise PolyaxonException(
                "Deployment type `{}` not supported".format(self.deployment_type)
            )
        check = False
        if self.is_kubernetes:
            check = self.check_for_kubernetes()
        elif self.is_docker_compose:
            check = self.check_for_docker_compose()
        elif self.is_docker:
            check = self.check_for_docker()
        elif self.is_heroku:
            check = self.check_for_heroku()
        if not check:
            raise PolyaxonException(
                "Deployment `{}` is not valid".format(self.deployment_type)
            )

    def _get_or_create_namespace(self) -> None:
        stdout = self._check_namespace()
        if stdout:
            return
        # Create a namespace
        try:
            with Printer.console.status(
                f"Creating `{self.deployment_namespace}` namespace ..."
            ):
                stdout = self.kubectl.execute(
                    args=["create", "namespace", self.deployment_namespace],
                    is_json=False,
                    stream=settings.CLIENT_CONFIG.debug,
                )
                click.echo(stdout)
                Printer.success(f"Namespace `{self.deployment_namespace}` is ready")
        except PolyaxonOperatorException:
            return

    def _check_namespace(self) -> Optional[Dict]:
        with Printer.console.status(
            f"Checking `{self.deployment_namespace}` namespace ..."
        ):
            try:
                stdout = self.kubectl.execute(
                    args=["get", "namespace", self.deployment_namespace],
                    is_json=True,
                    stream=settings.CLIENT_CONFIG.debug,
                )
                Printer.success(f"Namespace `{self.deployment_namespace}` is ready")
                return stdout
            except PolyaxonOperatorException:
                return None

    def install_on_kubernetes(self):
        self._get_or_create_namespace()

        args = ["install", self.release_name]
        if self.manager_path:
            args += [self.manager_path]
        else:
            args += [self.k8s_chart]

        args += ["--namespace={}".format(self.deployment_namespace)]
        if self.filepath:
            args += ["-f", self.filepath]
        if self.type in [DeploymentTypes.MICRO_K8S, DeploymentTypes.MINIKUBE]:
            args += [
                "--set",
                "gateway.service.type=NodePort,deploymentType={}".format(self.type),
            ]
        if self.deployment_version:
            Printer.info("Deployment version: `{}`".format(self.deployment_version))
            if self.deployment_version != "latest":
                args += ["--version", self.deployment_version]
        if self.dry_run:
            args += ["--debug", "--dry-run"]

        with Printer.console.status("Running final checks before ..."):
            time.sleep(self._SLEEP_TIME)
        with Printer.console.status("Running install command ..."):
            stdout = self.helm.execute(args=args, stream=settings.CLIENT_CONFIG.debug)
            Printer.success("Install command finished")
        click.echo(stdout)
        Printer.success("Deployment finished.")

    def install_on_docker_compose(self):
        from polyaxon._client.transport import Transport

        path = ComposeConfigManager.get_config_filepath()
        path = "/".join(path.split("/")[:-1])
        # Fetch docker-compose
        Transport().download(
            url="https://github.com/polyaxon/polyaxon-compose/archive/master.tar.gz",
            filename=path + "/file",
            untar=True,
            delete_tar=True,
            extract_path=path,
        )
        # Move necessary info
        shutil.copy(
            path + "/polyaxon-compose-master/docker-compose.yml",
            path + "/docker-compose.yml",
        )
        shutil.copy(
            path + "/polyaxon-compose-master/components.env", path + "/components.env"
        )
        shutil.copy(path + "/polyaxon-compose-master/base.env", path + "/base.env")
        shutil.rmtree(path + "/polyaxon-compose-master/")
        # Generate env from config
        ComposeConfigManager.set_config(self.compose.generate_env(self.config))
        Printer.success("Docker Compose deployment is initialised.")
        if self.dry_run:
            Printer.success("Polyaxon generated deployment env.")
            return
        self.docker.execute(["volume", "create", "--name=polyaxon-postgres"])
        Printer.success("Docker volume created.")
        self.compose.execute(["-f", path + "/docker-compose.yml", "up", "-d"])
        Printer.success("Deployment is running in the background.")
        Printer.success(
            "You can configure your CLI by running: "
            "polyaxon config set --host=localhost."
        )

    def install_on_docker(self):
        pass

    def install_on_heroku(self):
        pass

    def install(self):
        """Install polyaxon using the current config to the correct platform."""
        if not self.is_valid:
            raise PolyaxonException(
                "Deployment type `{}` not supported".format(self.deployment_type)
            )

        if self.is_kubernetes:
            self.install_on_kubernetes()
        elif self.is_docker_compose:
            self.install_on_docker_compose()
        elif self.is_docker:
            self.install_on_docker()
        elif self.is_heroku:
            self.install_on_heroku()

    def upgrade_on_kubernetes(self):
        Printer.print("Running checks for upgrade command ...")
        if self.release_name:
            Printer.info("Deployment release name: `{}`".format(self.release_name))
        if self.deployment_namespace:
            Printer.info("Deployment namespace: `{}`".format(self.deployment_namespace))
        self._check_namespace()
        args = ["upgrade", self.release_name]
        if self.manager_path:
            args += [self.manager_path]
        else:
            args += [self.k8s_chart]
        if self.filepath:
            args += ["-f", self.filepath]
        if self.type and self.type in [
            DeploymentTypes.MICRO_K8S,
            DeploymentTypes.MINIKUBE,
        ]:
            args += [
                "--set",
                "gateway.service.type=NodePort,deploymentType={}".format(self.type),
            ]
        if self.deployment_version:
            Printer.info("Deployment version: `{}`".format(self.deployment_version))
            if self.deployment_version != "latest":
                args += ["--version", self.deployment_version]
        args += ["--namespace={}".format(self.deployment_namespace)]
        if self.dry_run:
            args += ["--debug", "--dry-run"]

        with Printer.console.status("Running final checks ..."):
            time.sleep(self._SLEEP_TIME)
        with Printer.console.status("Running upgrade command ..."):
            stdout = self.helm.execute(args=args, stream=settings.CLIENT_CONFIG.debug)
            Printer.success("Upgrade command finished")
        click.echo(stdout)
        Printer.success("Deployment upgraded.")

    def upgrade_on_docker_compose(self):
        self.install_on_docker_compose()

    def upgrade_on_docker(self):
        pass

    def upgrade_on_heroku(self):
        pass

    def upgrade(self):
        """Upgrade deployment."""
        if not self.is_valid:
            raise PolyaxonException(
                "Deployment type `{}` not supported".format(self.deployment_type)
            )

        if self.is_kubernetes:
            self.upgrade_on_kubernetes()
        elif self.is_docker_compose:
            self.upgrade_on_docker_compose()
        elif self.is_docker:
            self.upgrade_on_docker()
        elif self.is_heroku:
            self.upgrade_on_heroku()

    def teardown_on_kubernetes(self, hooks):
        args = ["delete", self.release_name]
        if not hooks:
            args += ["--no-hooks"]
        args += ["--namespace={}".format(self.deployment_namespace)]
        with Printer.console.status("Running teardown command ..."):
            self.helm.execute(args=args)
        Printer.success("Deployment successfully deleted.")

    def teardown_on_docker_compose(self):
        path = ComposeConfigManager.get_config_filepath()
        path = "/".join(path.split("/")[:-1])
        self.compose.execute(["-f", path + "/docker-compose.yml", "down"])

    def teardown_on_docker(self, hooks):
        pass

    def teardown_on_heroku(self, hooks):
        pass

    def teardown(self, hooks=True):
        """Teardown Polyaxon."""
        if not self.is_valid:
            raise PolyaxonException(
                "Deployment type `{}` not supported".format(self.deployment_type)
            )

        if self.is_kubernetes:
            self.teardown_on_kubernetes(hooks=hooks)
        elif self.is_docker_compose:
            self.teardown_on_docker_compose()
        elif self.is_docker:
            self.teardown_on_docker(hooks=hooks)
        elif self.is_heroku:
            self.teardown_on_heroku(hooks=hooks)
