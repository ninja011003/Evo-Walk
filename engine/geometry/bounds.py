from typing import List, Dict, Any, Optional


def create(vertices: Optional[List[Dict]] = None) -> Dict:
    """Creates a new axis-aligned bounding box (AABB) given a set of vertices."""
    bounds = {
        'min': {'x': 0, 'y': 0},
        'max': {'x': 0, 'y': 0}
    }
    
    if vertices:
        update(bounds, vertices)
    
    return bounds


def update(bounds: Dict, vertices: List[Dict], velocity: Optional[Dict] = None) -> None:
    """Updates bounds using the given vertices and extends the bounds given a velocity."""
    bounds['min']['x'] = float('inf')
    bounds['max']['x'] = float('-inf')
    bounds['min']['y'] = float('inf')
    bounds['max']['y'] = float('-inf')
    
    for vertex in vertices:
        if vertex['x'] > bounds['max']['x']:
            bounds['max']['x'] = vertex['x']
        if vertex['x'] < bounds['min']['x']:
            bounds['min']['x'] = vertex['x']
        if vertex['y'] > bounds['max']['y']:
            bounds['max']['y'] = vertex['y']
        if vertex['y'] < bounds['min']['y']:
            bounds['min']['y'] = vertex['y']
    
    if velocity:
        if velocity['x'] > 0:
            bounds['max']['x'] += velocity['x']
        else:
            bounds['min']['x'] += velocity['x']
        
        if velocity['y'] > 0:
            bounds['max']['y'] += velocity['y']
        else:
            bounds['min']['y'] += velocity['y']


def contains(bounds: Dict, point: Dict) -> bool:
    """Returns True if the bounds contains the given point."""
    return (point['x'] >= bounds['min']['x'] and 
            point['x'] <= bounds['max']['x'] and
            point['y'] >= bounds['min']['y'] and 
            point['y'] <= bounds['max']['y'])


def overlaps(bounds_a: Dict, bounds_b: Dict) -> bool:
    """Returns True if the two bounds intersect."""
    return (bounds_a['min']['x'] <= bounds_b['max']['x'] and
            bounds_a['max']['x'] >= bounds_b['min']['x'] and
            bounds_a['max']['y'] >= bounds_b['min']['y'] and
            bounds_a['min']['y'] <= bounds_b['max']['y'])


def translate(bounds: Dict, vector: Dict) -> None:
    """Translates the bounds by the given vector."""
    bounds['min']['x'] += vector['x']
    bounds['max']['x'] += vector['x']
    bounds['min']['y'] += vector['y']
    bounds['max']['y'] += vector['y']


def shift(bounds: Dict, position: Dict) -> None:
    """Shifts the bounds to the given position."""
    delta_x = bounds['max']['x'] - bounds['min']['x']
    delta_y = bounds['max']['y'] - bounds['min']['y']
    
    bounds['min']['x'] = position['x']
    bounds['max']['x'] = position['x'] + delta_x
    bounds['min']['y'] = position['y']
    bounds['max']['y'] = position['y'] + delta_y
