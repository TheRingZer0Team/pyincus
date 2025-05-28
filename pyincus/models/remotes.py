#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

import yaml

from pyincus.exceptions import (
    IncusException,
    RemoteAlreadyExistsException,
    RemoteException,
    RemoteLocalCannotBeModifiedException,
    RemoteNotFoundException,
)
from pyincus.incus import Incus
from pyincus.models.projects import Project
from pyincus.utils import (
    REGEX_EMPTY_BODY,
    validateObjectFormat,
)


class Remote:
    def __init__(self, name: str, **kwargs) -> None:
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
    def projects(self) -> list[Project]:
        return Project.list(remote=self)
    
    @property
    def addr(self) -> str:
        return self.get(name=self.name).attributes["addr"]

    @property
    def authType(self) -> str:
        return self.get(name=self.name).attributes["authType"]

    @property
    def protocol(self) -> str:
        return self.get(name=self.name).attributes["protocol"]

    @property
    def public(self) -> bool:
        return self.get(name=self.name).attributes["public"]

    @classmethod
    def _fetch(cls, name: str) -> Remote | None:
        r = None

        remotes = cls.list()
        for remote in remotes:
            if name == remote.name:
                r = remote
                break

        return r

    @classmethod
    def exists(cls, name: str, **kwargs) -> bool:
        return isinstance(cls._fetch(name=name, **kwargs), Remote)

    @classmethod
    def get(cls, name: str) -> Remote:
        remote = cls._fetch(name=name)

        if remote is None or not isinstance(remote, Remote):
            raise RemoteNotFoundException()

        return remote

    @classmethod
    def list(cls, **kwargs) -> list[Remote]:
        objs = []
        cmd = f"{Incus.binaryPath} remote list -fyaml"

        result = Incus.run(cmd=cmd, **kwargs)

        if result["error"]:
            if REGEX_EMPTY_BODY.search(result["data"]):
                print(f'Retrying listing "{cmd}"...')
                return cls.list(**kwargs)
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
            objs.append(cls(**obj))

        return objs

    def refresh(self) -> None:
        self.__attributes = self.get(name=self.name).attributes

    def rename(self, name: str) -> None:
        validateObjectFormat(name)

        result = Incus.run(
            cmd=f"{Incus.binaryPath} remote rename '{self.name}' '{name}'"
        )

        if result["error"]:
            if "Remote local is static and cannot be modified" in result["data"]:
                raise RemoteLocalCannotBeModifiedException()
            if result["data"].endswith("already exists"):
                raise RemoteAlreadyExistsException(name=name)
            raise RemoteException(result["data"])

        self.attributes["name"] = name
