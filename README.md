# pyincus

## Description

This library was written to be able to use Incus with Python. There are some solutions out there but they either lack features or they are limiting in what our projects requires. 

The library uses the Incus client installed on your machine to work. Meaning that you need to manually create remotes in your Incus for this library to work. This way, it's possible to use this library for remotes that requires more than just a certificate or a password. 

## Usage

### Incus

The object `Incus` contains the methods to run commands on the system. It is also there that you can set the variable `cwd` in case you are running your code in a directory where you don't have the permission to write. You can also use the `check()` method to see if the library match the version of Incus.

#### Methods

* _check()_ - Check Incus version. Raises `IncusVersionException` if the version does not match.
* _run(cmd: str, \*\*kwargs)_ - Execute `cmd` on the operation system and returns a dictionary `{"data":result, "error":error}`. `kwargs` is passed to `subprocess.run()`.

#### Attributes

* _cwd_ - Subprocess variable. Changes the execution path.
* _remotes_ - Empty instance of `Remote` object to gain access to methods like `list`, `get` and `exists`.

#### Examples

```python
import pyincus

pyincus.incus.cwd = "/"
pyincus.incus.check()
```

### Model

Every object following this one inherite from `Model` and therefore can use any attribute or method from this object unless overridden.

#### Methods

* _exists(name: str)_ - Return `True` if the object exists and `False` if not.
* _list(filter: str)_ - `filter` is only used for `Instance` and `NetworkForward`. Returns a list of objects depending on the object that used this method.
* _refresh()_ - Refresh the attributes.

#### Attributes

* _attributes_ - Contains every variable from Incus object.
* _name_ - Read only attribute associated to the Incus object.
* _parent_ - Read only attribute associated to the Incus object.

### Remote

#### Methods

* _get(name: str)_ - Get a specific `Remote` object.
* _rename(name: str)_ - Equivalent to `incus remote rename`

#### Attributes

* _incus_ - `Incus` object.
* _projects_ - Empty instance of `Project` object to gain access to methods like `list`, `get` and `exists`.
* _addr_ - Read only attribute associated to the Incus object. Address of the remote object.
* _project_ - Read only attribute associated to the Incus object. Default project name for the remote.
* _public_ - Read only attribute associated to the Incus object. If the remote is public or private.

#### Examples

```python
import pyincus

# List remotes locally installed on your computer.
print(pyincus.remotes.list())

# Check if the remote exists
if(pyincus.remotes.exists(name="local")):
	# Fetch the remote
	remote = pyincus.remotes.get(name="local")

	print(remote.name)
```

### Project

#### Methods

* _get(name: str)_ - Get a specific `Project` object.
* _rename(name: str)_ - Equivalent to `incus project rename`

#### Attributes

* _acls_ - 
* _incus_ - `Incus` object.
* _remote_ - `Remote` object.
* _instances_ - Empty instance of `Instance` object to gain access to methods like `list`, `get` and `exists`.
* _networks_ - Empty instance of `Network` object to gain access to methods like `list`, `get` and `exists`.
* _config_ - Attribute associated to the Incus object. Project configuration.
* _description_ - Attribute associated to the Incus object. Project description.
* _usedBy_ - Read only attribute associated to the Incus object. Project used by what other object.

#### Examples

```python
import pyincus

remote = pyincus.remotes.get(name="local")

# List projects of a given remote.
print(remote.projects.list())

# Check if the project exists
if(remote.projects.exists(name="default")):
	# Fetch the project
	project = remote.projects.get(name="default")

	print(project.name)
```

### Instance

#### Methods

