# Utils

This module provides general-purpose utility functions.

---

## Functions

### `calculate_average(numbers)`

Calculates the arithmetic mean of a list of numbers.

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `numbers` | `list[float \| int]` | A list of numeric values to average. |

**Returns:** `float` — The arithmetic mean of the provided numbers, or `0` if the list is empty.

**Example**

```python
calculate_average([1, 2, 3, 4, 5])  # Returns 3.0
calculate_average([])               # Returns 0
```

---

### `get_user_name(user)`

Retrieves the `"name"` field from a user dictionary and returns it in uppercase.

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `user` | `dict[str, object] \| None` | A dictionary expected to contain a `"name"` key, or `None`. |

**Returns:** `str | None` — The user's name in uppercase, or `None` if `user` is falsy, the `"name"` key is absent, or its value is `None`.

**Example**

```python
get_user_name({"name": "alice"})  # Returns "ALICE"
get_user_name({"age": 30})        # Returns None
get_user_name(None)               # Returns None
```
