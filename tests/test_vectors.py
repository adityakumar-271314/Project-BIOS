from core.vector import Vector2


def test_vector_addition():
    a = Vector2(1, 2)
    b = Vector2(3, 4)

    result = a + b

    assert result.x == 4
    assert result.y == 6


def test_vector_subtraction():
    a = Vector2(10, 5)
    b = Vector2(2, 1)

    result = a - b

    assert result.x == 8
    assert result.y == 4


def test_vector_length():
    v = Vector2(3, 4)

    assert v.length() == 5


def test_vector_normalized():
    v = Vector2(3, 4)

    n = v.normalized()

    assert round(n.length(), 5) == 1.0


def test_vector_slide():
    velocity = Vector2(1, -1)
    normal = Vector2(0, 1)

    result = velocity.slide(normal)

    assert result.y == 0
