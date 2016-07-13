import re
__version__ = '1.3.27'

support_versions = ['0.9']


def is_a_version(version):
    version_pattern = re.compile(r'\d+\.\d+\.\d+')
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
