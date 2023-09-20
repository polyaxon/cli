import logging
import time

from typing import Dict, List, Optional, Union

import orjson

from clipped.utils.json import orjson_loads
from clipped.utils.logging import LogLevels
from docker import APIClient
from docker.errors import APIError, BuildError
from urllib3.exceptions import ReadTimeoutError

from polyaxon._schemas.types import Uri
from polyaxon.exceptions import PolyaxonBuildException, PolyaxonSchemaError

_logger = logging.getLogger("polyaxon.dockerizer")


class DockerMixin:
    IS_BUILD: Optional[bool] = None

    def _prepare_log_lines(self, log_line):  # pylint:disable=too-many-branches
        raw = log_line.decode("utf-8").strip()
        raw_lines = raw.split("\n")
        log_lines = []
        status = True
        for raw_line in raw_lines:
            try:
                json_line = orjson_loads(raw_line)

                if json_line.get("error"):
                    log_lines.append(
                        "{}: {}".format(
                            LogLevels.ERROR, str(json_line.get("error", json_line))
                        )
                    )
                    status = False
                else:
                    if json_line.get("stream"):
                        log_lines.append(
                            "Building: {}".format(json_line["stream"].strip())
                        )
                    elif json_line.get("status"):
                        if not self.is_pushing and not self.IS_BUILD:
                            self.is_pushing = True
                            log_lines.append("Pushing ...")
                    elif json_line.get("aux"):
                        log_lines.append(
                            "Pushing finished: {}".format(json_line.get("aux"))
                        )
                    else:
                        log_lines.append(str(json_line))
            except orjson.JSONDecodeError:
                log_lines.append("JSON decode error: {}".format(raw_line))
        return log_lines, status

    def _handle_logs(self, log_lines):
        for log_line in log_lines:
            print(log_line)  # pylint:disable=superfluous-parens

    def _handle_log_stream(self, stream):
        log_lines = []
        status = True
        try:
            for log_line in stream:
                new_log_lines, new_status = self._prepare_log_lines(log_line)
                log_lines += new_log_lines
                if not new_status:
                    status = new_status
                self._handle_logs(log_lines)
                log_lines = []
            if log_lines:
                self._handle_logs(log_lines)
        except (BuildError, APIError) as e:
            self._handle_logs(
                [
                    "{}: Could not build the image, encountered {}".format(
                        LogLevels.ERROR, e
                    )
                ]
            )
            return False

        return status


class DockerBuilder(DockerMixin):
    IS_BUILD = True

    def __init__(
        self,
        context: str,
        destination: str,
        credstore_env: Optional[Dict] = None,
        registries: Optional[List[Union[Uri, str]]] = None,
        docker: Optional[APIClient] = None,
    ):
        from polyaxon._config.parser import ConfigParser

        get_uri = ConfigParser.parse(Uri)
        self.destination = destination

        self.context = context
        self.registries = []
        for r in registries or []:
            try:
                self.registries.append(get_uri(value=r, key="DockerBuilder"))
            except PolyaxonSchemaError:
                raise PolyaxonBuildException(
                    "Registry `{}` is not valid Uri.".format(r)
                )
        self.docker = docker or APIClient(version="auto", credstore_env=credstore_env)
        self.is_pushing = False

    def check_image(self):
        return self.docker.images(self.destination)

    def login_private_registries(self):
        if not self.registries:
            return
        for registry in self.registries:
            self.docker.login(
                username=registry.user,
                password=registry.password,
                registry=registry.host_port,
                reauth=True,
            )

    def build(self, nocache: bool = False, memory_limit: Optional[int] = None):
        limits = {
            # Disable memory swap for building
            "memswap": -1
        }
        if memory_limit:
            limits["memory"] = memory_limit

        stream = self.docker.build(
            path=self.context,
            tag=self.destination,
            forcerm=True,
            rm=True,
            pull=True,
            nocache=nocache,
            container_limits=limits,
        )
        return self._handle_log_stream(stream=stream)


class DockerPusher(DockerMixin):
    IS_BUILD = False

    def __init__(
        self,
        destination: str,
        credstore_env: Optional[Dict] = None,
        docker: Optional[APIClient] = None,
    ):
        self.destination = destination
        self.docker = docker or APIClient(version="auto", credstore_env=credstore_env)
        self.is_pushing = False

    def push(self):
        stream = self.docker.push(self.destination, stream=True)
        return self._handle_log_stream(stream=stream)


def _build(
    context: str,
    destination: str,
    nocache: bool,
    docker: Optional[APIClient] = None,
    credstore_env: Optional[Dict] = None,
    registries: Optional[List[Union[Uri, str]]] = None,
):
    """Build necessary code for a job to run"""
    _logger.info("Starting build ...")

    # Build the image
    docker_builder = DockerBuilder(
        context=context,
        destination=destination,
        credstore_env=credstore_env,
        registries=registries,
        docker=docker,
    )
    docker_builder.login_private_registries()
    if docker_builder.check_image() and not nocache:
        # Image already built
        return docker_builder
    if not docker_builder.build(nocache=nocache):
        raise PolyaxonBuildException("The docker image could not be built.")
    return docker_builder


def build(
    context: str,
    destination: str,
    nocache: bool,
    docker: Optional[APIClient] = None,
    credstore_env: Optional[Dict] = None,
    registries: Optional[List[Union[Uri, str]]] = None,
    max_retries: int = 3,
    sleep_interval: int = 1,
):
    """Build necessary code for a job to run"""
    retry = 0
    is_done = False
    while retry < max_retries and not is_done:
        if retry:
            time.sleep(sleep_interval)
        try:
            docker_builder = _build(
                context=context,
                destination=destination,
                docker=docker,
                nocache=nocache,
                credstore_env=credstore_env,
                registries=registries,
            )
            is_done = True
            return docker_builder
        except ReadTimeoutError:
            retry += 1
    if not is_done:
        raise PolyaxonBuildException(
            "The docker image could not be built, client timed out."
        )


def push(
    destination: str,
    docker: Optional[APIClient] = None,
    max_retries: int = 3,
    sleep_interval: int = 1,
):
    docker_pusher = DockerPusher(destination=destination, docker=docker)
    retry = 0
    is_done = False
    while retry < max_retries and not is_done:
        if retry:
            time.sleep(sleep_interval)
        try:
            if not docker_pusher.push():
                raise PolyaxonBuildException("The docker image could not be pushed.")
            else:
                is_done = True
        except ReadTimeoutError:
            retry += 1

    if not is_done:
        raise PolyaxonBuildException(
            "The docker image could not be pushed, client timed out."
        )


def build_and_push(
    context: str,
    destination: str,
    nocache: bool,
    credstore_env: Optional[Dict] = None,
    registries: Optional[List[Union[Uri, str]]] = None,
    max_retries: int = 3,
    sleep_interval: int = 1,
):
    """Build necessary code for a job to run and push it."""
    # Build the image
    docker_builder = build(
        context=context,
        destination=destination,
        nocache=nocache,
        credstore_env=credstore_env,
        registries=registries,
        max_retries=max_retries,
        sleep_interval=sleep_interval,
    )
    push(
        destination=destination,
        docker=docker_builder.docker,
        max_retries=max_retries,
        sleep_interval=sleep_interval,
    )
