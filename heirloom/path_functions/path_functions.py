import os
import re


def convert_to_wine_path(path_to_convert):
    expanded_path = os.path.expanduser(path_to_convert)
    if not expanded_path.startswith('Z:'):
        converted_path = 'Z:' + expanded_path
    else:
        converted_path = expanded_path
    converted_path = converted_path.replace('/', '\\')
    return converted_path


def convert_to_unix_path(path_to_convert):
    regex = re.compile('^[A-Z|a-z]:')
    if re.match(regex, path_to_convert):
        path_to_convert = str().join(path_to_convert[2:]).replace('\\', '/')
    else:
        path_to_convert = path_to_convert.replace('\\', '/')
    return path_to_convert
