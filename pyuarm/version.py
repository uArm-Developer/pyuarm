import re
__version__ = '2.0.7'

support_versions = ['2.0']


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


def main():
    print ("Version: {}".format(__version__))
    print ("Support Firmware Version: {}".format(support_versions))

if __name__ == '__main__':
    main()