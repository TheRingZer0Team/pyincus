#!/usr/bin/env python3
import subprocess

from .exceptions import IncusException,\
                        IncusVersionException
from .models.remotes import Remote

INCUS_VERSION = 0.4

class Incus(object):
    def __init__(self, cwd=None, binaryPath='/usr/bin/incus'):
        self.__cwd = cwd
        self.__binaryPath = binaryPath

    @property
    def cwd(self):
        return self.__cwd

    @cwd.setter
    def cwd(self, value):
        self.__cwd = value

    @property
    def binaryPath(self):
        return self.__binaryPath

    @binaryPath.setter
    def binaryPath(self, value):
        self.__binaryPath = value

    @property
    def remotes(self):
        return Remote(self)

    def run(self, cmd: str, **kwargs):
        result = None
        error = False

        if(self.cwd and not "cwd" in kwargs):
            kwargs["cwd"] = self.cwd

        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kwargs)

        if(r.returncode != 0):
            result = r.stderr.strip()
            error = True
        else:
            result = r.stdout.strip()

        return {"data":result, "error":error}

    def check(self):
        result = self.run(cmd=f"{self.binaryPath} --version")
        
        if(result["error"]):
            raise IncusException(f"Unexpected error: {result['error']}")

        if(INCUS_VERSION != float(result["data"])):
            raise IncusVersionException(libVersion=INCUS_VERSION, clientVersion=float(result["data"]))

incus = Incus()
remotes = incus.remotes