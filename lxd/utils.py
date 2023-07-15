#!/usr/bin/env python3
import re

LXD_OBJECT_NAME = '[a-zA-Z][a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9]'

REGEX_LXD_OBJECT_NAME = re.compile(rf'^{LXD_OBJECT_NAME}$')
REGEX_IMAGE_NAME = re.compile(r'^([a-fA-F0-9]{64}|[a-fA-F0-9]{12}|[a-zA-Z0-9/\-\.]{1,64})$')
REGEX_DEVICE_NOT_FOUND = re.compile(rf'No (?P<device>{LXD_OBJECT_NAME}) device could be found')
REGEX_NETWORK_NOT_FOUND_COPY = re.compile(rf'Failed to load network "(?P<network>{LXD_OBJECT_NAME})" for project "{LXD_OBJECT_NAME}": Network not found')