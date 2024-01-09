#!/usr/bin/env python3
import re

INCUS_OBJECT_NAME = '[a-zA-Z][a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9]'

REGEX_INCUS_OBJECT_NAME = re.compile(rf'^{INCUS_OBJECT_NAME}$')
REGEX_IMAGE_NAME = re.compile(r'^([a-fA-F0-9]{64}|[a-fA-F0-9]{12}|[a-zA-Z0-9/\-\.]{1,64})$')
REGEX_DEVICE_NOT_FOUND = re.compile(rf'No (?P<device>{INCUS_OBJECT_NAME}) device could be found')
REGEX_NETWORK_NOT_FOUND_COPY = re.compile(rf'Failed to load network "(?P<network>{INCUS_OBJECT_NAME})" for project "{INCUS_OBJECT_NAME}": Network not found')
REGEX_EMPTY_BODY = re.compile(r'Error:\s*[a-zA-Z]+\s*"[^"]+":\s*http:\s*ContentLength=\d+\s*with\s*Body\s*length\s*\d+')
REGEX_IS_TRUE = re.compile(r'^(true|yes|1|on)$', re.IGNORECASE)
REGEX_IS_FALSE = re.compile(r'^(false|no|0|off)$', re.IGNORECASE)
REGEX_IS_NONE = re.compile(r'^(none|null|undefined)$', re.IGNORECASE)

def isTrue(value):
	if(isinstance(value, int)):
		value = str(value)

	if(isinstance(value, str)):
		return REGEX_IS_TRUE.match(value)
	
	return value

def isFalse(value):
	if(isinstance(value, int)):
		value = str(value)

	if(isinstance(value, str)):
		return REGEX_IS_FALSE.match(value)
	
	return value

def isNone(value):
	if(isinstance(value, str)):
		return REGEX_IS_NONE.match(value)

	return value is None