from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Aday:
    """Kesifte gorulen bir canli yayin (kanal basina bir kayit)."""

    platform: str          # "youtube" | "twitch"
    kanal_id: str
    kanal_adi: str
    url: str
    dil: str               # "tr" | "en" | "diger"
    izleyici: int
    baslik: str
    takipci: int | None = None   # YouTube abone sayisi (gizliyse None)
    ulke: str | None = None
    etiketler: list[str] = field(default_factory=list)

    @property
    def anahtar(self) -> str:
        return f"{self.platform}:{self.kanal_id}"

    def sozluk(self) -> dict:
        return asdict(self)
