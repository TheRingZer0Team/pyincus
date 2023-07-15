#!/usr/bin/env python3
from ._models import Model

from lxd.exceptions import  NetworkForwardException,\
                            NetworkForwardNotFoundException

class NetworkForward(Model):
    def __init__(self, parent, name: str=None, **kwargs):
        super().__init__(parent=parent, name=name, **kwargs)

    @property
    def lxd(self):
        return self.remote.parent

    @property
    def remote(self):
        return self.parent.project.remote

    @property
    def project(self):
        return self.parent.project

    @property
    def network(self):
        return self.parent

    @property
    def possibleProtocol(self):
        return ["tcp", "udp"]

    @property
    def listenAddress(self):
        return self.attributes["listen_address"]

    @property
    def config(self):
        return self.get(name=self.name).attributes["config"]

    @property
    def description(self):
        return self.get(name=self.name).attributes["description"]

    @description.setter
    def description(self, value):
        self.save(description=value)

    @property
    def ports(self):
        return self.get(name=self.name).attributes["ports"]

    def addPort(self, *, protocol, listenPorts, targetAddress, targetPort=None):
        #TODO: validate ports, addresses
        if(not protocol is None and not protocol in self.possibleProtocols):
            raise NetworkForwardException()

        result = self.lxd.run(cmd=f"lxc network forward port add --project='{self.project.name}' '{self.remote.name}':'{self.network.name}' '{self.listenAddress}' '{protocol}' '{listenPorts}' '{targetAddress}'{f' {chr(39)}{targetPort}{chr(39)} ' if targetPort else ''}")

        if(result["error"]):
            raise NetworkForwardException(result["data"])

    def remotePort(self, *, protocol, listenPorts):
        #TODO: validate ports
        if(not protocol is None and not protocol in self.possibleProtocols):
            raise NetworkForwardException()

        result = self.lxd.run(cmd=f"lxc network forward port remove --project='{self.project.name}' '{self.remote.name}':'{self.network.name}' '{self.listenAddress}' '{protocol}' '{listenPorts}'")

        if(result["error"]):
            raise NetworkForwardException(result["data"])

    def list(self):
        return super().list(filter=self.network.name)

    def get(self, listenAddress):
        #TODO: validate listenAddress
        forward = self._fetch(name=self.network.name, listenAddress=listenAddress, skipValidation=True)
        
        if(not isinstance(forward, self.__class__)):
            raise NetworkForwardNotFoundException()

        return forward

    def save(self, description: str=None):
        if(not description is None):
            if(not isinstance(description, str)):
                raise InvalidDescriptionException()

            self.attributes["description"] = description
        
        result = self.lxd.run(cmd=f"lxc network forward edit --project='{self.project.name}' '{self.remote.name}':'{self.network.name}' '{self.listenAddress}'", input=yaml.safe_dump(self.attributes))

        if(result["error"]):
            if("Error: yaml: unmarshal errors:" in result["data"]):
                raise NetworkForwardException("Error: yaml: unmarshal errors:")
            raise NetworkForwardException(result["data"])

        self.attributes = self.get(name=self.name).attributes

    def __str__(self):
        return f"{self.__class__.__name__} (config={self.config}, ports={self.ports})"