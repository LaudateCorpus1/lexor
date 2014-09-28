# Lexor local installation
#
# This bash file is meant to be used for local installation.
#

# The path to this local installation
export LEXOR_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Access to lexor
export PATH=$LEXOR_ROOT/bin:$PATH

# Python and C/C++
export PYTHONPATH=$LEXOR_ROOT:$PYTHONPATH

# LEXOR_CONFIG:
# If you have a configuration file for lexor that you wish to
# use then define this variable
#export LEXOR_CONFIG_PATH=/path/to/lexor.config