* _get(name: str)_ - Get a specific `Instance` object.
* _validateImageName(image: str)_ - Used to validate the image name for Incus compatibility.
* _copy(source: str, name: str=None, *, snapshotName: str=None, remoteSource: str=None, remoteDestination: str=None, projectSource: str=None, projectDestination: str=None, config: dict=None, device: dict=None, profile: str=None, mode: str='pull', storage: str=None, allowInconsistent: bool=False, empty: bool=False, instanceOnly: bool=False, noProfile: bool=False, refresh: bool=False, stateless: bool=False, vm: bool=False)_ -  Equivalent to `incus copy` command.
* _delete(force: bool=True)_ - Equivalent to `incus delete` command.
* _exec(cmd: str)_ - Equivalent to `incus exec` command.
* _init(image: str, name: str, *, remoteSource: str=None, config: dict=None, device: dict=None, profile: str=None, network: str=None, storage: str=None, empty: bool=False, noProfile: bool=False, vm: bool=False)_ - Equivalent to `incus init` command.
* _launch(image: str, name: str, *, remoteSource: str=None, config: dict=None, device: dict=None, profile: str=None, network: str=None, storage: str=None, empty: bool=False, noProfile: bool=False, vm: bool=False)_ - Equivalent to `incus launch` command.
* _pause()_ - Equivalent to `incus pause` command.
* _rename(name: str)_ - Equivalent to `incus rename` command.
* _restart(*, force: bool=True, timeout: int=-1)_ - Equivalent to `incus restart` command.
* _restore(self, name: str, *, stateful: bool=False)_ - Equivalent to `incus restore` command.
* _save(config: dict=None, devices: dict=None, profiles: list=None, description: str=None)_ - Equivalent to `yaml | incus config edit` command.
* _snapshot(name: str, *, reuse: bool=False, stateful: bool=False)_ - Equivalent to `incus snapshot` command.
* _start()_ - Equivalent to `incus start` command.
* _stop(*, force: bool=True, timeout: int=-1)_ - Equivalent to `incus stop` command.

#### Attributes

* _incus_ - `Incus` object.
* _remote_ - `Remote` object.
* _project_ - `Project` object.
* _architecture_ - Read only attribute associated to the Incus object. Instance architecture.
* _backups_ - Read only attribute associated to the Incus object. Instance backups.
* _config_ - Attribute associated to the Incus object. Instance configuration. 
* _createdAt_ - Read only attribute associated to the Incus object. Instance created at.
* _description_ - Attribute associated to the Incus object. Instance description.
* _devices_ - Attribute associated to the Incus object. Instance devices.
* _ephemeral_ - Read only attribute associated to the Incus object. Instance if ephemeral.
* _expandedConfig_ - Read only attribute associated to the Incus object. Instance expanded configuration.
* _expandedDevices_ - Read only attribute associated to the Incus object. Instance expanded devices.
* _lastUsedAt_ - Read only attribute associated to the Incus object. Instance last used at.
* _location_ - Read only attribute associated to the Incus object. Instance location.
* _profiles_ - Attribute associated to the Incus object. A list of instance profiles.
* _snapshots_ - Read only attribute associated to the Incus object. A list of instance snapshots.
* _state_ - Read only attribute associated to the Incus object. Instance state.
* _stateful_ - Read only attribute associated to the Incus object. Instance stateful.
* _status_ - Read only attribute associated to the Incus object. Instance state.
* _statusCode_ - Read only attribute associated to the Incus object. Instance status code.
* _type_ - Read only attribute associated to the Incus object. Instance type.

#### Examples

```python
import pyincus

remote = pyincus.remotes.get(name="local")
project = remote.projects.get(name="default")

# List instances of a given project.
print(project.instances.list())

# Check if the instance exists
if(project.instances.exists(name="test")):
	# Fetch the instance
	instance = project.instances.get(name="test")

	print(instance.name)

	# If the state of the instance is running, pause it.
	if(instance.state.lower() == "running"):
		instance.pause()
	
	# If the state of the instance is frozen, stop it.
	if(instance.state.lower() == "frozen"):
		instance.stop()

	# Delete the instance.
	instance.delete()

# Create and start an instance.
instance = project.instances.launch(image="ubuntu/22.04", name="test", remoteSource="images", config={"description":"Test description"})

# Get expanded devices, which are the devices coming from the profile.
devices = {"eth0": **instance.expandedDevices["eth0"]}

# Set static IPv4.
devices["eth0"]["ipv4.address"] = "10.0.0.1"

# Set the devices.
instance.devices = devices

# Create a snapshot.
instance.snapshot(name="my-snapshot-name")

# List that the snapshot is created.
print(instance.snapshots)

# Restore the instance snapshot.
instance.restore(name="my-snapshot-name")
```

### Network

#### Methods

* _get(name: str)_ - Get a specific `Network` object.

#### Attributes

