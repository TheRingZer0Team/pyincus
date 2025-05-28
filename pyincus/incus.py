#!/usr/bin/env python3
import subprocess

from pyincus.exceptions import IncusException, IncusVersionException

INCUS_VERSION = "6.12"


class Incus:
    cwd: str | None = None
    binaryPath: str = "/usr/bin/incus"

    @staticmethod
    def run(cmd: str, **kwargs) -> dict:
        result = None
        error = False
        if Incus.cwd and "cwd" not in kwargs:
            kwargs["cwd"] = Incus.cwd
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kwargs)
        if r.returncode != 0:
            result = r.stderr.strip()
            error = True
        else:
            result = r.stdout.strip()
        return {"data": result, "error": error}

    @staticmethod
    def check() -> None:
        result = Incus.run(cmd=f"{Incus.binaryPath} --version")
        if result["error"]:
            raise IncusException(f"Unexpected error: {result['error']}")
        if INCUS_VERSION != result["data"]:
            raise IncusVersionException(
                libVersion=INCUS_VERSION, clientVersion=result["data"]
            )
