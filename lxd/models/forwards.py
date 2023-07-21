#!/usr/bin/env python3
import re
import ipaddress

from ._models import Model

from lxd.exceptions import  NetworkForwardException,\
                            NetworkForwardNotFoundException,\
                            InvalidIPAddressException,\
                            InvalidPortProtocolException,\
                            InvalidPortRangeException,\
                            DuplicatePortException,\
                            StartLowerThanEndException,\
                            InvalidTargetPortsException,\
                            NetworkForwardPortNotFoundException,\
                            NetworkForwardPortAlreadyExistsException

REGEX_LIST_OF_PORTS = re.compile(r'^[1-9][0-9]{0,4}(([\-][1-9][0-9]{0,4})?([,][1-9][0-9]{0,4}|$))*$')

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
    def possibleProtocols(self):
        return ["tcp", "udp"]

    @property
    def listenAddress(self):
        return self.attributes["listen_address"]

    @property
    def config(self):
        return self.get(listenAddress=self.listenAddress).attributes["config"]

    @property
    def description(self):
        return self.get(listenAddress=self.listenAddress).attributes["description"]

    @description.setter
    def description(self, value):
        self.save(description=value)

    @property
    def ports(self):
        return self.get(listenAddress=self.listenAddress).attributes["ports"]

    def validatePortList(self, ports: "str | int"):
        tmpPortRanges = []
        
        if(isinstance(ports, int)):
            if(ports < 1 or ports > 65535):
                raise InvalidPortRangeException(ports=ports)
            tmpPortRanges.append(ports)
        else:
            if(not REGEX_LIST_OF_PORTS.match(ports)):
                raise InvalidPortRangeException(ports=ports)

            if(ports.count(",") > 0):
                tmpPorts = ports.split(",")

                for port in tmpPorts:
                    if(port.find("-") > -1):
                        start, end = [int(p) for p in port.split("-")]
                        if(start >= end):
                            raise StartLowerThanEndException(ports=port)

                        for i in range(start, end+1):
                            if(i in tmpPortRanges):
                                raise DuplicatePortException(ports=ports, duplicate=i)

                        tmpPortRanges.extend(range(start, end+1))
                    else:
                        port = int(port)
                        if(port in tmpPortRanges):
                            raise DuplicatePortException(ports=ports, duplicate=port)
                        
                        tmpPortRanges.append(port)
            elif(ports.find("-") > -1):
                start, end = [int(p) for p in ports.split("-")]
                if(start >= end):
                    raise StartLowerThanEndException(ports=ports)
                
                tmpPortRanges.extend(range(start, end+1))

        return tmpPortRanges

    def addPort(self, *, protocol: str, listenPorts: str, targetAddress: str, targetPorts: str=None):
        if(not isinstance(protocol, str) or not protocol in self.possibleProtocols):
            raise InvalidPortProtocolException(allowed=self.possibleProtocols, protocol=protocol)

        if(not isinstance(targetAddress, str)):
            raise InvalidIPAddressException(targetAddress)

        try:
            ipaddress.ip_address(targetAddress)
        except:
            raise InvalidIPAddressException(targetAddress)

        if(listenPorts is None):
            raise InvalidPortRangeException(ports=listenPorts)

        c1 = len(self.validatePortList(ports=listenPorts))
    
        if(not targetPorts is None):
            c2 = len(self.validatePortList(ports=targetPorts))

            if(c2 != c1):
                raise InvalidTargetPortsException(listenPorts=listenPorts, targetPorts=targetPorts)

        result = self.lxd.run(cmd=f"lxc network forward port add --project='{self.project.name}' '{self.remote.name}':'{self.network.name}' '{self.listenAddress}' '{protocol}' '{listenPorts}' '{targetAddress}'{f' {chr(39)}{targetPorts}{chr(39)} ' if targetPorts else ''}")

        if(result["error"]):
            if("Duplicate listen port " in result["data"] and f"for protocol \"{protocol}\" in port specification" in result["data"]):
                port = result["data"].split("Duplicate listen port ")[1].split(f" for protocol \"{protocol}\" in port specification")[0]
                raise NetworkForwardPortAlreadyExistsException(protocol=protocol, port=port)
            raise NetworkForwardException(result["data"])

    def removePort(self, *, protocol: str, listenPorts: str):
        if(protocol is None):
            raise InvalidPortProtocolException(allowed=self.possibleProtocols)
        
        if(not protocol in self.possibleProtocols):
            raise InvalidPortProtocolException(allowed=self.possibleProtocols, protocol=protocol)

        if(not listenPorts is None):
            self.validatePortList(ports=listenPorts)

        result = self.lxd.run(cmd=f"lxc network forward port remove --project='{self.project.name}' '{self.remote.name}':'{self.network.name}' '{self.listenAddress}' '{protocol}' '{listenPorts}'")

        if(result["error"]):
            if("No matching port(s) found" in result["data"]):
                raise NetworkForwardPortNotFoundException(ports=listenPorts)
            raise NetworkForwardException(result["data"])

    def list(self):
        return super().list(filter=self.network.name)

    def get(self, listenAddress):
        if(not isinstance(listenAddress, str)):
            raise InvalidIPAddressException(listenAddress)

        try:
            ipaddress.ip_address(listenAddress)
        except:
            raise InvalidIPAddressException(listenAddress)

        forward = self._fetch(name=self.network.name, listenAddress=listenAddress, skipValidation=True)
        
        if(not isinstance(forward, self.__class__)):
            raise NetworkForwardNotFoundException()

        return forward

    def refresh(self):
        self.attributes = self.get(listenAddress=self.listenAddress).attributes

    def save(self, description: str=None):
        self.refresh()

        if(not description is None):
            if(not isinstance(description, str)):
                raise InvalidDescriptionException()

            self.attributes["description"] = description
        
        result = self.lxd.run(cmd=f"lxc network forward edit --project='{self.project.name}' '{self.remote.name}':'{self.network.name}' '{self.listenAddress}'", input=yaml.safe_dump(self.attributes))

        if(result["error"]):
            if("Error: yaml: unmarshal errors:" in result["data"]):
                raise NetworkForwardException("Error: yaml: unmarshal errors:")
            raise NetworkForwardException(result["data"])

        self.attributes = self.get(listenAddress=self.listenAddress).attributes

    def __str__(self):
        return f"{self.__class__.__name__} (config={self.config}, ports={self.ports})"