* _incus_ - `Incus` object.
* _remote_ - `Remote` object.
* _project_ - `Project` object.
* _forwards_ - Empty instance of `NetworkForward` object to gain access to methods like `list`, `get` and `exists`.
* _config_ - Read only attribute associated to the Incus object. Network configuration.
* _description_ - Read only attribute associated to the Incus object. Network description.
* _locations_ - Read only attribute associated to the Incus object. Network locations
* _managed_ - Read only attribute associated to the Incus object. Network managed.
* _status_ - Read only attribute associated to the Incus object. Network status.
* _type_ - Read only attribute associated to the Incus object. Network type.
* _usedBy_ - Read only attribute associated to the Incus object. Network used by what other object.

#### Examples

```python
import pyincus

remote = pyincus.remotes.get(name="local")
project = remote.projects.get(name="default")

# List networks of a given project.
print(project.networks.list())

# Check if the network exists
if(project.networks.exists(name="test")):
	# Fetch the network
	network = project.networks.get(name="test")

	print(network.name)
```

### NetworkACL

#### Methods

* _create(name: str, *, description: str=None, egress: list=None, ingress: list=None)_ - Equivalent to `incus network acl create`
* _delete()_ - Equivalent to `incus network acl delete`
* _get(name: str)_ - Get a specific `NetworkACL` object.
* _rename(name: str)_ - Equivalent to `incus network acl rename`
* _save(description: str=None, egress: list=None, ingress: list=None)_ - Equivalent to `yaml | incus network acl edit`
* _validateGress(gress: list)_ - Validate egress or ingress.

#### Attributes

* _incus_ - `Incus` object.
* _remote_ - `Remote` object.
* _project_ - `Project` object.
* _config_ - Read only attribute associated to the Incus object.
* _description_ - Attribute associated to the Incus object. ACL description.
* _egress_ - Attribute associated to the Incus object. A list of every egress rules.
* _ingress_ - Attribute associated to the Incus object. A list of every ingress rules.
* _possibleActions_ - Read only attribute. List all possible values for the attribute action.
* _possibleProtocols_ - Read only attribute. List all possible values for the attribute protocol.
* _possibleRuleKeys_ - Read only attribute. List all possible keys for an ACL.
* _possibleStates_ - Read only attribute. List all possible values for the attribute state.
* _usedBy_ - Read only attribute associated to the Incus object. Network ACL used by what other object.

#### Examples

```python
import pyincus

remote = pyincus.remotes.get(name="local")
project = remote.projects.get(name="default")

# List instances of a given project.
print(project.instances.list())

# Check if the instance exists
if(project.instances.exists(name="test")):
	# Fetch the instance
	instance = project.instances.get(name="test")

	print(instance.name)
```

### NetworkForward

#### Methods

* _addPort(\*, protocol: str, listenPorts: str, targetAddress: str, targetPorts: str=None)_ - Add a port forward.
* _exists(listeAddress: str)_ - Return `True` if the object exists and `False` if not.
* _get(listenAddress: str)_ - Get a specific `NetworkForward` object.
* _list()_ - List all port forwards.
* _refresh()_ - Refresh the attributes.
* _removePort(\*, protocol: str, listenPorts: str)_ - Remove a port forward.
* _save(description: str=None)_ - Update the description of a network forward.
* _validatePortList(ports: str | int)_ - Validate that each port range in the list are valid. Each individual ports and port ranges must be split by a comma.

#### Attributes

* _incus_ - `Incus` object.
* _remote_ - `Remote` object.
* _project_ - `Project` object.
* _network_ - `Network` object.
* _config_ - Read only attribute associated to the Incus object. Network forward configuration.
* _description_ - Attribute associated to the Incus object. Network forward description.
* _listenAddress_ - Read only attribute associated to the Incus object. Name of the network forward as they don't work by name but by address.
* _ports_ - Read only attribute associated to the Incus object. List all port forwards.
* _possibleProtocols_ - Read only attribute. List all possible values for the attribute protocol.

#### Examples

```python
import pyincus

remote = pyincus.remotes.get(name="local")
project = remote.projects.get(name="default")
network = project.networks.get(name="test")

# List forwards of a given network.
print(network.forwards.list())

# Check if the forward exists
if(network.forwards.exists(listenAddress="10.0.0.1")):
	# Fetch the forward
	forward = network.forwards.get(listenAddress="10.0.0.1")

	print(forward.name)

	forward.addPort(protocol="tcp", listenPorts="80,443,9000-9005", targetAddress="10.0.0.2")
	
	forward.removePort(protocol="tcp", listenPorts="80,443,9000-9005")
```