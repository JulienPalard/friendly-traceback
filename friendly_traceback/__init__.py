# note that public_api.py limits the number of names imported via __all__

import sys as _sys
import warnings as _warnings

_valid_version = _sys.version_info.major >= 3 and _sys.version_info.minor >= 6

if not _valid_version:
    print("Python 3.6 or newer is required.")
    _sys.exit()


# Ensure that warnings are not shown to the end user, possibly causing confusion.
_warnings.simplefilter("ignore")

del _valid_version
del _sys
del _warnings

from .public_api import *  # noqa
from .console import FriendlyConsole, start_console  # noqa
