"""lexor setup script"""

import imp
import os.path as pt
from setuptools import setup


def get_version():
    """Get version & version_info without importing lexor.__init__ """
    path = pt.join(pt.dirname(__file__), 'lexor', '__version__.py')
    mod = imp.load_source('lexor_version', path)
    return mod.VERSION, mod.VERSION_INFO

VERSION, VERSION_INFO = get_version()

DESCRIPTION = "Document converter implemented in python."
LONG_DESCRIPTION = open(pt.join(pt.dirname(__file__), 'README.rst')).read()
LONG_DESCRIPTION += open(pt.join(pt.dirname(__file__), 'HISTORY.rst')).read()

DEV_STATUS_MAP = {
    'alpha': '3 - Alpha',
    'beta': '4 - Beta',
    'rc': '4 - Beta',
    'final': '5 - Production/Stable'
}
if VERSION_INFO[3] == 'alpha' and VERSION_INFO[4] == 0:
    DEVSTATUS = '2 - Pre-Alpha'
else:
    DEVSTATUS = DEV_STATUS_MAP[VERSION_INFO[3]]

setup(name='lexor',
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
      scripts=['bin/lexor'],
      install_requires=[
          'configparser>=3.3.0r2',
          'argcomplete>=0.6.7',
          'nose>=1.3',
          'python-dateutil>=2.2',
          ],
      package_data={
          'lexor.core': ['*.txt'],
          },
      include_package_data=True,
      classifiers=[
          'Development Status :: %s' % DEVSTATUS,
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
