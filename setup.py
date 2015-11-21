"""lexor setup script"""
import imp
import os.path as pt
from setuptools import setup


def get_version():
    """Get version & version_info without importing lexor.__init__"""
    path = pt.join(pt.dirname(__file__), 'lexor', '__version__.py')
    mod = imp.load_source('lexor_version', path)
    return mod.VERSION, mod.VERSION_INFO


def read_file(name):
    """Read a file located in the projects root directory"""
    return open(pt.join(pt.dirname(__file__), name)).read()


VERSION, VERSION_INFO = get_version()
DESCRIPTION = 'Document converter implemented in python.'
LONG_DESCRIPTION = read_file('README.rst')
LONG_DESCRIPTION += read_file('HISTORY.rst')
DEV_STATUS_MAP = {
    'alpha': '3 - Alpha',
    'beta': '4 - Beta',
    'rc': '4 - Beta',
    'final': '5 - Production/Stable'
}
if VERSION_INFO[3] == 'alpha' and VERSION_INFO[4] == 0:
    DEV_STATUS = '2 - Pre-Alpha'
else:
    DEV_STATUS = DEV_STATUS_MAP[VERSION_INFO[3]]

setup(
    name='lexor',
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    keywords='lexor markdown html',
    author='Manuel Lopez',
    author_email='jmlopez.rod@gmail.com',
    url='http://lexor.readthedocs.org',
    license='BSD License',
    packages=[
        'lexor',
        'lexor.command',
        'lexor.core',
    ],
    scripts=[
        'bin/lexor'
    ],
    install_requires=[
        'configparser>=3.3.0r2',
        'argparse>=1.4.0',
        'nose>=1.3',
        'python-dateutil>=2.2',
    ],
    package_data={
        'lexor.core': ['*.txt'],
    },
    include_package_data=True,
    classifiers=[
        'Development Status :: %s' % DEV_STATUS,
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Documentation',
        'Topic :: Communications :: Email',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Text Processing :: Markup',
    ],
)
