#!/usr/bin/env python3

######################
# Generic Exceptions #
######################

class LXDException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)

class LXDVersionException(LXDException):
    def __init__(self, libVersion, clientVersion):
        super().__init__(msg=f"The library uses \"{libVersion}\" and you have \"{clientVersion}\" installed. Please match the versions.")

class ObjectNotFoundException(LXDException):
    def __init__(self, msg="Object not found."):
        super().__init__(msg=msg)

class ObjectAlreadyExistsException(LXDException):
    def __init__(self, msg="Object already exists."):
        super().__init__(msg=msg)

class NameAlreadyInUseException(LXDException):
    def __init__(self, name: str):
        super().__init__(msg=f"Name {name} already in use.")

class InvalidLXDObjectNameFormatException(LXDException):
    def __init__(self, name: str):
        super().__init__(msg=f"The LXD object name is not the correct length or format. It has to be 1 to 63 characters long, contains only letters, numbers and dashes, must not start with a digit or dash, and must not end with a dash: {name}")

class InvalidDescriptionException(LXDException):
    def __init__(self):
        super().__init__(msg="description must be a string.")

class InvalidImageNameFormatException(LXDException):
    def __init__(self, name: str):
        super().__init__(msg=f"The image name is not the correct length or format. It has to be short hash of 12 hexadecimal, long hash of 64 hexadecimal or a combine of alphanumeric, dash, dot and forward slash of 1 to 64 length: {name}")

class InvalidIPAddressException(LXDException):
    def __init__(self, ipAddress: str):
        super().__init__(msg=f"IP address {f'{chr(34)}{ipAddress}{chr(34)} ' if ipAddress else ''}is not a valid IPv4 or IPv6.")

