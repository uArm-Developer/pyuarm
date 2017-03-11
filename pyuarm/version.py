import re
from pkg_resources import parse_version
__version__ = '2.4.0.12'
support_versions = ['2.2']


def is_a_version(version):
    version_pattern = re.compile(r'\d+\.\d+\.\d+\w*')
    if version_pattern.match(version):
        return True
    else:
        return False


def is_supported_version(version):
    pattern = re.compile(r'\d+\.\d+')
    major_version = pattern.match(version).group()
    for v in support_versions:
        if major_version == v:
            return True
    return False


def check_version_update(version1, version2):
    if parse_version(version1) > parse_version(version2):
        return True
    else:
        return False


if __name__ == '__main__':
    print(__version__)