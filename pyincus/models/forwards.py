#!/usr/bin/env python3
from __future__ import annotations

import ipaddress
import re
from typing import TYPE_CHECKING, Any

import yaml

from pyincus.exceptions import (
    DuplicatePortException,
    IncusException,
    InvalidDescriptionException,
    InvalidIPAddressException,
    InvalidPortProtocolException,
    InvalidPortRangeException,
    InvalidTargetPortsException,
    NetworkForwardException,
    NetworkForwardNotFoundException,
    NetworkForwardPortAlreadyExistsException,
    NetworkForwardPortNotFoundException,
    StartLowerThanEndException,
)
from pyincus.incus import Incus
from pyincus.utils import REGEX_EMPTY_BODY, validateObjectFormat

if TYPE_CHECKING:
    from pyincus.models.networks import Network

REGEX_LIST_OF_PORTS = re.compile(
    r"^[1-9][0-9]{0,4}(([\-][1-9][0-9]{0,4})?([,][1-9][0-9]{0,4}|$))*$"
)


class NetworkForward:
    possibleProtocols: list[str] = ["tcp", "udp"]

    def __init__(self, network: Network, name: str, **kwargs) -> None:
        self.network = network
        self.name = name
        if kwargs:
            if "name" in kwargs:
                del kwargs["name"]
            self.__attributes = kwargs

    def __str__(self) -> str:
        return f"{self.__class__.__name__} (config={self.config}, ports={self.ports})"

    @property
    def attributes(self) -> dict[str, Any]:
        return self.__attributes

    @attributes.setter
    def attributes(self, value: dict[str, Any]) -> None:
        self.__attributes = value

    @property
    def listenAddress(self) -> str:
        return self.attributes["listen_address"]

    @property
    def config(self) -> dict:
        return self.get(
            network=self.network, listenAddress=self.listenAddress
        ).attributes["config"]

    @property
    def description(self) -> str:
        return self.get(
            network=self.network, listenAddress=self.listenAddress
        ).attributes["description"]

    @description.setter
    def description(self, value: str):
        self.save(description=value)

    @property
    def ports(self):
        return self.get(
            network=self.network, listenAddress=self.listenAddress
        ).attributes["ports"]

    @classmethod
    def _fetch(
        cls, network: Network, name: str, skipValidation=False, **kwargs
    ) -> NetworkForward | None:
        if not skipValidation:
            validateObjectFormat(name)

        cmd = f"{Incus.binaryPath} network forward show --project='{network.project.name}' '{network.project.remote.name}':'{name}' '{kwargs['listenAddress']}'"
        del kwargs["listenAddress"]
        result = Incus.run(cmd=cmd, **kwargs)

        if result["error"]:
            if REGEX_EMPTY_BODY.search(result["data"]):
                print(f'Retrying fetching "{cmd}"...')
                return cls._fetch(
                    network=network, name=name, skipValidation=skipValidation, **kwargs
                )
            else:
                return result["data"]
        else:
            return cls(
                network=network,
                **yaml.safe_load(result["data"]),
            )

    @classmethod
    def exists(cls, network: Network, listenAddress: str) -> bool:
        return (
            cls._fetch(
                network=network,
                name=network.name,
                listenAddress=listenAddress,
                skipValidation=True,
            )
            is not None
        )

    @classmethod
    def get(cls, network: Network, listenAddress: str) -> NetworkForward:
        if not isinstance(listenAddress, str):
            raise InvalidIPAddressException(listenAddress)

        try:
            ipaddress.ip_address(listenAddress)
        except Exception:
            raise InvalidIPAddressException(listenAddress)

        forward = cls._fetch(
            network=network,
            name=network.name,
            listenAddress=listenAddress,
            skipValidation=True,
        )

        if forward is None:
            raise NetworkForwardNotFoundException()

        return forward

    @classmethod
    def list(
        cls, network: Network, skipValidation=False, **kwargs
    ) -> list[NetworkForward]:
        filter = network.name

        if not skipValidation:
            validateObjectFormat(filter)

        objs = []
        cmd = f"{Incus.binaryPath} network forward list -fyaml --project='{network.project.name}' '{network.project.remote.name}':'{filter}'"

        result = Incus.run(cmd=cmd, **kwargs)

        if result["error"]:
            if REGEX_EMPTY_BODY.search(result["data"]):
                print(f'Retrying listing "{cmd}"...')
                return cls.list(network=network, skipValidation=skipValidation)
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
            objs.append(cls(network=network, **obj))

        return objs

    @staticmethod
    def validatePortList(ports: str | int) -> list[int]:
        tmpPortRanges = []

        if isinstance(ports, int):
            if ports < 1 or ports > 65535:
                raise InvalidPortRangeException(ports=ports)
            tmpPortRanges.append(ports)
        else:
            if not REGEX_LIST_OF_PORTS.match(ports):
                raise InvalidPortRangeException(ports=ports)

            if ports.count(",") > 0:
                tmpPorts = ports.split(",")

                for port in tmpPorts:
                    if port.find("-") > -1:
                        start, end = [int(p) for p in port.split("-")]
                        if start >= end:
                            raise StartLowerThanEndException(ports=port)

                        for i in range(start, end + 1):
                            if i in tmpPortRanges:
                                raise DuplicatePortException(ports=ports, duplicate=i)

                        tmpPortRanges.extend(range(start, end + 1))
                    else:
                        port = int(port)
                        if port in tmpPortRanges:
                            raise DuplicatePortException(ports=ports, duplicate=port)

                        tmpPortRanges.append(port)
            elif ports.find("-") > -1:
                start, end = [int(p) for p in ports.split("-")]
                if start >= end:
                    raise StartLowerThanEndException(ports=ports)

                tmpPortRanges.extend(range(start, end + 1))

        return tmpPortRanges

    def addPort(
        self,
        *,
        protocol: str,
        listenPorts: str,
        targetAddress: str,
        targetPorts: str | None = None,
    ) -> None:
        if not isinstance(protocol, str) or protocol not in self.possibleProtocols:
            raise InvalidPortProtocolException(
                allowed=self.possibleProtocols, protocol=protocol
            )

        if not isinstance(targetAddress, str):
            raise InvalidIPAddressException(targetAddress)

        try:
            ipaddress.ip_address(targetAddress)
        except Exception:
            raise InvalidIPAddressException(targetAddress)

        if listenPorts is None:
            raise InvalidPortRangeException(ports=listenPorts)

        c1 = len(NetworkForward.validatePortList(ports=listenPorts))

        if targetPorts is not None:
            c2 = len(NetworkForward.validatePortList(ports=targetPorts))

            if c2 != c1:
                raise InvalidTargetPortsException(
                    listenPorts=listenPorts, targetPorts=targetPorts
                )

        result = Incus.run(
            cmd=f"{Incus.binaryPath} network forward port add --project='{self.network.project.name}' '{self.network.project.remote.name}':'{self.network.name}' '{self.listenAddress}' '{protocol}' '{listenPorts}' '{targetAddress}'{f' {chr(39)}{targetPorts}{chr(39)} ' if targetPorts else ''}"
        )

        if result["error"]:
            if (
                "Duplicate listen port " in result["data"]
                and f'for protocol "{protocol}" in port specification' in result["data"]
            ):
                port = (
                    result["data"]
                    .split("Duplicate listen port ")[1]
                    .split(f' for protocol "{protocol}" in port specification')[0]
                )
                raise NetworkForwardPortAlreadyExistsException(
                    protocol=protocol, port=port
                )
            raise NetworkForwardException(result["data"])

    def refresh(self) -> None:
        self.attributes = self.get(
            network=self.network, listenAddress=self.listenAddress
        ).attributes

    def removePort(self, *, protocol: str, listenPorts: str) -> None:
        if protocol is None:
            raise InvalidPortProtocolException(allowed=self.possibleProtocols)

        if protocol not in self.possibleProtocols:
            raise InvalidPortProtocolException(
                allowed=self.possibleProtocols, protocol=protocol
            )

        if listenPorts is not None:
            NetworkForward.validatePortList(ports=listenPorts)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} network forward port remove --project='{self.network.project.name}' '{self.network.project.remote.name}':'{self.network.name}' '{self.listenAddress}' '{protocol}' '{listenPorts}'"
        )

        if result["error"]:
            if "No matching port(s) found" in result["data"]:
                raise NetworkForwardPortNotFoundException(ports=listenPorts)
            raise NetworkForwardException(result["data"])

    def save(self, description: str | None = None) -> None:
        self.refresh()

        if description is not None:
            if not isinstance(description, str):
                raise InvalidDescriptionException()

            self.attributes["description"] = description

        result = Incus.run(
            cmd=f"{Incus.binaryPath} network forward edit --project='{self.network.project.name}' '{self.network.project.remote.name}':'{self.network.name}' '{self.listenAddress}'",
            input=yaml.safe_dump(self.attributes),
        )

        if result["error"]:
            if "Error: yaml: unmarshal errors:" in result["data"]:
                raise NetworkForwardException("Error: yaml: unmarshal errors:")
            raise NetworkForwardException(result["data"])

        self.attributes = self.get(
            network=self.network, listenAddress=self.listenAddress
        ).attributes
