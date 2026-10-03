"""İnce API kabuğu.

İş mantığı burada **değil**: router'lar parse → servis → serialize yapar, kurallar `services`'ta.
"""

from .main import create_app

__all__ = ["create_app"]
