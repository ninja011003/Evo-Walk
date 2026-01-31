import math
from typing import List, Dict, Any, Optional
from . import vector as Vector


def create(points: List[Dict], body: Any = None) -> List[Dict]:
    """
    Creates a new set of Body compatible vertices.
    The points argument accepts an array of vectors orientated around the origin (0, 0).
    Vertices must be specified in clockwise order.
    """
    vertices = []
    for i, point in enumerate(points):
        vertex = {
            'x': point['x'],
            'y': point['y'],
            'index': i,
            'body': body,
            'is_internal': False
        }
        vertices.append(vertex)
    return vertices


def from_path(path: str, body: Any = None) -> List[Dict]:
    """
    Parses a string containing ordered x y pairs separated by spaces,
    into a vertices array.
    """
    import re
    pattern = r'L?\s*([-\d.e]+)[\s,]*([-\d.e]+)'
    points = []
    for match in re.finditer(pattern, path, re.IGNORECASE):
        points.append({'x': float(match.group(1)), 'y': float(match.group(2))})
    return create(points, body)


def centre(vertices: List[Dict]) -> Dict:
    """Returns the centre (centroid) of the set of vertices."""
    area_val = area(vertices, signed=True)
    centre_pt = {'x': 0, 'y': 0}
    
    for i in range(len(vertices)):
        j = (i + 1) % len(vertices)
        cross_val = Vector.cross(vertices[i], vertices[j])
        temp = Vector.mult(Vector.add(vertices[i], vertices[j]), cross_val)
        centre_pt = Vector.add(centre_pt, temp)
    
    return Vector.div(centre_pt, 6 * area_val)


# Alias
center = centre


def mean(vertices: List[Dict]) -> Dict:
    """Returns the average (mean) of the set of vertices."""
    average = {'x': 0, 'y': 0}
    for vertex in vertices:
        average['x'] += vertex['x']
        average['y'] += vertex['y']
    return Vector.div(average, len(vertices))


def area(vertices: List[Dict], signed: bool = False) -> float:
    """Returns the area of the set of vertices."""
    area_val = 0
    j = len(vertices) - 1
    
    for i in range(len(vertices)):
        area_val += (vertices[j]['x'] - vertices[i]['x']) * (vertices[j]['y'] + vertices[i]['y'])
        j = i
    
    if signed:
        return area_val / 2
    return abs(area_val) / 2


def inertia(vertices: List[Dict], mass: float) -> float:
    """
    Returns the moment of inertia (second moment of area) of the set of vertices
    given the total mass.
    """
    numerator = 0
    denominator = 0
    v = vertices
    
    for n in range(len(v)):
        j = (n + 1) % len(v)
        cross_val = abs(Vector.cross(v[j], v[n]))
        numerator += cross_val * (Vector.dot(v[j], v[j]) + Vector.dot(v[j], v[n]) + Vector.dot(v[n], v[n]))
        denominator += cross_val
    
    if denominator == 0:
        return 0
    return (mass / 6) * (numerator / denominator)


def translate(vertices: List[Dict], vector: Dict, scalar: float = 1) -> List[Dict]:
    """Translates the set of vertices in-place."""
    translate_x = vector['x'] * scalar
    translate_y = vector['y'] * scalar
    
    for vertex in vertices:
        vertex['x'] += translate_x
        vertex['y'] += translate_y
    
    return vertices


def rotate(vertices: List[Dict], angle: float, point: Dict) -> List[Dict]:
    """Rotates the set of vertices in-place."""
    if angle == 0:
        return vertices
    
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    point_x = point['x']
    point_y = point['y']
    
    for vertex in vertices:
        dx = vertex['x'] - point_x
        dy = vertex['y'] - point_y
        vertex['x'] = point_x + (dx * cos_a - dy * sin_a)
        vertex['y'] = point_y + (dx * sin_a + dy * cos_a)
    
    return vertices


def contains(vertices: List[Dict], point: Dict) -> bool:
    """Returns True if the point is inside the set of vertices."""
    point_x = point['x']
    point_y = point['y']
    vertex = vertices[-1]
    
    for next_vertex in vertices:
        if (point_x - vertex['x']) * (next_vertex['y'] - vertex['y']) + \
           (point_y - vertex['y']) * (vertex['x'] - next_vertex['x']) > 0:
            return False
        vertex = next_vertex
    
    return True


