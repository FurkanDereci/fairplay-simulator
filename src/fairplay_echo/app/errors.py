"""Uygulama seviyesi hatalar.

Servis katmanı bunları fırlatır; HTTP kodlarına çevirme **tek yerde** (`app/main.py`
exception handler'ları) yapılır. Böylece servis, web çatısına bağımlı olmaz.
"""

from __future__ import annotations

from collections.abc import Mapping


class AppError(Exception):
    status_code = 400

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail)
        self.detail = detail or type(self).__name__


class Unauthorized(AppError):
    status_code = 401


class Forbidden(AppError):
    status_code = 403


class NotFound(AppError):
    status_code = 404


class Conflict(AppError):
    status_code = 409


class LockedOut(AppError):
    """İflas cooldown'ı aktifken para hareketi denendi."""

    status_code = 423


class EnergyDepleted(AppError):
    """Simülasyon enerjisi eşiğin altında."""

    status_code = 429


class UnknownFixture(AppError):
    status_code = 400


class UnknownMarket(AppError):
    status_code = 400


class RuinConfirmationRequired(AppError):
    """Kasa eşiğini aşan bahis, kullanıcı onayı olmadan işlenmez (spec §3.4).

    `ruin` gövdesi istemciye **yapısal** gider (stake, kasadaki pay, `R_ruin %`); istemci
    formülü kendisi hesaplamaz (SSOT). Şema `app/main.py`'deki özel handler'da verilir.
    """

    status_code = 409

    def __init__(self, detail: str, ruin: Mapping[str, object]) -> None:
        super().__init__(detail)
        self.ruin: dict[str, object] = dict(ruin)
