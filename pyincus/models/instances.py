#!/usr/bin/env python3
from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Any

import yaml

from pyincus.exceptions import (
    DeviceNotFoundException,
    IncusException,
    InstanceAlreadyExistsException,
    InstanceException,
    InstanceExecFailedException,
    InstanceIsAlreadyStoppedException,
    InstanceIsNotRunningException,
    InstanceIsPausedException,
    InstanceIsRunningException,
    InstanceNotFoundException,
    InstanceTimeoutExceededException,
    InvalidDescriptionException,
    InvalidImageNameFormatException,
    NameAlreadyInUseException,
    NetworkNotFoundException,
)
from pyincus.incus import Incus
from pyincus.utils import (
    REGEX_DEVICE_NOT_FOUND,
    REGEX_EMPTY_BODY,
    REGEX_IMAGE_NAME,
    REGEX_NETWORK_NOT_FOUND_COPY,
    isTrue,
    validateObjectFormat,
)

if TYPE_CHECKING:
    from pyincus.models.projects import Project


class Instance:
    def __init__(self, project: Project, name: str, **kwargs) -> None:
        self.project = project
        self.name = name
        if kwargs:
            if "name" in kwargs:
                del kwargs["name"]
            self.__attributes = kwargs

    def __str__(self) -> str:
        return f"{self.__class__.__name__} (name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def attributes(self) -> dict[str, Any]:
        return self.__attributes

    @attributes.setter
    def attributes(self, value: dict[str, Any]) -> None:
        self.__attributes = value

    @property
    def architecture(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["architecture"]

    @property
    def config(self) -> dict:
        return self.get(project=self.project, name=self.name).attributes["config"]

    @config.setter
    def config(self, value: dict) -> None:
        self.save(config=value)

    @property
    def devices(self) -> dict[str, dict]:
        return self.get(project=self.project, name=self.name).attributes["devices"]

    @devices.setter
    def devices(self, value: dict[str, dict]) -> None:
        self.save(devices=value)

    @property
    def ephemeral(self) -> bool:
        return self.get(project=self.project, name=self.name).attributes["ephemeral"]

    @property
    def profiles(self) -> list[str]:
        return self.get(project=self.project, name=self.name).attributes["profiles"]

    @profiles.setter
    def profiles(self, value: list[str]) -> None:
        self.save(profiles=value)

    @property
    def stateful(self) -> bool:
        return self.get(project=self.project, name=self.name).attributes["stateful"]

    @property
    def description(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["description"]

    @description.setter
    def description(self, value: str) -> None:
        self.save(description=value)

    @property
    def createdAt(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["created_at"]

    @property
    def expandedConfig(self) -> dict[str, str]:
        return self.get(project=self.project, name=self.name).attributes[
            "expanded_config"
        ]

    @property
    def expandedDevices(self) -> dict[str, dict]:
        return self.get(project=self.project, name=self.name).attributes[
            "expanded_devices"
        ]

    @property
    def status(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["status"]

    @property
    def statusCode(self) -> int:
        return self.get(project=self.project, name=self.name).attributes["status_code"]

    @property
    def lastUsedAt(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["last_used_at"]

    @property
    def location(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["location"]

    @property
    def type(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["type"]

    @property
    def backups(self) -> list:
        return self.get(project=self.project, name=self.name).attributes["backups"]

    @property
    def state(self) -> dict[str, Any]:
        return self.get(project=self.project, name=self.name).attributes["state"]

    @property
    def snapshots(self) -> list:
        return self.get(project=self.project, name=self.name).attributes["snapshots"]

    @classmethod
    def _fetch(cls, project: Project, name: str, **kwargs) -> Instance | None:
        i = None

        validateObjectFormat(name)

        instances = cls.list(project=project, filter=f"^{name}$", skipValidation=True)

        if len(instances) > 0:
            i = instances[0]

        return i

    @classmethod
    def exists(cls, project: Project, name: str, **kwargs) -> bool:
        return isinstance(cls._fetch(project=project, name=name, **kwargs), Instance)

    @classmethod
    def get(cls, project: Project, name: str) -> Instance:
        instance = cls._fetch(project=project, name=name)

        if instance is None or not isinstance(instance, Instance):
            raise InstanceNotFoundException()

        return instance

    @classmethod
    def list(
        cls, project: Project, filter: str = "", skipValidation=False, **kwargs
    ) -> list[Instance]:
        if not skipValidation:
            validateObjectFormat(filter)

        objs = []
        cmd = f"{Incus.binaryPath} list -fyaml --project='{project.name}' '{project.remote.name}':'{filter}'"
        result = Incus.run(cmd=cmd, **kwargs)

        if result["error"]:
            if REGEX_EMPTY_BODY.search(result["data"]):
                print(f'Retrying listing "{cmd}"...')
                return cls.list(
                    project=project,
                    filter=filter,
                    skipValidation=skipValidation,
                    **kwargs,
                )
            else:
                raise IncusException(result["data"])

        results = yaml.safe_load(result["data"])

        # If it's a dictionary (e.g. for Remotes), change it to a list like the majority.
        # Example:
        #   {"My-name-1":{"other-attribute":true}, "My-name-2":{"other-attribute":false}}
        #   To:
        #   [{"name":"My-name-1","other-attribute":true},{"name":"My-name-2","other-attribute":false}]
        if isinstance(results, dict):
            tmp = []
            for name, obj in results.items():
                obj["name"] = name
                tmp.append(obj)

            results = tmp

        for obj in results:
            if "project" in obj:
                del obj["project"]
            objs.append(cls(project=project, **obj))

        return objs

    @classmethod
    def copy(
        cls,
        project: Project,
        source: str,
        name: str | None = None,
        *,
        snapshotName: str | None = None,
        projectTarget: Project | None = None,
        config: dict | None = None,
        device: dict[str, dict] | None = None,
        profile: str | None = None,
        mode: str = "pull",
        storage: str | None = None,
        allowInconsistent: bool = False,
        instanceOnly: bool = False,
        noProfile: bool = False,
        refresh: bool = False,
        stateless: bool = False,
    ) -> Instance:
        validateObjectFormat(
            source,
            name,
            snapshotName,
            project.name,
            project.remote.name,
            projectTarget.name if projectTarget else None,
            projectTarget.remote.name if projectTarget else None,
            profile,
            storage,
        )

        if name is None and not refresh:
            raise InstanceException("""if(name is None and not refresh):""")

        configToString = None
        deviceToString = None

        if config is not None:
            # Expect to receive {"key":"value"}
            configToString = " ".join([f"-c {k}={v}" for k, v in config.items()])

        if device is not None:
            # Expect to receive this format {"eth0":{"key":"value"},"root":{"key":"value"}}
            for n, values in device.items():
                deviceToString = " ".join(
                    [f"-d {n},{k}={v}" for k, v in values.items()]
                )

        if mode not in ["pull", "push", "relay"]:
            raise InstanceException("""if(not mode in ["pull", "push", "relay"]):""")

        if projectTarget is None:
            projectTarget = project

        name = source

        result = Incus.run(
            cmd=textwrap.dedent(
                f"""\
                    {Incus.binaryPath} copy 
                    {f"'{project.remote.name}':" if project.remote.name else ""}'{source}'{f"/'{snapshotName}'" if snapshotName else ""} 
                    {f"'{projectTarget.remote.name}':" if projectTarget.remote.name else ""}'{name}' 
                    {f"--project='{project.name}' " if project.name else ""} 
                    {configToString if configToString else ""} 
                    {deviceToString if deviceToString else ""} 
                    {f"--mode='{mode}' " if mode else ""}
                    {f"--profile='{profile}' " if not noProfile and profile else ""}
                    {f"--storage='{storage}' " if storage else ""}
                    {f"--target-project='{projectTarget}' " if projectTarget else ""}
                    {"--allow-inconsistent " if allowInconsistent else ""}
                    {"--instance-only " if instanceOnly else ""}
                    {"--no-profile " if noProfile else ""}
                    {"--stateless " if stateless else ""}
                """
            ).replace("\n", "")
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                print('Command "copy" broke, attempt to get the content...')
                return cls.get(project=project, name=name if name else source)

            match = REGEX_DEVICE_NOT_FOUND.search(result["data"])
            if match:
                raise DeviceNotFoundException(match.group("device"))

            match = REGEX_NETWORK_NOT_FOUND_COPY.search(result["data"])
            if match:
                raise NetworkNotFoundException(match.group("network"))

            if 'This "instances" entry already exists' in result["data"]:
                raise InstanceAlreadyExistsException(name=name)

            raise InstanceException(result["data"])

        return Instance(project=project, name=name)

    def delete(self, *, force: bool = True)->None:
        if (
            force
            and "security.protection.delete" in self.config
            and isTrue(self.config["security.protection.delete"])
        ):
            tmpConfig = self.config
            tmpConfig["security.protection.delete"] = False
            self.config = tmpConfig

        result = Incus.run(
            cmd=f"{Incus.binaryPath} delete {'--force ' if force else ''}--project='{self.project.name}' '{self.project.remote.name}':'{self.name}'"
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                if self.exists(project=self.project, name=self.name):
                    self.delete(force=force)
            else:
                if "Instance not found" in result["data"]:
                    raise InstanceNotFoundException()

                raise InstanceException(result["data"])

    def exec(self, cmd: str) -> str:
        cmd = cmd.replace("'", "'\"'\"'")
        result = Incus.run(
            cmd=f"{Incus.binaryPath} exec --project='{self.project.name}' '{self.project.remote.name}':'{self.name}' -- bash -c '{cmd}'"
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                print(
                    'Command "exec" broke, it should have worked but there is no way of knowing.'
                )
            else:
                if "Instance not found" in result["data"]:
                    raise InstanceNotFoundException()
                if (
                    "Failed to retrieve PID of executing child process"
                    in result["data"]
                ):
                    raise InstanceExecFailedException()
                if "Command not found" in result["data"]:
                    raise InstanceExecFailedException()
                if "Instance is not running" in result["data"]:
                    raise InstanceIsNotRunningException()
                if "Instance is frozen" in result["data"]:
                    raise InstanceIsPausedException()

                raise InstanceException(result["data"])

        return result["data"]

    @classmethod
    def init(
        cls,
        project: Project,
        image: str,
        name: str,
        *,
        projectSource: Project | None = None,
        config: dict | None = None,
        device: dict[str, dict] | None = None,
        profile: str | None = None,
        network: str | None = None,
        storage: str | None = None,
        empty: bool = False,
        noProfile: bool = False,
        vm: bool = False,
    ) -> Instance:
        validateObjectFormat(
            name,
            project.remote.name,
            projectSource if projectSource else None,
            profile,
            network,
            storage,
        )
        cls.validateImageName(image)

        configToString = None
        deviceToString = None

        if config:
            # Expect to receive {"key":"value"}
            configToString = " ".join([f"-c {k}={v}" for k, v in config.items()])

        if device:
            # Expect to receive this format {"eth0":{"key":"value"},"root":{"key":"value"}}
            for n, values in device.items():
                deviceToString = " ".join(
                    [f"-d {n},{k}={v}" for k, v in values.items()]
                )

        result = Incus.run(
            cmd=textwrap.dedent(
                f"""\
                    {Incus.binaryPath} init 
                    {f"'{projectSource.remote.name}':" if projectSource else ""}'{image}' 
                    '{project.remote.name}':'{name}' 
                    --project='{project.name}' 
                    {configToString if configToString else ""} 
                    {deviceToString if deviceToString else ""} 
                    {f"--network='{network}' " if network else ""}
                    {f"--profile='{profile}' " if not noProfile and profile else ""}
                    {f"--storage='{storage}' " if storage else ""}
                    {"--empty " if empty else ""}
                    {"--no-profile " if noProfile else ""}
                    {"--vm " if vm else ""}
                """
            ).replace("\n", "")
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                print('Command "init" broke, attempt to get the content...')
                return cls.get(project=project, name=name)
            if 'This "instances" entry already exists' in result["data"]:
                raise InstanceAlreadyExistsException(name=name)
            raise InstanceException(result["data"])

        return Instance(project=project, name=name)

    @classmethod
    def launch(
        cls,
        project: Project,
        image: str,
        name: str,
        *,
        projectSource: Project | None = None,
        config: dict | None = None,
        device: dict[str, dict] | None = None,
        profile: str | None = None,
        network: str | None = None,
        storage: str | None = None,
        empty: bool = False,
        noProfile: bool = False,
        vm: bool = False,
    ) -> Instance:
        validateObjectFormat(
            name,
            project.name,
            project.remote.name,
            *([projectSource.remote.name, projectSource.name] if projectSource else []),
            profile,
            network,
            storage,
        )
        cls.validateImageName(image)

        configToString = None
        deviceToString = None

        if config:
            # Expect to receive {"key":"value"}
            configToString = " ".join([f"-c {k}={v}" for k, v in config.items()])

        if device:
            # Expect to receive this format {"eth0":{"key":"value"},"root":{"key":"value"}}
            for n, values in device.items():
                deviceToString = " ".join(
                    [f"-d {n},{k}={v}" for k, v in values.items()]
                )

        result = Incus.run(
            cmd=textwrap.dedent(
                f"""\
                    {Incus.binaryPath} launch 
                    {f"'{projectSource.remote.name}':" if projectSource else ""}'{image}' 
                    '{project.remote.name}':'{name}' 
                    --project='{project.name}' 
                    {configToString if configToString else ""} 
                    {deviceToString if deviceToString else ""} 
                    {f"--network='{network}' " if network else ""}
                    {f"--profile='{profile}' " if not noProfile and profile else ""}
                    {f"--storage='{storage}' " if storage else ""}
                    {"--empty " if empty else ""}
                    {"--no-profile " if noProfile else ""}
                    {"--vm " if vm else ""}
                """
            ).replace("\n", "")
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                print('Command "launch" broke, attempt to get the content...')
                return cls.get(project=project, name=name)
            if 'This "instances" entry already exists' in result["data"]:
                raise InstanceAlreadyExistsException(name=name)
            raise InstanceException(result["data"])

        return Instance(project=project, name=name)

    def move(
        self,
        source: str,
        *,
        name: str | None = None,
        remoteSource: str | None = None,
        remoteDestination: str | None = None,
        projectSource: str | None = None,
        projectDestination: str | None = None,
        config: dict | None = None,
        device: dict[str, dict] | None = None,
        profile: str | None = None,
        mode: str = "pull",
        storage: str | None = None,
        allowInconsistent: bool = False,
        instanceOnly: bool = False,
        noProfile: bool = False,
        stateless: bool = False,
    ) -> Instance:
        validateObjectFormat(
            source,
            name,
            remoteSource,
            remoteDestination,
            projectSource,
            projectDestination,
            profile,
            storage,
        )

        configToString = None
        deviceToString = None

        if config:
            # Expect to receive {"key":"value"}
            configToString = " ".join([f"-c {k}={v}" for k, v in config.items()])

        if device:
            # Expect to receive this format {"eth0":{"key":"value"},"root":{"key":"value"}}
            for n, values in device.items():
                deviceToString = " ".join(
                    [f"-d {n},{k}={v}" for k, v in values.items()]
                )

        if mode not in ["pull", "push", "relay"]:
            raise InstanceException("""if(not mode in ["pull", "push", "relay"]):""")

        if remoteSource is None:
            remoteSource = self.project.remote.name

        if remoteDestination is None:
            remoteDestination = self.project.remote.name

        if projectSource is None:
            projectSource = self.project.name

        if projectDestination is None:
            projectDestination = self.project.name

        if name is None:
            if projectDestination != projectSource:
                name = source
            else:
                raise InstanceException(
                    f"Name must be set when the source project ({projectSource}) and destination project ({projectDestination}) are not equal."
                )

        result = Incus.run(
            cmd=textwrap.dedent(
                f"""\
                    {Incus.binaryPath} move 
                    {f"'{remoteSource}':" if remoteSource else ""}'{source}' 
                    {f"'{remoteDestination}':" if remoteDestination else ""}'{name}' 
                    {f"--project='{projectSource}' " if projectSource else ""} 
                    {configToString if configToString else ""} 
                    {deviceToString if deviceToString else ""} 
                    {f"--mode='{mode}' " if mode else ""}
                    {f"--profile='{profile}' " if not noProfile and profile else ""}
                    {f"--storage='{storage}' " if storage else ""}
                    {f"--target-project='{projectDestination}' " if projectDestination else ""}
                    {"--allow-inconsistent " if allowInconsistent else ""}
                    {"--instance-only " if instanceOnly else ""}
                    {"--no-profile " if noProfile else ""}
                    {"--stateless " if stateless else ""}
                """
            ).replace("\n", "")
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                print('Command "copy" broke, attempt to get the content...')
                return self.get(project=self.project, name=name)

            match = REGEX_DEVICE_NOT_FOUND.search(result["data"])
            if match:
                raise DeviceNotFoundException(match.group("device"))

            match = REGEX_NETWORK_NOT_FOUND_COPY.search(result["data"])
            if match:
                raise NetworkNotFoundException(match.group("network"))

            if 'This "instances" entry already exists' in result["data"]:
                raise InstanceAlreadyExistsException(name=name)

            raise InstanceException(result["data"])

        return Instance(project=self.project, name=name)

    def pause(self, timeout: int | None = None) -> None:
        result = Incus.run(
            cmd=f"{Incus.binaryPath} pause --project='{self.project.name}' '{self.project.remote.name}':'{self.name}'",
            timeout=timeout,
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                if self.status.lower() != "frozen":
                    print('Command "pause" broke, attempt to pause again...')
                    self.pause(timeout=timeout)
            else:
                if "Error: The instance isn't running" == result["data"]:
                    raise InstanceIsNotRunningException()
                raise InstanceException(result["data"])

    def rename(self, name: str) -> None:
        validateObjectFormat(name)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} rename --project='{self.project.name}' '{self.project.remote.name}':'{self.name}' '{name}'"
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                if self.exists(project=self.project, name=self.name):
                    if self.status.lower() == "running":
                        raise InstanceIsRunningException()
                    else:
                        raise NameAlreadyInUseException(name)
            else:
                if result["data"].startswith('Error: Name "') and result[
                    "data"
                ].endswith('" already in use'):
                    raise NameAlreadyInUseException(
                        result["data"][
                            len('Error: Name "') : len('" already in use') + 1
                        ]
                    )
                if "Error: Renaming of running instance not allowed" == result["data"]:
                    raise InstanceIsRunningException()

        self.attributes["name"] = name

    def restart(self, *, force: bool = True, timeout: int = -1) -> None:
        result = Incus.run(
            cmd=f"{Incus.binaryPath} restart {'--force ' if force else ''}--timeout={timeout} --project='{self.project.name}' '{self.project.remote.name}':'{self.name}'"
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                print(
                    'Command "restart" broke, it should have worked but there is no way of knowing.'
                )
            else:
                if "Error: The instance is already stopped" == result["data"]:
                    raise InstanceIsAlreadyStoppedException()
                if "context deadline exceeded" in result["data"]:
                    raise InstanceTimeoutExceededException()
                raise InstanceException(result["data"])

    def restore(self, name: str, *, stateful: bool = False) -> None:
        validateObjectFormat(name)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} snapshot restore {'--stateful ' if stateful else ''}--project='{self.project.name}' '{self.project.remote.name}':'{self.name}' {name}"
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                print(
                    'Command "restore" broke, it should have worked but since there is no way of knowing and that it should be fine to restore again, let\'s do it again.'
                )
                self.restore(name=name, stateful=stateful)
            else:
                raise InstanceException(result["data"])

    def start(self) -> None:
        result = Incus.run(
            cmd=f"{Incus.binaryPath} start --project='{self.project.name}' '{self.project.remote.name}':'{self.name}'"
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                if self.status.lower() != "running":
                    print('Command "start" broke, retrying to start...')
                    self.start()
            else:
                raise InstanceException(result["data"])

    def stop(self, *, force: bool = True, timeout: int = -1) -> None:
        result = Incus.run(
            cmd=f"{Incus.binaryPath} stop {'--force ' if force else ''}--timeout={timeout} --project='{self.project.name}' '{self.project.remote.name}':'{self.name}'"
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                if self.status.lower() != "stopped":
                    print('Command "stop" broke, retrying to stop...')
                    self.stop(force=force, timeout=timeout)
            else:
                if "Error: The instance is already stopped" == result["data"]:
                    raise InstanceIsAlreadyStoppedException()
                if "Error: The instance isn't running" == result["data"]:
                    raise InstanceIsNotRunningException()
                if "context deadline exceeded" in result["data"]:
                    raise InstanceTimeoutExceededException()
                raise InstanceException(result["data"])

    def save(
        self,
        config: dict | None = None,
        devices: dict | None = None,
        profiles: list | None = None,
        description: str | None = None,
    ) -> None:
        self.refresh()

        if description is not None:
            if not isinstance(description, str):
                raise InvalidDescriptionException()

            self.attributes["description"] = description

        if config is not None:
            if not isinstance(config, dict):
                raise InstanceException("config must be a dictionary.")

            tmpConfig = self.config

            for k, v in config.items():
                if k not in self.expandedConfig:
                    raise InstanceException(f'config "{k}" not in expanded_config.')

                tmpConfig[k] = v

            self.attributes["config"] = tmpConfig

        if devices is not None:
            if not isinstance(devices, dict):
                raise InstanceException("devices must be a dictionary.")

            tmpDevices = {}

            for k, v in devices.items():
                if k not in self.expandedDevices:
                    raise InstanceException(f'device "{k}" not in expanded_devices.')

                tmpDevices[k] = self.expandedDevices[k]
                tmpDevices[k].update(v)

            self.attributes["devices"] = tmpDevices

        if profiles is not None:
            if not isinstance(profiles, list):
                raise InstanceException("profiles must be a list containing strings.")

            validateObjectFormat(*profiles)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} config edit --project='{self.project.name}' '{self.project.remote.name}':'{self.name}'",
            input=yaml.safe_dump(self.attributes),
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                if (
                    self.attributes
                    != self.get(project=self.project, name=self.name).attributes
                ):
                    print('Command "save" broke, retrying to save...')
                    self.save(
                        config=config,
                        devices=devices,
                        profiles=profiles,
                        description=description,
                    )
            else:
                if "Error: yaml: unmarshal errors:" in result["data"]:
                    raise InstanceException("Error: yaml: unmarshal errors:")
                if "Missing device type in config" in result["data"]:
                    raise DeviceNotFoundException()
                raise InstanceException(result["data"])

        self.attributes = self.get(project=self.project, name=self.name).attributes

    def snapshot(
        self, name: str, *, reuse: bool = False, stateful: bool = False
    ) -> None:
        validateObjectFormat(name)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} snapshot create {'--reuse ' if reuse else ''}{'--stateful ' if stateful else ''}--project='{self.project.name}' '{self.project.remote.name}':'{self.name}' {name}"
        )

        if result["error"]:
            if (
                REGEX_EMPTY_BODY.search(result["data"])
                or "Operation not found" in result["data"]
            ):
                found = False
                for snapshot in self.snapshots:
                    if snapshot["name"] == name:
                        found = True
                if not found:
                    print('Command "snapshot" broke, retrying to create...')
                    self.snapshot(name=name, reuse=reuse, stateful=stateful)
            else:
                raise InstanceException(result["data"])

    @staticmethod
    def validateImageName(image: str) -> None:
        if not REGEX_IMAGE_NAME.match(image):
            raise InvalidImageNameFormatException(image)

    def refresh(self) -> None:
        self.__attributes = self.get(project=self.project, name=self.name).attributes
