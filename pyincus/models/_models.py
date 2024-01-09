#!/usr/bin/env python3
import yaml

from pyincus.exceptions import  IncusException,\
                                InvalidIncusObjectNameFormatException
from pyincus.utils import   REGEX_EMPTY_BODY,\
                            REGEX_INCUS_OBJECT_NAME

class Model(object):
    def __init__(self, **kwargs):
        if("parent" in kwargs):
            self.__parent = kwargs["parent"]
            del kwargs["parent"]
        else:
            self.__parent = None
            
        self.__attributes = kwargs

    @property
    def attributes(self):
        return self.__attributes

    @attributes.setter
    def attributes(self, value):
        self.__attributes = value

    @property
    def name(self):
        return self.__attributes["name"]

    @property
    def parent(self):
        return self.__parent

    def list(self, filter: str='', skipValidation=False, **kwargs):
        if(not skipValidation):
            self.validateObjectFormat(filter)

        cmd = None
        
        if(self.__class__.__name__ == "Remote"):
            cmd = f"{self.incus.binaryPath} remote list -fyaml"
        
        if(self.__class__.__name__ == "Project"):
            cmd = f"{self.incus.binaryPath} project list -fyaml '{self.remote.name}':"

        if(self.__class__.__name__ == "Instance"):
            cmd = f"{self.incus.binaryPath} list -fyaml --project='{self.project.name}' '{self.remote.name}':'{filter}'"
        
        if(self.__class__.__name__ == "Network"):
            cmd = f"{self.incus.binaryPath} network list -fyaml --project='{self.project.name}' '{self.remote.name}':"
        
        if(self.__class__.__name__ == "NetworkACL"):
            cmd = f"{self.incus.binaryPath} network acl list -fyaml --project='{self.project.name}' '{self.remote.name}':"
        
        if(self.__class__.__name__ == "NetworkForward"):
            cmd = f"{self.incus.binaryPath} network forward list -fyaml --project='{self.project.name}' '{self.remote.name}':'{filter}'"

        result = self.incus.run(cmd=cmd, **kwargs)

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"])):
                print(f"Retrying listing \"{cmd}\"...")
                return self.list(filter=filter, skipValidation=skipValidation, **kwargs)
            else:
                raise IncusException(result["data"])

        results = yaml.safe_load(result["data"])

        objs = []

        # If it's a dictionary (e.g. for Remotes), change it to a list like the majority.
        # Example: 
        #   {"My-name-1":{"other-attribute":true}, "My-name-2":{"other-attribute":false}}
        #   To:
        #   [{"name":"My-name-1","other-attribute":true},{"name":"My-name-2","other-attribute":false}]
        if(isinstance(results, dict)):
            tmp = []
            for name, obj in results.items():
                obj["name"] = name
                tmp.append(obj)

            results = tmp

        for obj in results:
            objs.append(self.__class__(parent=self.parent, **obj))

        return objs
    
    def _fetch(self, name: str, skipValidation=False, **kwargs):
        if(not skipValidation):
            self.validateObjectFormat(name)

        cmd = None
        
        if(self.__class__.__name__ == "Project"):
            cmd = f"{self.incus.binaryPath} project show '{self.remote.name}':'{name}'"
        
        if(self.__class__.__name__ == "Network"):
            cmd = f"{self.incus.binaryPath} network show --project='{self.project.name}' '{self.remote.name}':'{name}'"
        
        if(self.__class__.__name__ == "NetworkACL"):
            cmd = f"{self.incus.binaryPath} network acl show --project='{self.project.name}' '{self.remote.name}':'{name}'"
        
        if(self.__class__.__name__ == "NetworkForward"):
            cmd = f"{self.incus.binaryPath} network forward show --project='{self.project.name}' '{self.remote.name}':'{name}' '{kwargs['listenAddress']}'"
            del kwargs["listenAddress"]

        result = self.incus.run(cmd=cmd, **kwargs)

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"])):
                print(f"Retrying fetching \"{cmd}\"...")
                return self._fetch(name=name, skipValidation=skipValidation, **kwargs)
            else:
                return result["data"]
        else:
            return self.__class__(parent=self.parent, **yaml.safe_load(result["data"]))

    def exists(self, name: str, **kwargs):
        return isinstance(self._fetch(name=name, **kwargs), self.__class__)

    def refresh(self):
        self.__attributes = self.get(name=self.name).attributes

    def validateObjectFormat(self, *args):
        for arg in args:
            if(arg and (not isinstance(arg, str) or not REGEX_INCUS_OBJECT_NAME.match(arg))):
                raise InvalidIncusObjectNameFormatException(arg)

    def __str__(self):
        return f"{self.__class__.__name__} (name={self.name})"

    def __repr__(self):
        return self.__str__()