"""Tests for src/vec.py -- Vec 2D vector class."""

import math
import pytest
from src.vec import Vec


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestVecConstruction:
    def test_construct_from_x_y(self):
        v = Vec(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_construct_copy(self):
        original = Vec(5.0, 6.0)
        copy = Vec(original)
        assert copy.x == original.x
        assert copy.y == original.y

    def test_copy_is_independent(self):
        original = Vec(5.0, 6.0)
        copy = Vec(original)
        copy.x = 99.0
        assert original.x == 5.0

    def test_construct_with_zero(self):
        v = Vec(0.0, 0.0)
        assert v.x == 0.0
        assert v.y == 0.0

    def test_construct_with_negative_values(self):
        v = Vec(-3.0, -4.0)
        assert v.x == -3.0
        assert v.y == -4.0

    def test_construct_with_integers(self):
        v = Vec(3, 4)
        assert v.x == 3
        assert v.y == 4


# ---------------------------------------------------------------------------
# as_tuple
# ---------------------------------------------------------------------------

class TestVecAsTuple:
    def test_as_tuple(self):
        v = Vec(1.0, 2.0)
        assert v.as_tuple() == (1.0, 2.0)

    def test_as_tuple_negative(self):
        v = Vec(-1.0, -2.0)
        assert v.as_tuple() == (-1.0, -2.0)

    def test_as_tuple_zero(self):
        v = Vec(0.0, 0.0)
        assert v.as_tuple() == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Addition
# ---------------------------------------------------------------------------

class TestVecAddition:
    def test_add_two_vectors(self):
        a = Vec(1.0, 2.0)
        b = Vec(3.0, 4.0)
        result = a + b
        assert result.x == 4.0
        assert result.y == 6.0

    def test_add_returns_new_vec(self):
        a = Vec(1.0, 2.0)
        b = Vec(3.0, 4.0)
        result = a + b
        assert result is not a
        assert result is not b

    def test_add_negative_vectors(self):
        a = Vec(-1.0, -2.0)
        b = Vec(-3.0, -4.0)
        result = a + b
        assert result.x == -4.0
        assert result.y == -6.0

    def test_add_zero_vector(self):
        a = Vec(5.0, 7.0)
        zero = Vec(0.0, 0.0)
        result = a + zero
        assert result.x == 5.0
        assert result.y == 7.0


# ---------------------------------------------------------------------------
# Subtraction
# ---------------------------------------------------------------------------

class TestVecSubtraction:
    def test_subtract_two_vectors(self):
        a = Vec(5.0, 7.0)
        b = Vec(3.0, 4.0)
        result = a - b
        assert result.x == 2.0
        assert result.y == 3.0

    def test_subtract_returns_new_vec(self):
        a = Vec(5.0, 7.0)
        b = Vec(3.0, 4.0)
        result = a - b
        assert result is not a
        assert result is not b

    def test_subtract_self_gives_zero(self):
        a = Vec(5.0, 7.0)
        result = a - a
        assert result.x == pytest.approx(0.0)
        assert result.y == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Scalar multiplication
# ---------------------------------------------------------------------------

class TestVecScalarMultiplication:
    @pytest.mark.parametrize(
        "x, y, scalar, expected_x, expected_y",
        [
            (2.0, 3.0, 2.0, 4.0, 6.0),
            (2.0, 3.0, 0.0, 0.0, 0.0),
            (2.0, 3.0, -1.0, -2.0, -3.0),
            (0.0, 0.0, 5.0, 0.0, 0.0),
            (1.0, 1.0, 0.5, 0.5, 0.5),
        ],
    )
    def test_scalar_multiplication(self, x, y, scalar, expected_x, expected_y):
        v = Vec(x, y)
        result = v * scalar
        assert result.x == pytest.approx(expected_x)
        assert result.y == pytest.approx(expected_y)

    def test_scalar_multiplication_returns_new_vec(self):
        v = Vec(2.0, 3.0)
        result = v * 2.0
        assert result is not v


# ---------------------------------------------------------------------------
# Dot product
# ---------------------------------------------------------------------------

class TestVecDotProduct:
    def test_dot_product_perpendicular(self):
        a = Vec(1.0, 0.0)
        b = Vec(0.0, 1.0)
        assert a.dot(b) == pytest.approx(0.0)

    def test_dot_product_parallel(self):
        a = Vec(1.0, 0.0)
        b = Vec(3.0, 0.0)
        assert a.dot(b) == pytest.approx(3.0)

    def test_dot_product_antiparallel(self):
        a = Vec(1.0, 0.0)
        b = Vec(-1.0, 0.0)
        assert a.dot(b) == pytest.approx(-1.0)

    def test_dot_product_general(self):
        a = Vec(2.0, 3.0)
        b = Vec(4.0, 5.0)
        # 2*4 + 3*5 = 8 + 15 = 23
        assert a.dot(b) == pytest.approx(23.0)

    def test_dot_product_with_self(self):
        a = Vec(3.0, 4.0)
        # 3*3 + 4*4 = 9 + 16 = 25
        assert a.dot(a) == pytest.approx(25.0)


# ---------------------------------------------------------------------------
# Magnitude
# ---------------------------------------------------------------------------

class TestVecMagnitude:
    def test_magnitude_unit_x(self):
        v = Vec(1.0, 0.0)
        assert v.magnitude() == pytest.approx(1.0)

    def test_magnitude_unit_y(self):
        v = Vec(0.0, 1.0)
        assert v.magnitude() == pytest.approx(1.0)

    def test_magnitude_3_4_5_triangle(self):
        v = Vec(3.0, 4.0)
        assert v.magnitude() == pytest.approx(5.0)

    def test_magnitude_zero_vector(self):
        v = Vec(0.0, 0.0)
        assert v.magnitude() == pytest.approx(0.0)

    def test_magnitude_negative_components(self):
        v = Vec(-3.0, -4.0)
        assert v.magnitude() == pytest.approx(5.0)

    @pytest.mark.parametrize(
        "x, y, expected_mag",
        [
            (1.0, 1.0, math.sqrt(2)),
            (5.0, 12.0, 13.0),
            (8.0, 15.0, 17.0),
        ],
    )
    def test_magnitude_parametrized(self, x, y, expected_mag):
        v = Vec(x, y)
        assert v.magnitude() == pytest.approx(expected_mag)


# ---------------------------------------------------------------------------
# Normalize
# ---------------------------------------------------------------------------

class TestVecNormalize:
    def test_normalize_unit_vector_unchanged(self):
        v = Vec(1.0, 0.0)
        n = v.normalize()
        assert n.x == pytest.approx(1.0)
        assert n.y == pytest.approx(0.0)

    def test_normalize_3_4_5(self):
        v = Vec(3.0, 4.0)
        n = v.normalize()
        assert n.x == pytest.approx(3.0 / 5.0)
        assert n.y == pytest.approx(4.0 / 5.0)
        assert n.magnitude() == pytest.approx(1.0)

    def test_normalize_negative_vector(self):
        v = Vec(-3.0, -4.0)
        n = v.normalize()
        assert n.magnitude() == pytest.approx(1.0)
        assert n.x == pytest.approx(-3.0 / 5.0)
        assert n.y == pytest.approx(-4.0 / 5.0)

    def test_normalize_zero_vector_returns_zero(self):
        """Normalizing a zero vector should return a zero vector (no crash)."""
        v = Vec(0.0, 0.0)
        n = v.normalize()
        assert n.x == pytest.approx(0.0)
        assert n.y == pytest.approx(0.0)

    def test_normalize_returns_new_vec(self):
        v = Vec(3.0, 4.0)
        n = v.normalize()
        assert n is not v

    def test_normalize_preserves_direction(self):
        v = Vec(10.0, 0.0)
        n = v.normalize()
        assert n.x == pytest.approx(1.0)
        assert n.y == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Rotate
# ---------------------------------------------------------------------------

class TestVecRotate:
    def test_rotate_0_degrees(self):
        v = Vec(1.0, 0.0)
        r = v.rotate(0)
        assert r.x == pytest.approx(1.0)
        assert r.y == pytest.approx(0.0)

    def test_rotate_90_degrees(self):
        v = Vec(1.0, 0.0)
        r = v.rotate(90)
        assert r.x == pytest.approx(0.0)
        assert r.y == pytest.approx(1.0)

    def test_rotate_180_degrees(self):
        v = Vec(1.0, 0.0)
        r = v.rotate(180)
        assert r.x == pytest.approx(-1.0)
        assert r.y == pytest.approx(0.0)

    def test_rotate_270_degrees(self):
        v = Vec(1.0, 0.0)
        r = v.rotate(270)
        assert r.x == pytest.approx(0.0)
        assert r.y == pytest.approx(-1.0)

    def test_rotate_360_degrees(self):
        v = Vec(1.0, 0.0)
        r = v.rotate(360)
        assert r.x == pytest.approx(1.0)
        assert r.y == pytest.approx(0.0)

    def test_rotate_45_degrees(self):
        v = Vec(1.0, 0.0)
        r = v.rotate(45)
        expected = math.sqrt(2) / 2.0
        assert r.x == pytest.approx(expected)
        assert r.y == pytest.approx(expected)

    def test_rotate_negative_90_degrees(self):
        v = Vec(1.0, 0.0)
        r = v.rotate(-90)
        assert r.x == pytest.approx(0.0)
        assert r.y == pytest.approx(-1.0)

    def test_rotate_returns_new_vec(self):
        v = Vec(1.0, 0.0)
        r = v.rotate(90)
        assert r is not v

    @pytest.mark.parametrize("angle", [0, 45, 90, 135, 180, 225, 270, 315, 360])
    def test_rotate_preserves_magnitude(self, angle):
        v = Vec(3.0, 4.0)
        r = v.rotate(angle)
        assert r.magnitude() == pytest.approx(v.magnitude())

    def test_rotate_non_unit_vector_90_degrees(self):
        v = Vec(0.0, 5.0)
        r = v.rotate(90)
        assert r.x == pytest.approx(-5.0)
        assert r.y == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# get_orientation_angle
# ---------------------------------------------------------------------------

class TestVecOrientationAngle:
    def test_orientation_angle_east(self):
        v = Vec(1.0, 0.0)
        assert v.get_orientation_angle() == pytest.approx(0.0)

    def test_orientation_angle_north(self):
        v = Vec(0.0, 1.0)
        assert v.get_orientation_angle() == pytest.approx(90.0)

    def test_orientation_angle_west(self):
        v = Vec(-1.0, 0.0)
        assert v.get_orientation_angle() == pytest.approx(180.0)

    def test_orientation_angle_south(self):
        v = Vec(0.0, -1.0)
        assert v.get_orientation_angle() == pytest.approx(-90.0)

    def test_orientation_angle_northeast_45(self):
        v = Vec(1.0, 1.0)
        assert v.get_orientation_angle() == pytest.approx(45.0)

    def test_orientation_angle_southeast_neg45(self):
        v = Vec(1.0, -1.0)
        assert v.get_orientation_angle() == pytest.approx(-45.0)

    @pytest.mark.parametrize(
        "x, y, expected_angle",
        [
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 90.0),
            (-1.0, 0.0, 180.0),
            (0.0, -1.0, -90.0),
            (1.0, 1.0, 45.0),
            (-1.0, 1.0, 135.0),
            (-1.0, -1.0, -135.0),
            (1.0, -1.0, -45.0),
        ],
    )
    def test_orientation_angle_parametrized(self, x, y, expected_angle):
        v = Vec(x, y)
        assert v.get_orientation_angle() == pytest.approx(expected_angle)


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------

class TestVecRepr:
    def test_repr(self):
        v = Vec(1.5, 2.5)
        assert repr(v) == "Vec(1.5, 2.5)"

    def test_repr_integers(self):
        v = Vec(3, 4)
        assert repr(v) == "Vec(3, 4)"
