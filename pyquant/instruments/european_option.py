from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)  # initialiser
class EuropeanOption:
    underlying: str
    strike: float
    expiry: date
    option_type: str

    def __post_init__(self) -> None:  # validating contracts
        if not self.underlying.strip():
            raise ValueError("Underlying cannot be empty.")
        if self.strike <= 0:
            raise ValueError("Strike must be positive.")
        if self.option_type not in {"call", "put"}:
            raise ValueError("Option type must be 'call' or 'put'.")
