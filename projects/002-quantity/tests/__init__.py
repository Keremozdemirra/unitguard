"""Test package.

The dimension algebra lives in the sibling project ``001-dimensions`` rather
than on PyPI, so a checkout has to be told where to find it. Doing this in the
test package rather than in each test module means the path is set before any
test module imports ``unitguard_quantity``, which imports the dimensions
package at module level.
"""

import os
import sys

_SIBLING = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "001-dimensions",
)
if _SIBLING not in sys.path:
    sys.path.insert(0, _SIBLING)
