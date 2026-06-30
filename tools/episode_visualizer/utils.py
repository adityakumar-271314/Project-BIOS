def clamp(value, min_val, max_val):
    """Auxiliary numeric float coordinate value container clamp tool method."""
    return max(min_val, min(value, max_val))