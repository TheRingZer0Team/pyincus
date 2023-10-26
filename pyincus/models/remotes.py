#!/usr/bin/env python3
from ._models import Model
from .projects import Project

from pyincus.exceptions import  RemoteException,\
                                RemoteNotFoundException,\
                                RemoteAlreadyExistsException,\
                                RemoteLocalCannotBeModifiedException

class Remote(Model):
    def __init__(self, parent: Model=None, name: str=None, **kwargs):
        super().__init__(parent=parent, name=name, **kwargs)

    @property
    def incus(self):
        return self.parent

    @property
    def projects(self):
        return Project(self)

    @property
    def addr(self):
        return self.get(name=self.name).attributes["addr"]

    @property
    def public(self):
        return self.get(name=self.name).attributes["public"]

    @property
    def project(self):
        return self.get(name=self.name).attributes["project"]

    def _fetch(self, name: str):
        r = None

        remotes = self.list()
        for remote in remotes:
            if(name == remote.name):
                r = remote
                break

        return r

    def get(self, name: str):
        remote = self._fetch(name=name)
        
        if(remote is None):
            raise RemoteNotFoundException()

        return remote

    def rename(self, name: str):
        self.validateObjectFormat(name)

        result = self.incus.run(cmd=f"{self.incus.binaryPath} remote rename '{self.name}' '{name}'")

        if(result["error"]):
            if("Remote local is static and cannot be modified" in result["data"]):
                raise RemoteLocalCannotBeModifiedException()
            if(result["data"].endswith("already exists")):
                raise RemoteAlreadyExistsException(name=name)
            raise RemoteException(result["data"])

        self.attributes["name"] = name