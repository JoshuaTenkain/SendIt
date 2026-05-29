"""Courier adapter registry.

Resolves ``Courier`` rows in the DB into concrete adapter instances. Honours
``Courier.is_enabled`` so admins can toggle a courier off at any time.

Supported ``adapter_code`` values:

* ``tcg``         - live The Courier Guy (Shiplogic) API
* ``csv_table``   - CSV-uploaded price-table pricing
* ``mock``        - synthetic test adapter
* ``aramex`` / ``courier_guy_stub`` / ``pargo`` - legacy stubs (kept for tests)
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.couriers.aramex import AramexAdapter
from app.integrations.couriers.base import CourierAdapter
from app.integrations.couriers.courier_guy import CourierGuyAdapter
from app.integrations.couriers.csv_table import CSVTableAdapter
from app.integrations.couriers.dhl import DHLAdapter
from app.integrations.couriers.mock import MockCourierAdapter
from app.integrations.couriers.pargo import PargoAdapter
from app.integrations.couriers.tcg import TCGAdapter
from app.models.courier import Courier


class CourierRegistry:
    """Adapter registry.

    Two construction modes:
      * ``CourierRegistry(adapters=[...])``     - explicit adapters (tests/legacy)
      * ``CourierRegistry.from_db(db)``         - build from DB, filtered to enabled
    """

    def __init__(self, adapters: Iterable[CourierAdapter] | None = None):
        self._adapters: dict[str, CourierAdapter] = {}
        self._courier_ids: dict[str, str] = {}  # code -> courier.id (str)
        for adapter in adapters or self.default_adapters():
            self._adapters[adapter.courier_code] = adapter

    @staticmethod
    def default_adapters() -> list[CourierAdapter]:
        return [MockCourierAdapter(), AramexAdapter(), CourierGuyAdapter(), PargoAdapter()]

    @classmethod
    def from_db(cls, db: Session) -> "CourierRegistry":
        """Build a registry of enabled couriers from the DB.

        Falls back to an empty registry if nothing is enabled — caller is
        expected to surface a helpful error to the user.
        """
        reg = cls(adapters=[])
        rows = list(
            db.scalars(
                select(Courier).where(Courier.is_enabled.is_(True)).order_by(Courier.name)
            )
        )
        for courier in rows:
            adapter = _build_adapter(db=db, courier=courier)
            if adapter is None:
                continue
            reg._adapters[courier.code] = adapter
            reg._courier_ids[courier.code] = str(courier.id)
        return reg

    def get_enabled(self, enabled_codes: set[str] | None = None) -> list[CourierAdapter]:
        if not enabled_codes:
            return list(self._adapters.values())
        return [a for a in self._adapters.values() if a.courier_code in enabled_codes]

    def get(self, courier_code: str) -> CourierAdapter:
        return self._adapters[courier_code]

    def courier_id_for_code(self, courier_code: str) -> str | None:
        return self._courier_ids.get(courier_code)


def _build_adapter(*, db: Session, courier: Courier) -> CourierAdapter | None:
    """Map a ``Courier`` DB row to a concrete adapter instance."""
    from app.config import settings

    code = (courier.adapter_code or courier.code or "").lower()
    if code == "tcg":
        if not settings.tcg_enabled or not settings.tcg_api_token:
            return None
        return TCGAdapter(markup_pct=int(courier.base_markup_pct or 0))
    if code == "aramex":
        if not settings.aramex_enabled or not settings.aramex_api_key:
            return None
        return AramexAdapter(markup_pct=int(courier.base_markup_pct or 0))
    if code == "dhl":
        if not settings.dhl_enabled or not settings.dhl_api_key:
            return None
        return DHLAdapter(markup_pct=int(courier.base_markup_pct or 0))
    if code == "csv_table":
        return CSVTableAdapter(db=db, courier=courier)
    if code == "mock":
        return MockCourierAdapter()
    if code in ("courier_guy_stub", "courier_guy"):
        return CourierGuyAdapter()
    if code == "pargo":
        return PargoAdapter()
    return None
