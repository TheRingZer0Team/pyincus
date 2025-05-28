#!/usr/bin/env python3
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

from pyincus.exceptions import (
    IncusException,
    InvalidACLGressException,
    InvalidACLRuleActionException,
    InvalidACLRuleKeyException,
    InvalidACLRuleProtocolException,
    InvalidACLRuleStateException,
    InvalidDescriptionException,
    MissingProtocolException,
    NetworkACLAlreadyExistsException,
    NetworkACLException,
    NetworkACLInUseException,
    NetworkACLNotFoundException,
)
from pyincus.incus import Incus
from pyincus.utils import (
    REGEX_EMPTY_BODY,
    validateObjectFormat,
)

if TYPE_CHECKING:
    from pyincus.models.projects import Project


class NetworkACL:
    possibleActions: list[str] = ["allow", "reject", "drop"]

    possibleStates: list[str] = ["enabled", "disabled", "logged"]

    possibleProtocols: list[str] = ["icmp4", "icmp6", "tcp", "udp"]

    possibleRuleKeys: list[str] = [
        "action",
        "state",
        "description",
        "source",
        "destination",
        "protocol",
        "source_port",
        "destination_port",
        "icmp_type",
        "icmp_code",
    ]

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
    def config(self) -> dict:
        return self.get(project=self.project, name=self.name).attributes["config"]

    @property
    def description(self) -> str:
        return self.get(project=self.project, name=self.name).attributes["description"]

    @description.setter
    def description(self, value: str) -> None:
        self.save(description=value)

    @property
    def egress(self) -> list:
        return self.get(project=self.project, name=self.name).attributes["egress"]

    @egress.setter
    def egress(self, value: list) -> None:
        self.save(egress=value)

    @property
    def ingress(self) -> list:
        return self.get(project=self.project, name=self.name).attributes["ingress"]

    @ingress.setter
    def ingress(self, value: list) -> None:
        self.save(ingress=value)

    @property
    def usedBy(self) -> list:
        return self.get(project=self.project, name=self.name).attributes["used_by"]

    @classmethod
    def _fetch(
        cls, project: Project, name: str, skipValidation=False, **kwargs
    ) -> NetworkACL | None:
        if not skipValidation:
            validateObjectFormat(name)

        result = Incus.run(
            cmd=(
                cmd
                := f"{Incus.binaryPath} network acl show --project='{project.name}' '{project.remote.name}':'{name}'"
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
    def get(cls, project: Project, name: str) -> NetworkACL:
        acl = cls._fetch(project=project, name=name)

        if acl is None:
            raise NetworkACLNotFoundException()

        return acl

    @classmethod
    def exists(cls, project: Project, name: str, **kwargs) -> bool:
        return isinstance(cls._fetch(project=project, name=name, **kwargs), NetworkACL)

    @classmethod
    def list(
        cls, project: Project, filter: str = "", skipValidation=False, **kwargs
    ) -> list[NetworkACL]:
        if not skipValidation:
            validateObjectFormat(filter)

        objs = []
        cmd = f"{Incus.binaryPath} network acl list -fyaml --project='{project.name}' '{project.remote.name}':"

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
        *,
        description: str | None = None,
        egress: list | None = None,
        ingress: list | None = None,
    ) -> NetworkACL:
        validateObjectFormat(name)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} network acl create --project='{project.name}' '{project.remote.name}':'{name}'"
        )

        if result["error"]:
            if "The network ACL already exists" in result["data"]:
                raise NetworkACLAlreadyExistsException(name=name)

            raise NetworkACLException(result["data"])

        acl = cls(project=project, name=name)

        try:
            acl.save(description=description, egress=egress, ingress=ingress)
        except NetworkACLException as error:
            acl.delete()
            raise error

        return acl

    def delete(self) -> None:
        result = Incus.run(
            cmd=f"{Incus.binaryPath} network acl delete --project='{self.project.name}' '{self.project.remote.name}':'{self.name}'"
        )

        if result["error"]:
            if "Network ACL not found" in result["data"]:
                raise NetworkACLNotFoundException()
            if "Cannot delete an ACL that is in use" in result["data"]:
                raise NetworkACLInUseException(name=self.name)

            raise NetworkACLException(result["data"])

    def refresh(self) -> None:
        self.__attributes = self.get(project=self.project, name=self.name).attributes

    def rename(self, name: str) -> None:
        validateObjectFormat(name)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} network acl rename --project='{self.project.name}' '{self.project.remote.name}':'{self.name}' '{name}'"
        )

        if result["error"]:
            if "An ACL by that name exists already" in result["data"]:
                raise NetworkACLAlreadyExistsException(name=name)
            if "Cannot rename an ACL that is in use" in result["data"]:
                raise NetworkACLInUseException(name=name)

        self.attributes["name"] = name

    def save(
        self,
        description: str | None = None,
        egress: list | None = None,
        ingress: list | None = None,
    ) -> None:
        self.refresh()

        if description is not None:
            if not isinstance(description, str):
                raise InvalidDescriptionException()

            self.attributes["description"] = description

        if egress is not None:
            self.attributes["egress"] = self.validateGress(gress=egress)

        if ingress is not None:
            self.attributes["ingress"] = self.validateGress(gress=ingress)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} network acl edit --project='{self.project.name}' '{self.project.remote.name}':'{self.name}'",
            input=yaml.safe_dump(self.attributes),
        )

        if result["error"]:
            if "Error: yaml: unmarshal errors:" in result["data"]:
                raise NetworkACLException("Error: yaml: unmarshal errors:")
            raise NetworkACLException(result["data"])

        self.attributes = self.get(project=self.project, name=self.name).attributes

    @staticmethod
    def validateGress(gress: list) -> list:
        if not isinstance(gress, list):
            raise InvalidACLGressException()

        if gress:
            for g in gress:
                if not isinstance(g, dict):
                    raise InvalidACLGressException()

                if "action" not in g or not isinstance(g["action"], str):
                    raise InvalidACLRuleActionException(
                        allowed=NetworkACL.possibleActions
                    )

                if g["action"] not in NetworkACL.possibleActions:
                    raise InvalidACLRuleActionException(
                        allowed=NetworkACL.possibleActions, action=g["action"]
                    )

                if "state" not in g or not isinstance(g["state"], str):
                    raise InvalidACLRuleStateException(
                        allowed=NetworkACL.possibleStates
                    )

                if g["state"] not in NetworkACL.possibleStates:
                    raise InvalidACLRuleStateException(
                        allowed=NetworkACL.possibleStates, state=g["state"]
                    )

                if (
                    "protocol" in g
                    and g["protocol"] not in NetworkACL.possibleProtocols
                ):
                    raise InvalidACLRuleProtocolException(
                        allowed=NetworkACL.possibleProtocols, protocol=g["protocol"]
                    )

                if (
                    ("source_port" in g and g["source_port"])
                    or ("destination_port" in g and g["destination_port"])
                ) and ("protocol" not in g or g["protocol"] is None):
                    raise MissingProtocolException()

                for k in g.keys():
                    if g[k] is None:
                        del g[k]
                        continue

                    if k not in NetworkACL.possibleRuleKeys:
                        raise InvalidACLRuleKeyException(
                            allowed=NetworkACL.possibleRuleKeys
                        )

                    if not isinstance(k, str):
                        raise InvalidACLRuleKeyException(
                            allowed=NetworkACL.possibleRuleKeys, key=k
                        )

        return gress
