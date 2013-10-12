"""lexor setup script"""

from setuptools import find_packages, setup
from lexor.__version__ import VERSION, VERSION_INFO

DESCRIPTION = "Document converter implemented in python."
LONG_DESCRIPTION = "Lexor is a parser, converter and writer."

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
      url='http://math.uh.edu/~jmlopez/lexor',
      license='BSD License',
      packages=find_packages(),
      scripts=[
          'bin/lexor',
          ],
      package_data={
          'lexor.dev': ['*.txt'],
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
