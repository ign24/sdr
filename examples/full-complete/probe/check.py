def normalize(value: str) -> str:
    return "-".join(value.strip().lower().split())


inputs = ["  Blue Card ", "GREEN card", "Red   Card"]
expected = ["blue-card", "green-card", "red-card"]
assert [normalize(value) for value in inputs] == expected
assert [normalize(value) for value in inputs] == expected
print("SYNTHETIC_PROBE_OK")
