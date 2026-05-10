from __future__ import annotations
import math

from matplotlib.pylab import normal


class Vector2:
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = float(x)
        self.y = float(y)

    # =====================================================
    # Arithmetic
    # =====================================================

    def __add__(self, o: "Vector2") -> "Vector2":
        return Vector2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vector2") -> "Vector2":
        return Vector2(self.x - o.x, self.y - o.y)

    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector2":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "Vector2":
        return Vector2(self.x / scalar, self.y / scalar)

    # =====================================================
    # Geometry
    # =====================================================

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalized(self) -> "Vector2":
        mag = self.length()

        if mag <= 1e-9:
            return Vector2()

        return Vector2(self.x / mag, self.y / mag)

    def dot(self, o: "Vector2") -> float:
        return self.x * o.x + self.y * o.y

    def slide(self, normal: "Vector2") -> "Vector2":
        return self - normal * self.dot(normal)

    def lerp(self, o: "Vector2", t: float) -> "Vector2":
        return self + (o - self) * t

    def copy(self) -> "Vector2":
        return Vector2(self.x, self.y)

    # =====================================================
    # Serialization
    # =====================================================

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Vector2":
        return cls(
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
        )

    # =====================================================
    # Debugging
    # =====================================================

    def __repr__(self):
        return f"Vector2({self.x:.3f}, {self.y:.3f})"
