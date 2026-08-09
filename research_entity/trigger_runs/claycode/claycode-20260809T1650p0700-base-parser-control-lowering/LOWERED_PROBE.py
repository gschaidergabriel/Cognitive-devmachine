def classify(x):
    if x["instability"] >= 0.80:
        return "DIVERGING_OR_OVERTHINKING"
    if x["state_delta"] <= 0.05 and x["residual_pressure"] >= 0.50:
        return "STALLED"
    if x["recurrence_delta"] >= 0.15 and x["instability"] < 0.80:
        return "PRODUCTIVE_LIMIT_CYCLE"
    return "CONVERGING_FIXED_POINT"
