#!/usr/bin/env python3
from ._models import Model
from .acls import NetworkACL
from .instances import Instance
from .networks import Network

from pyincus.exceptions import  ProjectException,\
                                ProjectNotFoundException,\
                                ProjectAlreadyExistsException,\
                                ProjectDefaultCannotBeRenamedException,\
                                ProjectIsInUseException

class Project(Model):
    def __init__(self, parent: Model=None, name: str=None, **kwargs):
        super().__init__(parent=parent, name=name, **kwargs)

    @property
    def incus(self):
        return self.remote.parent

    @property
    def remote(self):
        return self.parent

    @property
    def instances(self):
        return Instance(self)

    @property
    def networks(self):
        return Network(self)

    @property
    def acls(self):
        return NetworkACL(self)

    @property
    def config(self):
        return self.get(name=self.name).attributes["config"]

    @property
    def description(self):
        return self.get(name=self.name).attributes["description"]

    @property
    def usedBy(self):
        return self.get(name=self.name).attributes["used_by"]

    def get(self, name: str):
        project = self._fetch(name=name)
        
        if(not isinstance(project, self.__class__)):
            raise ProjectNotFoundException()

        return project

    def rename(self, name: str):
        self.validateObjectFormat(name)

        result = self.incus.run(cmd=f"{self.incus.binaryPath} project rename '{self.remote.name}':'{self.name}' '{name}'")

        if(result["error"]):
            if("The 'default' project cannot be renamed" in result["data"]):
                raise ProjectDefaultCannotBeRenamedException()
            if("already exists" in result["data"]):
                raise ProjectAlreadyExistsException(name=name)
            if("Only empty projects can be renamed" in result["data"]):
                raise ProjectIsInUseException()
            raise ProjectException(result["data"])

        self.attributes["name"] = name