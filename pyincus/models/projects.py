#!/usr/bin/env python3
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

from pyincus.exceptions import (
    IncusException,
    ProjectAlreadyExistsException,
    ProjectDefaultCannotBeRenamedException,
    ProjectException,
    ProjectIsInUseException,
    ProjectNotFoundException,
)
from pyincus.incus import Incus
from pyincus.models.acls import NetworkACL
from pyincus.models.instances import Instance
from pyincus.models.networks import Network
from pyincus.utils import (
    REGEX_EMPTY_BODY,
    validateObjectFormat,
)

if TYPE_CHECKING:
    from pyincus.models.remotes import Remote


class Project:
    def __init__(self, remote: Remote, name: str, **kwargs) -> None:
        self.remote = remote
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
    def instances(self) -> list[Instance]:
        return Instance.list(project=self)

    @property
    def networks(self) -> list[Network]:
        return Network.list(project=self)

    @property
    def acls(self) -> list[NetworkACL]:
        return NetworkACL.list(project=self)

    @property
    def config(self) -> dict:
        return self.get(remote=self.remote, name=self.name).attributes["config"]

    @property
    def description(self) -> str:
        return self.get(remote=self.remote, name=self.name).attributes["description"]

    @property
    def usedBy(self) -> list[str]:
        return self.get(remote=self.remote, name=self.name).attributes["used_by"]

    @classmethod
    def _fetch(
        cls, remote: Remote, name: str, skipValidation=False, **kwargs
    ) -> Project | None:
        if not skipValidation:
            validateObjectFormat(name)

        result = Incus.run(
            cmd=(cmd := f"{Incus.binaryPath} project show '{remote.name}':'{name}'"),
            **kwargs,
        )

        if result["error"]:
            if REGEX_EMPTY_BODY.search(result["data"]):
                print(f'Retrying fetching "{cmd}"...')
                return cls._fetch(
                    remote=remote, name=name, skipValidation=skipValidation, **kwargs
                )
            else:
                return result["data"]
        else:
            return cls(
                remote=remote,
                **yaml.safe_load(result["data"]),
            )

    @classmethod
    def exists(cls, remote: Remote, name: str, **kwargs) -> bool:
        return isinstance(cls._fetch(remote=remote, name=name, **kwargs), Project)

    @classmethod
    def get(cls, remote: Remote, name: str) -> Project:
        project = cls._fetch(remote=remote, name=name)

        if project is None:
            raise ProjectNotFoundException()

        return project

    @classmethod
    def list(
        cls, remote: Remote, filter: str = "", skipValidation=False, **kwargs
    ) -> list[Project]:
        if not skipValidation:
            validateObjectFormat(filter)

        objs = []
        cmd = f"{Incus.binaryPath} project list -fyaml '{remote.name}':"

        result = Incus.run(cmd=cmd, **kwargs)

        if result["error"]:
            if REGEX_EMPTY_BODY.search(result["data"]):
                print(f'Retrying listing "{cmd}"...')
                return cls.list(
                    remote=remote,
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
            objs.append(cls(remote=remote, **obj))

        return objs

    def refresh(self) -> None:
        self.__attributes = self.get(remote=self.remote, name=self.name).attributes

    def rename(self, name: str) -> None:
        validateObjectFormat(name)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} project rename '{self.remote.name}':'{self.name}' '{name}'"
        )

        if result["error"]:
            if "The 'default' project cannot be renamed" in result["data"]:
                raise ProjectDefaultCannotBeRenamedException()
            if "already exists" in result["data"]:
                raise ProjectAlreadyExistsException(name=name)
            if "Only empty projects can be renamed" in result["data"]:
                raise ProjectIsInUseException()
            raise ProjectException(result["data"])

        self.attributes["name"] = name
