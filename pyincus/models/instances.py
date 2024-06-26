#!/usr/bin/env python3
import yaml
import textwrap

from pyincus.utils import   REGEX_DEVICE_NOT_FOUND,\
                            REGEX_EMPTY_BODY,\
                            REGEX_IMAGE_NAME,\
                            REGEX_NETWORK_NOT_FOUND_COPY,\
                            isTrue

from ._models import Model

from pyincus.exceptions import  DeviceNotFoundException,\
                                InstanceAlreadyExistsException,\
                                InstanceException,\
                                InstanceExecFailedException,\
                                InstanceIsAlreadyStoppedException,\
                                InstanceIsNotRunningException,\
                                InstanceIsPausedException,\
                                InstanceIsRunningException,\
                                InstanceNotFoundException,\
                                InstanceTimeoutExceededException,\
                                InvalidDescriptionException,\
                                InvalidImageNameFormatException,\
                                NameAlreadyInUseException,\
                                NetworkNotFoundException

class Instance(Model):
    def __init__(self, parent: Model=None, name: str=None, **kwargs):
        super().__init__(parent=parent, name=name, **kwargs)

    @property
    def incus(self):
        return self.remote.parent

    @property
    def remote(self):
        return self.parent.remote

    @property
    def project(self):
        return self.parent

    @property
    def architecture(self):
        return self.get(name=self.name).attributes["architecture"]

    @property
    def config(self):
        return self.get(name=self.name).attributes["config"]

    @config.setter
    def config(self, value):
        self.save(config=value)

    @property
    def devices(self):
        return self.get(name=self.name).attributes["devices"]

    @devices.setter
    def devices(self, value):
        self.save(devices=value)

    @property
    def ephemeral(self):
        return self.get(name=self.name).attributes["ephemeral"]

    @property
    def profiles(self):
        return self.get(name=self.name).attributes["profiles"]

    @profiles.setter
    def profiles(self, value):
        self.save(profiles=value)

    @property
    def stateful(self):
        return self.get(name=self.name).attributes["stateful"]

    @property
    def description(self):
        return self.get(name=self.name).attributes["description"]

    @description.setter
    def description(self, value):
        self.save(description=value)

    @property
    def createdAt(self):
        return self.get(name=self.name).attributes["created_at"]

    @property
    def expandedConfig(self):
        return self.get(name=self.name).attributes["expanded_config"]

    @property
    def expandedDevices(self):
        return self.get(name=self.name).attributes["expanded_devices"]

    @property
    def status(self):
        return self.get(name=self.name).attributes["status"]

    @property
    def statusCode(self):
        return self.get(name=self.name).attributes["status_code"]

    @property
    def lastUsedAt(self):
        return self.get(name=self.name).attributes["last_used_at"]

    @property
    def location(self):
        return self.get(name=self.name).attributes["location"]

    @property
    def type(self):
        return self.get(name=self.name).attributes["type"]

    @property
    def backups(self):
        return self.get(name=self.name).attributes["backups"]

    @property
    def state(self):
        return self.get(name=self.name).attributes["state"]

    @property
    def snapshots(self):
        return self.get(name=self.name).attributes["snapshots"]

    def validateImageName(self, image: str):
        if(not REGEX_IMAGE_NAME.match(image)):
            raise InvalidImageNameFormatException(image)

    def _fetch(self, name: str):
        i = None

        self.validateObjectFormat(name)

        instances = self.list(filter=f"^{name}$", skipValidation=True)

        if(len(instances) > 0):
            i = instances[0]

        return i

    def get(self, name: str):
        instance = self._fetch(name=name)
        
        if(instance is None):
            raise InstanceNotFoundException()

        return instance

    def copy(self, source: str, name: str=None, *, snapshotName: str=None, remoteSource: str=None, remoteDestination: str=None, projectSource: str=None, projectDestination: str=None, config: dict=None, device: dict=None, profile: str=None, mode: str='pull', storage: str=None, allowInconsistent: bool=False, instanceOnly: bool=False, noProfile: bool=False, refresh: bool=False, stateless: bool=False):
        self.validateObjectFormat(source, name, snapshotName, remoteSource, remoteDestination, projectSource, projectDestination, profile, storage)

        if(name is None and not refresh):
            raise InstanceException("""if(name is None and not refresh):""")

        if(config):
            # Expect to receive {"key":"value"}
            config = ' '.join([f"-c {k}={v}" for k,v in config.items()])

        if(device):
            # Expect to receive this format {"eth0":{"key":"value"},"root":{"key":"value"}}
            for n, values in device.items():
                device = ' '.join([f"-d {n},{k}={v}" for k,v in values.items()])

        if(not mode in ["pull", "push", "relay"]):
            raise InstanceException("""if(not mode in ["pull", "push", "relay"]):""")

        if(remoteSource is None):
            remoteSource = self.remote.name

        if(remoteDestination is None):
            remoteDestination = self.remote.name

        if(projectSource is None):
            projectSource = self.project.name

        if(projectDestination is None):
            projectDestination = self.project.name

        result = self.incus.run(cmd=
            textwrap.dedent(
                f"""\
                    {self.incus.binaryPath} copy 
                    {f"'{remoteSource}':" if remoteSource else ""}'{source}'{f"/'{snapshotName}'" if snapshotName else ""} 
                    {f"'{remoteDestination}':" if remoteDestination else ""}'{name}' 
                    {f"--project='{projectSource}' " if projectSource else ""} 
                    {config if config else ""} 
                    {device if device else ""} 
                    {f"--mode='{mode}' " if mode else ""}
                    {f"--profile='{profile}' " if not noProfile and profile else ""}
                    {f"--storage='{storage}' " if storage else ""}
                    {f"--target-project='{projectDestination}' " if projectDestination else ""}
                    {"--allow-inconsistent " if allowInconsistent else ""}
                    {"--instance-only " if instanceOnly else ""}
                    {"--no-profile " if noProfile else ""}
                    {"--stateless " if stateless else ""}
                """
            ).replace("\n","")
        )

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                print(f"Command \"copy\" broke, attempt to get the content...")
                return self.get(name=name)

            match = REGEX_DEVICE_NOT_FOUND.search(result["data"])
            if(match):
                raise DeviceNotFoundException(match.group('device'))

            match = REGEX_NETWORK_NOT_FOUND_COPY.search(result["data"])
            if(match):
                raise NetworkNotFoundException(match.group('network'))

            if('This "instances" entry already exists' in result["data"]):
                raise InstanceAlreadyExistsException(name=name)

            raise InstanceException(result["data"])

        return Instance(parent=self.parent, name=name)

    def delete(self, *, force: bool=True):
        if(force and "security.protection.delete" in self.config and isTrue(self.config["security.protection.delete"])):
            tmpConfig = self.config
            tmpConfig["security.protection.delete"] = False
            self.config = tmpConfig

        result = self.incus.run(cmd=f"{self.incus.binaryPath} delete {'--force ' if force else ''}--project='{self.project.name}' '{self.remote.name}':'{self.name}'")

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                if(self.exists(name=self.name)):
                    self.delete(force=force)
            else:
                if('Instance not found' in result["data"]):
                    raise InstanceNotFoundException()

                raise InstanceException(result["data"])

    def exec(self, cmd: str):
        cmd = cmd.replace("'","'\"'\"'")
        result = self.incus.run(cmd=f"{self.incus.binaryPath} exec --project='{self.project.name}' '{self.remote.name}':'{self.name}' -- bash -c '{cmd}'")

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                print(f"Command \"exec\" broke, it should have worked but there is no way of knowing.")
            else:
                if('Instance not found' in result["data"]):
                    raise InstanceNotFoundException()
                if('Failed to retrieve PID of executing child process' in result["data"]):
                    raise InstanceExecFailedException()
                if('Command not found' in result["data"]):
                    raise InstanceExecFailedException()
                if('Instance is not running' in result["data"]):
                    raise InstanceIsNotRunningException()
                if('Instance is frozen' in result["data"]):
                    raise InstanceIsPausedException()

                raise InstanceException(result["data"])

        return result["data"]

    def init(self, image: str, name: str, *, remoteSource: str=None, config: dict=None, device: dict=None, profile: str=None, network: str=None, storage: str=None, empty: bool=False, noProfile: bool=False, vm: bool=False):
        self.validateObjectFormat(name, remoteSource, profile, network, storage)
        self.validateImageName(image)

        if(config):
            # Expect to receive {"key":"value"}
            config = ' '.join([f"-c {k}={v}" for k,v in config.items()])

        if(device):
            # Expect to receive this format {"eth0":{"key":"value"},"root":{"key":"value"}}
            for n, values in device.items():
                device = ' '.join([f"-d {n},{k}={v}" for k,v in values.items()])

        result = self.incus.run(cmd=
            textwrap.dedent(
                f"""\
                    {self.incus.binaryPath} init 
                    {f"'{remoteSource}':" if remoteSource else ""}'{image}' 
                    '{self.remote.name}':'{name}' 
                    --project='{self.project.name}' 
                    {config if config else ""} 
                    {device if device else ""} 
                    {f"--network='{network}' " if network else ""}
                    {f"--profile='{profile}' " if not noProfile and profile else ""}
                    {f"--storage='{storage}' " if storage else ""}
                    {"--empty " if empty else ""}
                    {"--no-profile " if noProfile else ""}
                    {"--vm " if vm else ""}
                """
            ).replace("\n","")
        )

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                print(f"Command \"init\" broke, attempt to get the content...")
                return self.get(name=name)
            if('This "instances" entry already exists' in result["data"]):
                raise InstanceAlreadyExistsException(name=name)
            raise InstanceException(result["data"])
        
        return Instance(parent=self.parent, name=name)

    def launch(self, image: str, name: str, *, remoteSource: str=None, config: dict=None, device: dict=None, profile: str=None, network: str=None, storage: str=None, empty: bool=False, noProfile: bool=False, vm: bool=False):
        self.validateObjectFormat(name, remoteSource, profile, network, storage)
        self.validateImageName(image)

        if(config):
            # Expect to receive {"key":"value"}
            config = ' '.join([f"-c {k}={v}" for k,v in config.items()])

        if(device):
            # Expect to receive this format {"eth0":{"key":"value"},"root":{"key":"value"}}
            for n, values in device.items():
                device = ' '.join([f"-d {n},{k}={v}" for k,v in values.items()])

        result = self.incus.run(cmd=
            textwrap.dedent(
                f"""\
                    {self.incus.binaryPath} launch 
                    {f"'{remoteSource}':" if remoteSource else ""}'{image}' 
                    '{self.remote.name}':'{name}' 
                    --project='{self.project.name}' 
                    {config if config else ""} 
                    {device if device else ""} 
                    {f"--network='{network}' " if network else ""}
                    {f"--profile='{profile}' " if not noProfile and profile else ""}
                    {f"--storage='{storage}' " if storage else ""}
                    {"--empty " if empty else ""}
                    {"--no-profile " if noProfile else ""}
                    {"--vm " if vm else ""}
                """
            ).replace("\n","")
        )

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                print(f"Command \"launch\" broke, attempt to get the content...")
                return self.get(name=name)
            if('This "instances" entry already exists' in result["data"]):
                raise InstanceAlreadyExistsException(name=name)
            raise InstanceException(result["data"])

        return Instance(parent=self.parent, name=name)

    def pause(self, timeout: int=None):
        result = self.incus.run(cmd=f"{self.incus.binaryPath} pause --project='{self.project.name}' '{self.remote.name}':'{self.name}'", timeout=timeout)

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                if(self.status.lower() != "frozen"):
                    print(f"Command \"pause\" broke, attempt to pause again...")
                    self.pause(timeout=timeout)
            else:
                if("Error: The instance isn't running" == result["data"]):
                    raise InstanceIsNotRunningException()
                raise InstanceException(result["data"])

    def move(self, source: str, *, name: str=None, remoteSource: str=None, remoteDestination: str=None, projectSource: str=None, projectDestination: str=None, config: dict=None, device: dict=None, profile: str=None, mode: str='pull', storage: str=None, allowInconsistent: bool=False, instanceOnly: bool=False, noProfile: bool=False, stateless: bool=False):
        self.validateObjectFormat(source, name, remoteSource, remoteDestination, projectSource, projectDestination, profile, storage)

        if(config):
            # Expect to receive {"key":"value"}
            config = ' '.join([f"-c {k}={v}" for k,v in config.items()])

        if(device):
            # Expect to receive this format {"eth0":{"key":"value"},"root":{"key":"value"}}
            for n, values in device.items():
                device = ' '.join([f"-d {n},{k}={v}" for k,v in values.items()])

        if(not mode in ["pull", "push", "relay"]):
            raise InstanceException("""if(not mode in ["pull", "push", "relay"]):""")

        if(remoteSource is None):
            remoteSource = self.remote.name

        if(remoteDestination is None):
            remoteDestination = self.remote.name

        if(projectSource is None):
            projectSource = self.project.name

        if(projectDestination is None):
            projectDestination = self.project.name

        if(name is None):
            if(projectDestination != projectSource):
                name = source
            else:
                raise InstanceException(f"Name must be set when the source project ({projectSource}) and destination project ({projectDestination}) are not equal.")

        result = self.incus.run(cmd=
            textwrap.dedent(
                f"""\
                    {self.incus.binaryPath} move 
                    {f"'{remoteSource}':" if remoteSource else ""}'{source}' 
                    {f"'{remoteDestination}':" if remoteDestination else ""}'{name}' 
                    {f"--project='{projectSource}' " if projectSource else ""} 
                    {config if config else ""} 
                    {device if device else ""} 
                    {f"--mode='{mode}' " if mode else ""}
                    {f"--profile='{profile}' " if not noProfile and profile else ""}
                    {f"--storage='{storage}' " if storage else ""}
                    {f"--target-project='{projectDestination}' " if projectDestination else ""}
                    {"--allow-inconsistent " if allowInconsistent else ""}
                    {"--instance-only " if instanceOnly else ""}
                    {"--no-profile " if noProfile else ""}
                    {"--stateless " if stateless else ""}
                """
            ).replace("\n","")
        )

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                print(f"Command \"copy\" broke, attempt to get the content...")
                return self.get(name=name)

            match = REGEX_DEVICE_NOT_FOUND.search(result["data"])
            if(match):
                raise DeviceNotFoundException(match.group('device'))

            match = REGEX_NETWORK_NOT_FOUND_COPY.search(result["data"])
            if(match):
                raise NetworkNotFoundException(match.group('network'))

            if('This "instances" entry already exists' in result["data"]):
                raise InstanceAlreadyExistsException(name=name)

            raise InstanceException(result["data"])

        return Instance(parent=self.parent, name=name)

    def rename(self, name: str):
        self.validateObjectFormat(name)

        result = self.incus.run(cmd=f"{self.incus.binaryPath} rename --project='{self.project.name}' '{self.remote.name}':'{self.name}' '{name}'")

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                if(self.exists(name=self.name)):
                    if(self.status.lower() == "running"):
                        raise InstanceIsRunningException()
                    else:
                        raise NameAlreadyInUseException(name)
            else:
                if(result["data"].startswith("Error: Name \"") and result["data"].endswith("\" already in use")):
                    raise NameAlreadyInUseException(result["data"][len("Error: Name \""):len("\" already in use")+1])
                if("Error: Renaming of running instance not allowed" == result["data"]):
                    raise InstanceIsRunningException()

        self.attributes["name"] = name

    def restart(self, *, force: bool=True, timeout: int=-1):
        result = self.incus.run(cmd=f"{self.incus.binaryPath} restart {'--force ' if force else ''}--timeout={timeout} --project='{self.project.name}' '{self.remote.name}':'{self.name}'")

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                print(f"Command \"restart\" broke, it should have worked but there is no way of knowing.")
            else:
                if("Error: The instance is already stopped" == result["data"]):
                    raise InstanceIsAlreadyStoppedException()
                if("context deadline exceeded" in result["data"]):
                    raise InstanceTimeoutExceededException()
                raise InstanceException(result["data"])

    def restore(self, name: str, *, stateful: bool=False):
        self.validateObjectFormat(name)

        result = self.incus.run(cmd=f"{self.incus.binaryPath} snapshot restore {'--stateful ' if stateful else ''}--project='{self.project.name}' '{self.remote.name}':'{self.name}' {name}")

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                print(f"Command \"restore\" broke, it should have worked but since there is no way of knowing and that it should be fine to restore again, let's do it again.")
                self.restore(name=name, stateful=stateful)
            else:
                raise InstanceException(result["data"])

    def start(self):
        result = self.incus.run(cmd=f"{self.incus.binaryPath} start --project='{self.project.name}' '{self.remote.name}':'{self.name}'")

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                if(self.status.lower() != 'running'):
                    print(f"Command \"start\" broke, retrying to start...")
                    self.start()
            else:
                raise InstanceException(result["data"])

    def stop(self, *, force: bool=True, timeout: int=-1):
        result = self.incus.run(cmd=f"{self.incus.binaryPath} stop {'--force ' if force else ''}--timeout={timeout} --project='{self.project.name}' '{self.remote.name}':'{self.name}'")

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                if(self.status.lower() != "stopped"):
                    print(f"Command \"stop\" broke, retrying to stop...")
                    self.stop(force=force, timeout=timeout)
            else:
                if("Error: The instance is already stopped" == result["data"]):
                    raise InstanceIsAlreadyStoppedException()
                if("Error: The instance isn't running" == result["data"]):
                    raise InstanceIsNotRunningException()
                if("context deadline exceeded" in result["data"]):
                    raise InstanceTimeoutExceededException()
                raise InstanceException(result["data"])

    def snapshot(self, name: str, *, reuse: bool=False, stateful: bool=False):
        self.validateObjectFormat(name)

        result = self.incus.run(cmd=f"{self.incus.binaryPath} snapshot create {'--reuse ' if reuse else ''}{'--stateful ' if stateful else ''}--project='{self.project.name}' '{self.remote.name}':'{self.name}' {name}")

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                found = False
                for snapshot in self.snapshots:
                    if(snapshot["name"] == name):
                        found = True
                if(not found):
                    print(f"Command \"snapshot\" broke, retrying to create...")
                    self.snapshot(name=name, reuse=reuse, stateful=stateful)
            else:
                raise InstanceException(result["data"])

    def save(self, config: dict=None, devices: dict=None, profiles: list=None, description: str=None):
        self.refresh()

        if(not description is None):
            if(not isinstance(description, str)):
                raise InvalidDescriptionException()

            self.attributes["description"] = description
            
        if(not config is None):
            if(not isinstance(config, dict)):
                raise InstanceException("config must be a dictionary.")

            tmpConfig = self.config

            for k, v in config.items():
                if(not k in self.expandedConfig):
                    raise InstanceException(f"config \"{k}\" not in expanded_config.")

                tmpConfig[k] = v

            self.attributes["config"] = tmpConfig

        if(not devices is None):
            if(not isinstance(devices, dict)):
                raise Instancexception("devices must be a dictionary.")

            tmpDevices = {}

            for k, v in devices.items():
                if(not k in self.expandedDevices):
                    raise InstanceException(f"device \"{k}\" not in expanded_devices.")

                tmpDevices[k] = self.expandedDevices[k]
                tmpDevices[k].update(v)

            self.attributes["devices"] = tmpDevices

        if(not profiles is None):
            if(not isinstance(profiles, list)):
                raise InstanceException("profiles must be a list containing strings.")

            self.validateObjectFormat(*profiles)

        result = self.incus.run(cmd=f"{self.incus.binaryPath} config edit --project='{self.project.name}' '{self.remote.name}':'{self.name}'", input=yaml.safe_dump(self.attributes))

        if(result["error"]):
            if(REGEX_EMPTY_BODY.search(result["data"]) or "Operation not found" in result["data"]):
                if(self.attributes != self.get(name=self.name).attributes):
                    print(f"Command \"save\" broke, retrying to save...")
                    self.save(config=config, devices=devices, profiles=profiles, description=description)
            else:
                if("Error: yaml: unmarshal errors:" in result["data"]):
                    raise InstanceException("Error: yaml: unmarshal errors:")
                if("Missing device type in config" in result["data"]):
                    raise DeviceNotFoundException()
                raise InstanceException(result["data"])

        self.attributes = self.get(name=self.name).attributes