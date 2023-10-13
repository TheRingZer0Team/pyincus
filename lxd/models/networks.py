#!/usr/bin/env python3
import yaml

from ._models import Model
from .forwards import NetworkForward

from lxd.exceptions import  NetworkException,\
                            NetworkNotFoundException

class Network(Model):
    def __init__(self, parent: Model=None, name: str=None, **kwargs):
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

    @property
    def possibleNetworkTypes(self):
        return ["bridge", "ovn"]

    @property
    def possibleConfigKeysForBridge(self):
        return ["ipv4", "ipv6"]

    @property
    def possibleConfigKeysForOVN(self):
        return ["network", "ipv4", "ipv6"]

    def get(self, name: str):
        network = self._fetch(name=name)
        
        if(not isinstance(network, self.__class__)):
            raise NetworkNotFoundException()

        return network

    def create(self, name: str, type: str, *, description: str=None, config: dict=None):
        self.validateObjectFormat(name)

        self.attributes["name"] = name

        if(not type in self.possibleNetworkTypes):
            raise NetworkException()

        if(config):
            # Expect to receive {"key":"value"}
            for k, v in config.items():
                if(type == "bridge"):
                    if(not k in self.possibleConfigKeysForBridge):
                        raise NetworkException()
                elif(type == "ovn"):
                    if(not k in self.possibleConfigKeysForOVN):
                        raise NetworkException()
                else:
                    raise NetworkException()

            config = ' '.join([f"{k}={v}" for k,v in config.items()])

        result = self.lxd.run(cmd=f"lxc network create --project='{self.project.name}' '{self.remote.name}':'{self.name}' --type={type} {config if config else ''}")

        if(result["error"]):
            if("The network already exists" in result["data"]):
                raise NetworkAlreadyExistsException(name=name)

            raise NetworkException(result["data"])

        try:
            self.save(description=description)
        except NetworkException as error:
            self.delete()
            raise error

        return self.get(name=name)

    def delete(self):
        result = self.lxd.run(cmd=f"lxc network delete --project='{self.project.name}' '{self.remote.name}':'{self.name}'")

        if(result["error"]):
            if('Network not found' in result["data"]):
                raise NetworkNotFoundException()
            if('Cannot delete a Network that is in use' in result["data"]):
                raise NetworkInUseException(name=self.name)

            raise NetworkException(result["data"])

    def rename(self, name: str):
        self.validateObjectFormat(name)

        result = self.lxd.run(cmd=f"lxc network rename --project='{self.project.name}' '{self.remote.name}':'{self.name}' '{name}'")

        if(result["error"]):
            if("A Network by that name exists already" in result["data"]):
                raise NetworkAlreadyExistsException(name=name)
            if("Cannot rename a Network that is in use" in result["data"]):
                raise NetworkInUseException(name=name)

        self.attributes["name"] = name

    def save(self, *, description: str=None, config: dict=None):
        self.refresh()
        
        if(not description is None):
            if(not isinstance(description, str)):
                raise InvalidDescriptionException()

            self.attributes["description"] = description

        if(config):
            # Expect to receive {"key":"value"}
            for k, v in config.items():
                if(self.type == "bridge"):
                    if(not k in self.possibleConfigKeysForBridge):
                        raise NetworkException()
                elif(self.type == "ovn"):
                    if(not k in self.possibleConfigKeysForOVN):
                        raise NetworkException()
                else:
                    raise NetworkException()

            self.attributes["config"] = config

        result = self.lxd.run(cmd=f"lxc network edit --project='{self.project.name}' '{self.remote.name}':'{self.name}'", input=yaml.safe_dump(self.attributes))

        if(result["error"]):
            if("Error: yaml: unmarshal errors:" in result["data"]):
                raise NetworkException("Error: yaml: unmarshal errors:")
            raise NetworkException(result["data"])

        self.attributes = self.get(name=self.name).attributes