import math
from typing import Optional, Dict, Any

# Type alias for vector
Vector = Dict[str, float]


def create(x: float = 0, y: float = 0) -> Vector:
    """Creates a new vector."""
    return {'x': x, 'y': y}


def clone(vector: Vector) -> Vector:
    """Returns a new vector with x and y copied from the given vector."""
    return {'x': vector['x'], 'y': vector['y']}


def magnitude(vector: Vector) -> float:
    """Returns the magnitude (length) of a vector."""
    return math.sqrt(vector['x'] * vector['x'] + vector['y'] * vector['y'])


def magnitude_squared(vector: Vector) -> float:
    """Returns the magnitude squared (saves a sqrt operation)."""
    return vector['x'] * vector['x'] + vector['y'] * vector['y']


def rotate(vector: Vector, angle: float, output: Optional[Vector] = None) -> Vector:
    """Rotates the vector about (0, 0) by specified angle."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    if output is None:
        output = {}
    x = vector['x'] * cos_a - vector['y'] * sin_a
    output['y'] = vector['x'] * sin_a + vector['y'] * cos_a
    output['x'] = x
    return output


def rotate_about(vector: Vector, angle: float, point: Vector, output: Optional[Vector] = None) -> Vector:
    """Rotates the vector about a specified point by specified angle."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    if output is None:
        output = {}
    x = point['x'] + ((vector['x'] - point['x']) * cos_a - (vector['y'] - point['y']) * sin_a)
    output['y'] = point['y'] + ((vector['x'] - point['x']) * sin_a + (vector['y'] - point['y']) * cos_a)
    output['x'] = x
    return output


def normalise(vector: Vector) -> Vector:
    """Normalises a vector (such that its magnitude is 1)."""
    mag = magnitude(vector)
    if mag == 0:
        return {'x': 0, 'y': 0}
    return {'x': vector['x'] / mag, 'y': vector['y'] / mag}


# Alias for American spelling
normalize = normalise


def dot(vector_a: Vector, vector_b: Vector) -> float:
    """Returns the dot-product of two vectors."""
    return vector_a['x'] * vector_b['x'] + vector_a['y'] * vector_b['y']


def cross(vector_a: Vector, vector_b: Vector) -> float:
    """Returns the cross-product of two vectors (scalar in 2D)."""
    return vector_a['x'] * vector_b['y'] - vector_a['y'] * vector_b['x']


def cross3(vector_a: Vector, vector_b: Vector, vector_c: Vector) -> float:
    """Returns the cross-product of three vectors."""
    return (vector_b['x'] - vector_a['x']) * (vector_c['y'] - vector_a['y']) - \
           (vector_b['y'] - vector_a['y']) * (vector_c['x'] - vector_a['x'])


def add(vector_a: Vector, vector_b: Vector, output: Optional[Vector] = None) -> Vector:
    """Adds the two vectors."""
    if output is None:
        output = {}
    output['x'] = vector_a['x'] + vector_b['x']
    output['y'] = vector_a['y'] + vector_b['y']
    return output


def sub(vector_a: Vector, vector_b: Vector, output: Optional[Vector] = None) -> Vector:
    """Subtracts the two vectors (a - b)."""
    if output is None:
        output = {}
    output['x'] = vector_a['x'] - vector_b['x']
    output['y'] = vector_a['y'] - vector_b['y']
    return output


def mult(vector: Vector, scalar: float) -> Vector:
    """Multiplies a vector by a scalar."""
    return {'x': vector['x'] * scalar, 'y': vector['y'] * scalar}


def div(vector: Vector, scalar: float) -> Vector:
    """Divides a vector by a scalar."""
    return {'x': vector['x'] / scalar, 'y': vector['y'] / scalar}


def perp(vector: Vector, negate: bool = False) -> Vector:
    """Returns the perpendicular vector. Set negate to True for opposite direction."""
    n = -1 if negate else 1
    return {'x': n * -vector['y'], 'y': n * vector['x']}


def neg(vector: Vector) -> Vector:
    """Negates both components of a vector."""
    return {'x': -vector['x'], 'y': -vector['y']}


def angle(vector_a: Vector, vector_b: Vector) -> float:
    """Returns the angle between vectors (vectorB - vectorA) and the x-axis in radians."""
    return math.atan2(vector_b['y'] - vector_a['y'], vector_b['x'] - vector_a['x'])


# Temporary vector pool for efficiency
_temp = [create(), create(), create(), create(), create(), create()]
