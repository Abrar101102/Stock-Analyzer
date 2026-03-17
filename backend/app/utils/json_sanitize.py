import math
from typing import Any

def sanitize_json_floats(obj: Any) -> Any:
    """
    Recursively convert float NaN/Inf to None so FastAPI/Starlette JSON serialization doesn't crash.
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize_json_floats(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_json_floats(v) for v in obj]
    return obj