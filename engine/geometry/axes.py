import math
from typing import List, Dict
from . import vector as Vector


def from_vertices(vertices: List[Dict]) -> List[Dict]:
    """
    Creates a new set of axes from the given vertices.
    Returns unique edge normals for collision detection.
    """
    axes = {}
    
    for i in range(len(vertices)):
        j = (i + 1) % len(vertices)
        
        # Get the edge normal (perpendicular to edge)
        normal = Vector.normalise({
            'x': vertices[j]['y'] - vertices[i]['y'],
            'y': vertices[i]['x'] - vertices[j]['x']
        })
        
        # Use a gradient key to detect duplicate axes (parallel edges)
        # This reduces the number of axes for SAT
        if normal['x'] == 0:
            gradient_key = float('inf') if normal['y'] >= 0 else float('-inf')
        else:
            gradient_key = normal['y'] / normal['x']
        
        axes[gradient_key] = normal
    
    return list(axes.values())


def rotate(axes: List[Dict], angle: float) -> None:
    """Rotates a set of axes by the given angle in-place."""
    if angle == 0:
        return
    
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    
    for axis in axes:
        x = axis['x'] * cos_a - axis['y'] * sin_a
        axis['y'] = axis['x'] * sin_a + axis['y'] * cos_a
        axis['x'] = x
