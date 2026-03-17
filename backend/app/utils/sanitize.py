import math
from typing import Any

import pandas as pd

def sanitize_value(v: Any) -> Any:
    """
    Convert pandas/numpy NaN/NA/Inf to None and normalize scalar types.
    """
    # Pandas missing (covers pd.NA, NaT, numpy.nan inside many containers)
    if v is None:
        return None
    if pd.isna(v):
        return None

    # Float infinities / NaN
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return v

    # Pandas Timestamp -> python datetime/date is handled elsewhere
    return v