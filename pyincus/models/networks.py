#!/usr/bin/env python3
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

from pyincus.exceptions import (
    IncusException,
    InvalidDescriptionException,
    InvalidNetworkConfigurationKeyException,
    InvalidNetworkTypeException,
    NetworkAlreadyExistsException,
    NetworkException,
    NetworkInUseException,
    NetworkNotFoundException,
)
from pyincus.incus import Incus
from pyincus.utils import (
    REGEX_EMPTY_BODY,
    validateObjectFormat,
)

if TYPE_CHECKING:
    from pyincus.models.forwards import NetworkForward
    from pyincus.models.projects import Project


class Network:
    possibleNetworkTypes: list[str] = ["bridge", "ovn"]

    possibleConfigKeysForBridge: list[str] = [
        "bridge.driver",
        "bridge.hwaddr",
        "bridge.mode",
        "bridge.mtu",
        "dns.domain",
        "dns.mode",
        "dns.search",
        "dns.zone.forward",
        "dns.zone.reverse.ipv4",
        "dns.zone.reverse.ipv6",
        "fan.type",
        "ipv4.address",
        "ipv4.dhcp",
        "ipv4.dhcp.expiry",
        "ipv4.dhcp.gateway",
        "ipv4.dhcp.ranges",
        "ipv4.firewall",
        "ipv4.nat",
        "ipv4.nat.address",
        "ipv4.nat.order",
        "ipv4.ovn.ranges",
        "ipv4.routes",
        "ipv4.routing",
        "ipv6.address",
        "ipv6.dhcp",
        "ipv6.dhcp.expiry",
        "ipv6.dhcp.ranges",
        "ipv6.dhcp.stateful",
        "ipv6.firewall",
        "ipv6.nat",
        "ipv6.nat.address",
        "ipv6.nat.order",
        "ipv6.ovn.ranges",
        "ipv6.routes",
        "ipv6.routing",
        "maas.subnet.ipv4",
        "maas.subnet.ipv6",
        "raw.dnsmasq",
        "security.acls",
        "security.acls.default.egress.action",
        "security.acls.default.egress.logged",
        "security.acls.default.ingress.action",
        "security.acls.default.ingress.logged",
    ]

    possibleConfigKeysForOVN: list[str] = [
        "network",
        "bridge.hwaddr",
        "bridge.mtu",
        "dns.domain",
        "dns.search",
        "dns.zone.forward",
        "dns.zone.reverse.ipv4",
        "dns.zone.reverse.ipv6",
        "ipv4.address",
        "ipv4.dhcp",
        "ipv4.l3only",
        "ipv4.nat",
        "ipv4.nat.address",
        "ipv6.address",
        "ipv6.dhcp",
        "ipv6.dhcp.stateful",
        "ipv6.l3only",
        "ipv6.nat",
        "ipv6.nat.address",
        "security.acls",
        "security.acls.default.egress.action",
        "security.acls.default.egress.logged",
        "security.acls.default.ingress.action",
        "security.acls.default.ingress.logged",
    ]

    def __init__(self, project: Project, name: str, **kwargs) -> None:
        self.project = project
        self.name = name
        if kwargs:
            if "name" in kwargs:
                del kwargs["name"]
            self.__attributes = kwargs

    @property
    def forwards(self) -> list[NetworkForward]:
        return NetworkForward.list(network=self)

    @property
    def attributes(self) -> dict[str, Any]:
        return self.__attributes

    @attributes.setter
    def attributes(self, value: dict[str, Any]) -> None:
        self.__attributes = value

    @property
    def config(self) -> dict[str, str]:
        return self.get(project=self.project, name=self.name).attributes["config"]

    @config.setter
    def config(self, value: dict[str, str]):
        self.save(config=value)

    @property
    def description(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["description"]

    @description.setter
    def description(self, value: str):
        self.save(description=value)

    @property
    def type(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["type"]

    @property
    def usedBy(self) -> list[str]:
        return self.get(project=self.project, name=self.name).attributes["used_by"]

    @property
    def managed(self) -> bool:
        return self.get(project=self.project, name=self.name).attributes["managed"]

    @property
    def status(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["status"]

    @property
    def locations(self):
        return self.get(project=self.project, name=self.name).attributes["locations"]

    def __str__(self) -> str:
        return f"{self.__class__.__name__} (name={self.name})"

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def _fetch(
        cls, project: Project, name: str, skipValidation=False, **kwargs
    ) -> Network | None:
        if not skipValidation:
            validateObjectFormat(name)

        result = Incus.run(
            cmd=(
                cmd
                := f"{Incus.binaryPath} network show --project='{project.name}' '{project.remote.name}':'{name}'"
            ),
            **kwargs,
        )

        if result["error"]:
            if REGEX_EMPTY_BODY.search(result["data"]):
                print(f'Retrying fetching "{cmd}"...')
                return cls._fetch(
                    project=project, name=name, skipValidation=skipValidation, **kwargs
                )
            else:
                return result["data"]
        else:
            if "project" in (obj := yaml.safe_load(result["data"])):
                del obj["project"]

            return cls(
                project=project,
                **obj,
            )

    @classmethod
    def exists(cls, project: Project, name: str, **kwargs) -> bool:
        return isinstance(cls._fetch(project=project, name=name, **kwargs), Network)

    @classmethod
    def get(cls, project: Project, name: str) -> Network:
        network = cls._fetch(project=project, name=name)

        if network is None:
            raise NetworkNotFoundException()

        return network

    @classmethod
    def list(
        cls, project: Project, filter: str = "", skipValidation=False, **kwargs
    ) -> list[Network]:
        if not skipValidation:
            validateObjectFormat(filter)

        objs = []
        cmd = f"{Incus.binaryPath} network list -fyaml --project='{project.name}' '{project.remote.name}':"

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
    def create(
        cls,
        project: Project,
        name: str,
        _type: str,
        *,
        description: str | None = None,
        config: dict[str, str] | None = None,
    ) -> Network:
        validateObjectFormat(name)

        if _type not in cls.possibleNetworkTypes:
            raise InvalidNetworkTypeException(cls.possibleNetworkTypes)

        configToString = None

        if config is not None:
            # Expect to receive {"key":"value"}
            for k, v in config.items():
                if _type == "bridge":
                    if k not in cls.possibleConfigKeysForBridge:
                        raise InvalidNetworkConfigurationKeyException(
                            allowed=cls.possibleConfigKeysForBridge, key=k
                        )
                elif _type == "ovn":
                    if k not in cls.possibleConfigKeysForOVN:
                        raise InvalidNetworkConfigurationKeyException(
                            allowed=cls.possibleConfigKeysForOVN, key=k
                        )
                else:
                    raise InvalidNetworkTypeException(cls.possibleNetworkTypes)

            configToString = " ".join([f"{k}={v}" for k, v in config.items()])

        result = Incus.run(
            cmd=f"{Incus.binaryPath} network create --project='{project.name}' '{project.remote.name}':'{name}' --type={_type} {configToString if configToString else ''}"
        )

        if result["error"]:
            if "The network already exists" in result["data"]:
                raise NetworkAlreadyExistsException(name=name)

            raise NetworkException(result["data"])

        network = cls(project=project, name=name)

        try:
            network.save(description=description)
        except NetworkException as error:
            network.delete()
            raise error

        return network

    def delete(self):
        result = Incus.run(
            cmd=f"{Incus.binaryPath} network delete --project='{self.project.name}' '{self.project.remote.name}':'{self.name}'"
        )

        if result["error"]:
            if "Network not found" in result["data"]:
                raise NetworkNotFoundException()
            if "Cannot delete a Network that is in use" in result["data"]:
                raise NetworkInUseException(name=self.name)

            raise NetworkException(result["data"])

    def refresh(self) -> None:
        self.__attributes = self.get(project=self.project, name=self.name).attributes

    def rename(self, name: str):
        validateObjectFormat(name)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} network rename --project='{self.project.name}' '{self.project.remote.name}':'{self.name}' '{name}'"
        )

        if result["error"]:
            if "A Network by that name exists already" in result["data"]:
                raise NetworkAlreadyExistsException(name=name)
            if "Cannot rename a Network that is in use" in result["data"]:
                raise NetworkInUseException(name=name)

        self.attributes["name"] = name

    def save(
        self, *, description: str | None = None, config: dict[str, str] | None = None
    ):
        self.refresh()

        if description is not None:
            if not isinstance(description, str):
                raise InvalidDescriptionException()

            self.attributes["description"] = description

        if config:
            tmp = {**config}

            # Expect to receive {"key":"value"}
            for k, v in tmp.items():
                if k.startswith("volatile"):
                    del config[k]
                    continue

                if self.type == "bridge":
                    if k not in self.possibleConfigKeysForBridge:
                        raise InvalidNetworkConfigurationKeyException(
                            allowed=self.possibleConfigKeysForBridge, key=k
                        )
                elif self.type == "ovn":
                    if k not in self.possibleConfigKeysForOVN:
                        raise InvalidNetworkConfigurationKeyException(
                            allowed=self.possibleConfigKeysForOVN, key=k
                        )
                else:
                    raise InvalidNetworkTypeException(self.possibleNetworkTypes)

            self.attributes["config"] = config

        result = Incus.run(
            cmd=f"{Incus.binaryPath} network edit --project='{self.project.name}' '{self.project.remote.name}':'{self.name}'",
            input=yaml.safe_dump(self.attributes),
        )

        if result["error"]:
            if "Error: yaml: unmarshal errors:" in result["data"]:
                raise NetworkException("Error: yaml: unmarshal errors:")
            raise NetworkException(result["data"])

        self.attributes = self.get(project=self.project, name=self.name).attributes
