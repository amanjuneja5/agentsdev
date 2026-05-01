"""Unit tests for utils.py."""

import unittest

from utils import calculate_average, get_user_name


class TestCalculateAverage(unittest.TestCase):
    """Tests for the calculate_average function."""

    # --- happy-path tests ---

    def test_integers(self):
        """Average of a list of integers."""
        self.assertEqual(calculate_average([1, 2, 3, 4, 5]), 3.0)

    def test_floats(self):
        """Average of a list of floats."""
        self.assertAlmostEqual(calculate_average([1.5, 2.5, 3.0]), 2.333333, places=5)

    def test_mixed_int_and_float(self):
        """Average of a mixed list of ints and floats."""
        self.assertAlmostEqual(calculate_average([1, 2.0, 3]), 2.0)

    def test_single_element(self):
        """Average of a single-element list equals that element."""
        self.assertEqual(calculate_average([42]), 42.0)

    def test_two_elements(self):
        """Average of two elements."""
        self.assertEqual(calculate_average([10, 20]), 15.0)

    def test_negative_numbers(self):
        """Average handles negative numbers correctly."""
        self.assertEqual(calculate_average([-2, -4, -6]), -4.0)

    def test_mixed_positive_and_negative(self):
        """Average of numbers that cancel out is zero."""
        self.assertEqual(calculate_average([-3, 3]), 0.0)

    def test_all_zeros(self):
        """Average of all-zero list is zero."""
        self.assertEqual(calculate_average([0, 0, 0]), 0.0)

    def test_large_list(self):
        """Average of a large consecutive sequence."""
        numbers = list(range(1, 101))  # 1 to 100
        self.assertEqual(calculate_average(numbers), 50.5)

    # --- edge / boundary tests ---

    def test_empty_list_returns_zero(self):
        """Empty list must return 0 per the docstring contract."""
        self.assertEqual(calculate_average([]), 0)

    def test_return_type_is_float_for_non_empty(self):
        """Return value for a non-empty list should be a float."""
        result = calculate_average([1, 2, 3])
        self.assertIsInstance(result, float)

    def test_very_large_numbers(self):
        """Average of very large numbers."""
        self.assertEqual(calculate_average([1e15, 3e15]), 2e15)

    def test_very_small_floats(self):
        """Average of very small floats."""
        self.assertAlmostEqual(calculate_average([1e-10, 3e-10]), 2e-10)


class TestGetUserName(unittest.TestCase):
    """Tests for the get_user_name function."""

    # --- happy-path tests ---

    def test_returns_uppercase_name(self):
        """Name should be returned in uppercase."""
        self.assertEqual(get_user_name({"name": "alice"}), "ALICE")

    def test_name_already_uppercase(self):
        """Already-uppercase name stays uppercase."""
        self.assertEqual(get_user_name({"name": "BOB"}), "BOB")

    def test_mixed_case_name(self):
        """Mixed-case name is fully uppercased."""
        self.assertEqual(get_user_name({"name": "ChArLiE"}), "CHARLIE")

    def test_extra_keys_ignored(self):
        """Extra keys in the dict do not affect the result."""
        user = {"name": "diana", "age": 30, "active": True}
        self.assertEqual(get_user_name(user), "DIANA")

    def test_name_with_spaces(self):
        """Name containing spaces is uppercased correctly."""
        self.assertEqual(get_user_name({"name": "john doe"}), "JOHN DOE")

    # --- None / falsy user tests ---

    def test_none_user_returns_none(self):
        """None user returns None."""
        self.assertIsNone(get_user_name(None))

    def test_empty_dict_returns_none(self):
        """Empty dict is falsy and should return None."""
        self.assertIsNone(get_user_name({}))

    # --- missing or None name tests ---

    def test_name_key_missing_returns_none(self):
        """Dict without a 'name' key returns None."""
        self.assertIsNone(get_user_name({"age": 25}))

    def test_name_value_none_returns_none(self):
        """Dict with name=None returns None."""
        self.assertIsNone(get_user_name({"name": None}))

    # --- return-type tests ---

    def test_return_type_is_str_when_name_present(self):
        """Return type is str when a valid name is present."""
        result = get_user_name({"name": "eve"})
        self.assertIsInstance(result, str)

    def test_return_type_is_none_when_no_user(self):
        """Return type is NoneType when user is None."""
        self.assertIsNone(get_user_name(None))


if __name__ == "__main__":
    unittest.main()