class DeviceNotFoundException(ObjectNotFoundException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Device {f'{chr(34)}{name}{chr(34)} ' if name else ''}not found.")

#####################
# Remote Exceptions #
#####################

class RemoteException(LXDException):
    def __init__(self, msg: str):
        super().__init__(msg=msg)

class RemoteNotFoundException(RemoteException, ObjectNotFoundException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Remote {f'{chr(34)}{name}{chr(34)} ' if name else ''}not found.")

class RemoteAlreadyExistsException(RemoteException, ObjectAlreadyExistsException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Remote {f'{chr(34)}{name}{chr(34)} ' if name else ''}already exists.")

class RemoteLocalCannotBeModifiedException(RemoteException):
    def __init__(self):
        super().__init__(msg="Remote \"local\" is static and cannot be modified.")

######################
# Project Exceptions #
######################

class ProjectException(LXDException):
    def __init__(self, msg: str):
        super().__init__(msg=msg)

class ProjectNotFoundException(ProjectException, ObjectNotFoundException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Project {f'{chr(34)}{name}{chr(34)} ' if name else ''}not found.")

class ProjectAlreadyExistsException(ProjectException, ObjectAlreadyExistsException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Project {f'{chr(34)}{name}{chr(34)} ' if name else ''}already exists.")

class ProjectDefaultCannotBeRenamedException(ProjectException):
    def __init__(self):
        super().__init__(msg="The 'default' project cannot be renamed.")

class ProjectIsInUseException(ProjectException):
    def __init__(self):
        super().__init__(msg="Only empty projects can be renamed.")

#######################
# Instance Exceptions #
#######################

class InstanceException(LXDException):
    def __init__(self, msg: str):
        super().__init__(msg=msg)

class InstanceNotFoundException(InstanceException, ObjectNotFoundException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Instance {f'{chr(34)}{name}{chr(34)} ' if name else ''}not found.")

class InstanceAlreadyExistsException(InstanceException, ObjectAlreadyExistsException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Instance {f'{chr(34)}{name}{chr(34)} ' if name else ''}already exists.")

class InstanceIsRunningException(LXDException):
    def __init__(self):
        super().__init__(msg="The instance is running.")

class InstanceIsNotRunningException(LXDException):
    def __init__(self):
        super().__init__(msg="The instance is not running.")

class InstanceIsAlreadyStoppedException(LXDException):
    def __init__(self):
        super().__init__(msg="The instance is already stopped.")

class InstanceTimeoutExceededException(LXDException):
    def __init__(self):
        super().__init__(msg="The time allowed has exceeded.")

######################
# Network Exceptions #
######################

class NetworkException(LXDException):
    def __init__(self, msg: str):
        super().__init__(msg=msg)

class NetworkNotFoundException(NetworkException, ObjectNotFoundException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Network {f'{chr(34)}{name}{chr(34)} ' if name else ''}not found.")

class NetworkAlreadyExistsException(NetworkException, ObjectAlreadyExistsException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Network {f'{chr(34)}{name}{chr(34)} ' if name else ''}already exists.")

##########################
# Network ACL Exceptions #
##########################

class NetworkACLException(LXDException):
    def __init__(self, msg: str):
        super().__init__(msg=msg)

class NetworkACLNotFoundException(NetworkACLException, ObjectNotFoundException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Network ACL {f'{chr(34)}{name}{chr(34)} ' if name else ''}not found.")

class NetworkACLAlreadyExistsException(NetworkACLException, ObjectAlreadyExistsException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Network ACL {f'{chr(34)}{name}{chr(34)} ' if name else ''}already exists.")

class NetworkACLInUseException(NetworkACLException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Network ACL {f'{chr(34)}{name}{chr(34)} ' if name else ''}in use.")

class InvalidACLGressException(NetworkACLException):
    def __init__(self):
        super().__init__(msg="egress and ingress must be a list containing dictionaries.")

class InvalidACLRuleActionException(NetworkACLException):
    def __init__(self, allowed, action=None):
        super().__init__(msg=f"Action {f'{chr(34)}{action}{chr(34)} ' if action else ''}must be present and must be one of the following: {allowed}")

class InvalidACLRuleStateException(NetworkACLException):
    def __init__(self, allowed, state=None):
        super().__init__(msg=f"State {f'{chr(34)}{state}{chr(34)} ' if state else ''}must be present and must be one of the following: {allowed}")

class InvalidACLRuleProtocolException(NetworkACLException):
    def __init__(self, allowed, protocol=None):
        super().__init__(msg=f"Protocol {f'{chr(34)}{protocol}{chr(34)} ' if protocol else ''} must be one of the following: {allowed}")

class InvalidACLRuleKeyException(NetworkACLException):
    def __init__(self, allowed, key=None):
        super().__init__(msg=f"Key {f'{chr(34)}{key}{chr(34)} ' if key else ''} must be one of the following: {allowed}")

class MissingProtocolException(NetworkACLException):
    def __init__(self):
        super().__init__(msg="Protocol must be specified when \"source_port\" or \"destination_port\" are used.")

##############################
# Network Forward Exceptions #
##############################

class NetworkForwardException(LXDException):
    def __init__(self, msg: str):
        super().__init__(msg=msg)

class NetworkForwardNotFoundException(NetworkForwardException, ObjectNotFoundException):
    def __init__(self, name: str=None):
        super().__init__(msg=f"Network Forward {f'{chr(34)}{name}{chr(34)} ' if name else ''}not found.")

class NetworkForwardPortNotFoundException(NetworkForwardException, ObjectNotFoundException):
    def __init__(self, ports):
        super().__init__(msg=f"Network Forward port \"{ports}\" was not found.")

class NetworkForwardAlreadyExistsException(NetworkForwardException, ObjectAlreadyExistsException):
    def __init__(self):
        super().__init__(msg="Network Forward already exists.")

class NetworkForwardPortAlreadyExistsException(NetworkForwardException, ObjectAlreadyExistsException):
    def __init__(self, *, protocol, port):
        super().__init__(msg=f"Network Forward port \"{port}\" already exists for protocol \"{protocol}\".")

class InvalidPortProtocolException(NetworkForwardException):
    def __init__(self, allowed, protocol=None):
        super().__init__(msg=f"Protocol {f'{chr(34)}{protocol}{chr(34)} ' if protocol else ''}must be one of the following: {allowed}")

class StartLowerThanEndException(NetworkForwardException):
    def __init__(self, ports):
        super().__init__(msg=f"Invalid port range. Start must be lower than end: {ports}")

class InvalidPortRangeException(NetworkForwardException):
    def __init__(self, ports):
        super().__init__(msg=f"Invalid port range, can only be digits with dashes and commas: {ports}")

class DuplicatePortException(NetworkForwardException):
    def __init__(self, *, ports, duplicate):
        super().__init__(msg=f"Duplicate port \"{duplicate}\" with: {ports}")

class InvalidTargetPortsException(NetworkForwardException):
    def __init__(self, *, listenPorts, targetPorts):
        super().__init__(msg=f"Target ports \"{targetPorts}\" must either be empty or the same amount of listen ports \"{listenPorts}\".")
