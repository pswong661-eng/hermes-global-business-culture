"""Test bootstrap for the dash-named plugin directory.

Same pattern as catalog plugin memory-wiki: stop pytest from importing the
plugin's ``__init__.py`` as a test module (it does ``from . import ...`` which
needs the Hermes plugin loader's package context), and put the plugin root on
``sys.path`` so ``import tools`` / ``import schemas`` resolve.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

collect_ignore = ["__init__.py"]
