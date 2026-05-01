def calculate_average(numbers: list[float | int]) -> float:
    """Calculate the average of a list of numbers.

    Args:
        numbers: A list of numeric values to average.

    Returns:
        The arithmetic mean of the numbers, or 0 if the list is empty.
    """
    if not numbers:
        return 0
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

def get_user_name(user: dict[str, object] | None) -> str | None:
    """Retrieve and uppercase the name from a user dictionary.

    Args:
        user: A dictionary expected to contain a "name" key, or None/falsy.

    Returns:
        The user's name in uppercase if present, None if the user is falsy
        or the "name" key is missing or None.
    """
    if not user:
        return None
    name = user.get("name")
    return name.upper() if name is not None else None