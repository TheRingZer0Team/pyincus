#!/usr/bin/env python3
import subprocess

from .exceptions import LXDException,\
                        LXDVersionException
from .models.remotes import Remote

LXD_VERSION = 5.15

class LXD(object):
    def __init__(self, cwd=None):
        self.__cwd = cwd

    @property
    def cwd(self):
        return self.__cwd

    @cwd.setter
    def cwd(self, value):
        self.__cwd = value

    @property
    def remotes(self):
        return Remote(self)

    def run(self, cmd: str, **kwargs):
        result = None
        error = False

        if(self.cwd and not "cwd" in kwargs):
            kwargs["cwd"] = self.cwd

        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kwargs)

        if(r.stderr):
            result = r.stderr.strip()
            error = True
        else:
            result = r.stdout.strip()

        return {"data":result, "error":error}

    def check(self):
        result = self.run(cmd="lxc --version")
        
        if(result["error"]):
            raise LXDException(f"Unexpected error: {result['error']}")

        if(LXD_VERSION != float(result["data"])):
            raise LXDVersionException(libVersion=LXD_VERSION, clientVersion=float(result["data"]))

lxd = LXD()
remotes = lxd.remotes