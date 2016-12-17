import re
__version__ = '2.2.5.3'
support_versions = ['2.2.1']


def is_a_version(version):
    version_pattern = re.compile(r'\d+\.\d+\.\d+\w*')
    if version_pattern.match(version):
        return True
    else:
        return False


def is_supported_version(version):
    pattern = re.compile(r'\d+\.\d+\.\d+')
    major_version = pattern.match(version).group()
    for v in support_versions:
        if major_version == v:
            return True
    return False
