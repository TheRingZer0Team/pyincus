#!/usr/bin/env python3
from ._models import Model
from .forwards import NetworkForward

from lxd.exceptions import  NetworkException,\
                            NetworkNotFoundException

class Network(Model):
    def __init__(self, parent, name: str=None, **kwargs):
        super().__init__(parent=parent, name=name, **kwargs)

    @property
    def lxd(self):
        return self.remote.parent

    @property
    def remote(self):
        return self.parent.remote

    @property
    def project(self):
        return self.parent

    @property
    def forwards(self):
        return NetworkForward(self)

    @property
    def config(self): # Need setter
        return self.get(name=self.name).attributes["config"]

    @property
    def description(self): # Need setter
        return self.get(name=self.name).attributes["description"]

    @property
    def type(self):
        return self.get(name=self.name).attributes["type"]

    @property
    def usedBy(self):
        return self.get(name=self.name).attributes["used_by"]

    @property
    def managed(self):
        return self.get(name=self.name).attributes["managed"]

    @property
    def status(self):
        return self.get(name=self.name).attributes["status"]

    @property
    def locations(self):
        return self.get(name=self.name).attributes["locations"]

    def get(self, name: str):
        network = self._fetch(name=name)
        
        if(not isinstance(network, self.__class__)):
            raise NetworkNotFoundException()

        return network