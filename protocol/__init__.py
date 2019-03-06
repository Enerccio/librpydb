# py23 compatible
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

from .base import __all__ as base_all
from .gen import __all__ as gen_all

from .base import *
from .gen import *

__all__ = ["features"] + base_all + gen_all

# enabled features
features = {
    "supportsExceptionInfoRequest": False,
    "supportTerminateDebuggee": False,
    "supportsTerminateThreadsRequest": False,
    "supportsDataBreakpoints": False,
    "supportsStepInTargetsRequest": False,
    "supportsSetExpression": False,
    "supportsGotoTargetsRequest": False,
    "supportsFunctionBreakpoints": False,

    # TODO
    "supportsConditionalBreakpoints": False,
    "supportsHitConditionalBreakpoints": False,
}