def scale(vertices: List[Dict], scale_x: float, scale_y: float, point: Optional[Dict] = None) -> List[Dict]:
    """Scales the vertices from a point (default is centre) in-place."""
    if scale_x == 1 and scale_y == 1:
        return vertices
    
    if point is None:
        point = centre(vertices)
    
    for vertex in vertices:
        delta = Vector.sub(vertex, point)
        vertex['x'] = point['x'] + delta['x'] * scale_x
        vertex['y'] = point['y'] + delta['y'] * scale_y
    
    return vertices


def chamfer(vertices: List[Dict], radius: Any = None, quality: int = -1, 
            quality_min: int = 2, quality_max: int = 14) -> List[Dict]:
    """
    Chamfers a set of vertices by giving them rounded corners.
    Returns a new set of vertices.
    """
    if isinstance(radius, (int, float)):
        radius = [radius]
    elif radius is None:
        radius = [8]
    
    new_vertices = []
    
    for i in range(len(vertices)):
        prev_vertex = vertices[i - 1] if i > 0 else vertices[-1]
        vertex = vertices[i]
        next_vertex = vertices[(i + 1) % len(vertices)]
        current_radius = radius[i] if i < len(radius) else radius[-1]
        
        if current_radius == 0:
            new_vertices.append(vertex)
            continue
        
        prev_normal = Vector.normalise({
            'x': vertex['y'] - prev_vertex['y'],
            'y': prev_vertex['x'] - vertex['x']
        })
        
        next_normal = Vector.normalise({
            'x': next_vertex['y'] - vertex['y'],
            'y': vertex['x'] - next_vertex['x']
        })
        
        diagonal_radius = math.sqrt(2 * current_radius ** 2)
        radius_vector = Vector.mult(Vector.clone(prev_normal), current_radius)
        mid_normal = Vector.normalise(Vector.mult(Vector.add(prev_normal, next_normal), 0.5))
        scaled_vertex = Vector.sub(vertex, Vector.mult(mid_normal, diagonal_radius))
        
        precision = quality
        if quality == -1:
            precision = current_radius ** 0.32 * 1.75
        
        precision = max(quality_min, min(quality_max, int(precision)))
        
        if precision % 2 == 1:
            precision += 1
        
        alpha = math.acos(Vector.dot(prev_normal, next_normal))
        theta = alpha / precision
        
        for j in range(precision):
            new_vertices.append(Vector.add(Vector.rotate(radius_vector, theta * j), scaled_vertex))
    
    return new_vertices


def clockwise_sort(vertices: List[Dict]) -> List[Dict]:
    """Sorts the input vertices into clockwise order in place."""
    centre_pt = mean(vertices)
    vertices.sort(key=lambda v: Vector.angle(centre_pt, v))
    return vertices


def is_convex(vertices: List[Dict]) -> Optional[bool]:
    """
    Returns True if the vertices form a convex shape (vertices must be in clockwise order).
    Returns None if not computable.
    """
    flag = 0
    n = len(vertices)
    
    if n < 3:
        return None
    
    for i in range(n):
        j = (i + 1) % n
        k = (i + 2) % n
        z = (vertices[j]['x'] - vertices[i]['x']) * (vertices[k]['y'] - vertices[j]['y'])
        z -= (vertices[j]['y'] - vertices[i]['y']) * (vertices[k]['x'] - vertices[j]['x'])
        
        if z < 0:
            flag |= 1
        elif z > 0:
            flag |= 2
        
        if flag == 3:
            return False
    
    if flag != 0:
        return True
    return None


def hull(vertices: List[Dict]) -> List[Dict]:
    """Returns the convex hull of the input vertices as a new array of points."""
    upper = []
    lower = []
    
    # Sort vertices on x-axis (y-axis for ties)
    sorted_vertices = sorted(vertices, key=lambda v: (v['x'], v['y']))
    
    # Build lower hull
    for vertex in sorted_vertices:
        while len(lower) >= 2 and Vector.cross3(lower[-2], lower[-1], vertex) <= 0:
            lower.pop()
        lower.append(vertex)
    
    # Build upper hull
    for vertex in reversed(sorted_vertices):
        while len(upper) >= 2 and Vector.cross3(upper[-2], upper[-1], vertex) <= 0:
            upper.pop()
        upper.append(vertex)
    
    # Remove last points (repeated at beginning of other list)
    upper.pop()
    lower.pop()
    
    return upper + lower
