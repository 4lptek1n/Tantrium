"""Failure-frontier helpers for coefficient positivity checks."""


def find_first_failure(rows):
    """Return the first row whose value is negative, or None.

    Rows may be dictionaries with a 'value' or 'coefficient' key.
    """
    for row in rows:
        value = row.get("value", row.get("coefficient", None))
        if value is not None and value < 0:
            return row
    return None


def summarize_failure(rows):
    failure = find_first_failure(rows)
    if failure is None:
        return "No negative coefficient found in supplied rows."
    return f"First failure: {failure}"
