import hashlib
import json
from typing import Any


def calculate_request_hash(
    payload: dict[str, Any],
) -> str:
    """
    Create a deterministic SHA-256 fingerprint of a request.

    sort_keys=True ensures identical requests generate the same
    fingerprint even if dictionary key ordering differs.
    """

    canonical_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical_payload.encode("utf-8")
    ).hexdigest()