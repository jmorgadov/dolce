import logging

import pydolce.core.rules.checkers  # noqa: F401  (checkers are registered on import)
from pydolce.commands.check import check
from pydolce.commands.suggest import suggest

__version__ = "0.1.4"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

__all__ = ["__version__", "check", "suggest"]
