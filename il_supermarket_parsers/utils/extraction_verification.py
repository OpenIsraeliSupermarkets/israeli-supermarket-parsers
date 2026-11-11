"""Production switch for checking each parsed file against its XML."""

import os
from enum import Enum
from typing import Optional

ENV_VAR = "PARSER_VERIFY_EXTRACTION"


class ExtractionVerification(str, Enum):
    """How :class:`RawParsingPipeline` checks a file after parsing it."""

    OFF = "off"
    FULL = "full"


def get_extraction_verification(
    value: Optional[str] = None,
) -> ExtractionVerification:
    """Read the mode from ``value`` or ``PARSER_VERIFY_EXTRACTION``.

    Unset or empty means ``off``. Any value other than ``off``/``full``
    (case-insensitive) raises ``ValueError``, so a typo fails at startup
    instead of silently skipping verification.
    """
    if value is None:
        value = os.getenv(ENV_VAR, "")
    value = value.strip().lower() or ExtractionVerification.OFF.value
    try:
        return ExtractionVerification(value)
    except ValueError as error:
        allowed = ", ".join(mode.value for mode in ExtractionVerification)
        raise ValueError(
            f"{ENV_VAR} must be one of {allowed}, got {value!r}"
        ) from error
