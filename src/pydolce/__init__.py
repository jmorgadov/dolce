import logging

from pydolce.check import check

__version__ = "0.1.3"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

__all__ = ["check"]
