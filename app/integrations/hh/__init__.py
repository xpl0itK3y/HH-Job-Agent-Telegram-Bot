"""HeadHunter integration package."""

from app.integrations.hh.client import HHClient
from app.integrations.hh.mapper import map_hh_vacancy

__all__ = ["HHClient", "map_hh_vacancy"]
