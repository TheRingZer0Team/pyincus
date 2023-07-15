#!/usr/bin/env python3
import yaml

from ._models import Model

from lxd.exceptions import  NetworkACLException,\
                            NetworkACLAlreadyExistsException,\
                            NetworkACLNotFoundException,\
                            NetworkACLInUseException,\
                            InvalidACLGressException,\
                            InvalidACLRuleActionException,\
                            InvalidACLRuleKeyException,\
                            InvalidACLRuleProtocolException,\
                            InvalidACLRuleStateException,\
                            InvalidDescriptionException,\
                            MissingProtocolException

class NetworkACL(Model):
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
    def possibleActions(self):
        return ["allow", "reject", "drop"]

    @property
    def possibleStates(self):
        return ["enabled", "disabled", "logged"]

    @property
    def possibleProtocols(self):
        return ["icmp4", "icmp6", "tcp", "udp"]

    @property
    def possibleRuleKeys(self):
        return ["action","state","description","source","destination","protocol","source_port","destination_port","icmp_type","icmp_code"]

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
    def egress(self):
        return self.get(name=self.name).attributes["egress"]

    @egress.setter
    def egress(self, value):
        self.save(egress=value)

    @property
    def ingress(self):
        return self.get(name=self.name).attributes["ingress"]

    @ingress.setter
    def ingress(self, value):
        self.save(ingress=value)

    @property
    def usedBy(self):
        return self.get(name=self.name).attributes["used_by"]

    def __validateGress(self, gress: list):
        if(not isinstance(gress, list)):
            raise InvalidACLGressException()

        if(gress):
            for g in gress:
                if(not isinstance(g, dict)):
                    raise InvalidACLGressException()

                if(not "action" in g or not isinstance(g["action"], str)):
                    raise InvalidACLRuleActionException(allowed=self.possibleActions)

                if(not g["action"] in self.possibleActions):
                    raise InvalidACLRuleActionException(allowed=self.possibleActions, action=g["action"])

                if(not "state" in g or not isinstance(g["state"], str)):
                    raise InvalidACLRuleStateException(allowed=self.possibleStates)

                if(not g["state"] in self.possibleStates):
                    raise InvalidACLRuleStateException(allowed=self.possibleStates, state=g["state"])

                if("protocol" in g and not g["protocol"] in self.possibleProtocols):
                    raise InvalidACLRuleProtocolException(allowed=self.possibleProtocols, protocol=g["protocol"])

                if(("source_port" in g or "destination_port" in g) and not "protocol" in g):
                    raise MissingProtocolException()

                for k in g.keys():
                    if(not k in self.possibleRuleKeys):
                        raise InvalidACLRuleKeyException(allowed=self.possibleRuleKeys)

                    if(not isinstance(k, str)):
                        raise InvalidACLRuleKeyException(allowed=self.possibleRuleKeys, key=k)

        return gress

    def create(self, name: str, *, description: str=None, egress: list=None, ingress: list=None):
        self._validateObjectFormat(name)

        self.attributes["name"] = name

        result = self.lxd.run(cmd=f"lxc network acl create --project='{self.project.name}' '{self.remote.name}':'{self.name}'")

        if(result["error"]):
            if("The network ACL already exists" in result["data"]):
                raise NetworkACLAlreadyExistsException(name=name)

            raise NetworkACLException(result["data"])

        try:
            self.save(description=description, egress=egress, ingress=ingress)
        except NetworkACLException as error:
            self.delete()

        return self.get(name=name)

    def delete(self):
        result = self.lxd.run(cmd=f"lxc network acl delete --project='{self.project.name}' '{self.remote.name}':'{self.name}'")

        if(result["error"]):
            if('Network ACL not found' in result["data"]):
                raise NetworkACLNotFoundException()
            if('Cannot delete an ACL that is in use' in result["data"]):
                raise NetworkACLInUseException(name=self.name)

            raise NetworkACLException(result["data"])

    def get(self, name: str):
        acl = self._fetch(name=name)
        
        if(not isinstance(acl, self.__class__)):
            raise NetworkACLNotFoundException()

        return acl

    def rename(self, name: str):
        self._validateObjectFormat(name)

        result = self.lxd.run(cmd=f"lxc network acl rename --project='{self.project.name}' '{self.remote.name}':'{self.name}' '{name}'")

        if(result["error"]):
            if("An ACL by that name exists already" in result["data"]):
                raise NetworkACLAlreadyExistsException(name=name)
            if("Cannot rename an ACL that is in use" in result["data"]):
                raise NetworkACLInUseException(name=name)

        self.attributes["name"] = name

    def save(self, description: str=None, egress: list=None, ingress: list=None):
        if(not description is None):
            if(not isinstance(description, str)):
                raise InvalidDescriptionException()

            self.attributes["description"] = description
        
        if(not egress is None):
            self.attributes["egress"] = self.__validateGress(gress=egress)
        
        if(not ingress is None):
            self.attributes["ingress"] = self.__validateGress(gress=ingress)

        result = self.lxd.run(cmd=f"lxc network acl edit --project='{self.project.name}' '{self.remote.name}':'{self.name}'", input=yaml.safe_dump(self.attributes))

        if(result["error"]):
            if("Error: yaml: unmarshal errors:" in result["data"]):
                raise NetworkACLException("Error: yaml: unmarshal errors:")
            raise NetworkACLException(result["data"])

        self.attributes = self.get(name=self.name).attributes