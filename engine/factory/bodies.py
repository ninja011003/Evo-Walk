import math
from typing import Dict, Any, List, Optional

from ..body import body as Body
from ..geometry import vector as Vector
from ..geometry import vertices as Vertices
from ..core import common as Common


def rectangle(x: float, y: float, width: float, height: float, options: Optional[Dict] = None) -> Dict:
    """
    Creates a new rigid body model with a rectangle hull.
    The options parameter is passed to Body.create, allowing you to set body properties.
    """
    options = options or {}
    
    rectangle_opts = dict(options)
    rectangle_opts['label'] = rectangle_opts.get('label', 'Rectangle Body')
    rectangle_opts['position'] = {'x': x, 'y': y}
    rectangle_opts['vertices'] = Vertices.from_path(
        f'L 0 0 L {width} 0 L {width} {height} L 0 {height}'
    )
    
    return Body.create(rectangle_opts)


def trapezoid(x: float, y: float, width: float, height: float, slope: float, options: Optional[Dict] = None) -> Dict:
    """
    Creates a new rigid body model with a trapezoid hull.
    """
    options = options or {}
    slope = slope or 0.5
    
    # Clamp slope to prevent invalid shapes
    slope = min(slope, 0.99) if slope >= 1 else max(slope, 0.01) if slope < 0 else slope
    
    roof = (1 - slope * 2) * width
    
    x1 = width * slope
    x2 = x1 + roof
    x3 = x2 + width * slope
    vertices = [
        {'x': 0, 'y': 0},
        {'x': x3, 'y': 0},
        {'x': x2, 'y': height},
        {'x': x1, 'y': height}
    ]
    
    if x1 < width * 0.5:
        vertices[0] = {'x': x1, 'y': 0}
        del vertices[3]
    
    trapezoid_opts = dict(options)
    trapezoid_opts['label'] = trapezoid_opts.get('label', 'Trapezoid Body')
    trapezoid_opts['position'] = {'x': x, 'y': y}
    trapezoid_opts['vertices'] = vertices
    
    return Body.create(trapezoid_opts)


def circle(x: float, y: float, radius: float, options: Optional[Dict] = None, max_sides: int = 25) -> Dict:
    """
    Creates a new rigid body model with a circle hull (approximated by a polygon).
    """
    options = options or {}
    
    sides = max(10, min(max_sides, round(radius)))
    
    # Optimisation: bodies with radius of 10 pixels or less approximate circles using polygons
    if sides < 25:
        return polygon(x, y, sides, radius, options)
    
    # For larger circles we use high-resolution polygons
    theta = 2 * math.pi / sides
    path = ''
    offset = theta * 0.5
    
    for i in range(sides):
        angle = offset + i * theta
        xx = math.cos(angle) * radius
        yy = math.sin(angle) * radius
        path += f'L {xx:.4f} {yy:.4f}'
    
    circle_opts = dict(options)
    circle_opts['label'] = circle_opts.get('label', 'Circle Body')
    circle_opts['circle_radius'] = radius
    circle_opts['position'] = {'x': x, 'y': y}
    circle_opts['vertices'] = Vertices.from_path(path)
    
    return Body.create(circle_opts)


def polygon(x: float, y: float, sides: int, radius: float, options: Optional[Dict] = None) -> Dict:
    """
    Creates a new rigid body model with a regular polygon hull.
    """
    options = options or {}
    
    if sides < 3:
        return circle(x, y, radius, options)
    
    theta = 2 * math.pi / sides
    path = ''
    offset = theta * 0.5
    
    for i in range(sides):
        angle = offset + i * theta
        xx = math.cos(angle) * radius
        yy = math.sin(angle) * radius
        path += f'L {xx:.4f} {yy:.4f}'
    
    polygon_opts = dict(options)
    polygon_opts['label'] = polygon_opts.get('label', 'Polygon Body')
    polygon_opts['position'] = {'x': x, 'y': y}
    polygon_opts['vertices'] = Vertices.from_path(path)
    
    return Body.create(polygon_opts)


def from_vertices(x: float, y: float, vertex_sets: Any, options: Optional[Dict] = None, flag_internal: bool = False, remove_collinear: float = 0.01, minimum_area: float = 10, remove_duplicates: float = 0.01) -> Dict:
    """
    Creates a body using the supplied vertices (or an array of vertices).
    If the vertices are convex, they will be used as-is.
    If they are concave or contain multiple parts, convex decomposition is required
    (this implementation assumes convex input for simplicity).
    """
    options = options or {}
    
    # Handle input as single set or multiple sets
    if not isinstance(vertex_sets, list):
        vertex_sets = [vertex_sets]
    
    if isinstance(vertex_sets[0], dict):
        # Single set of vertices
        vertex_sets = [vertex_sets]
    
    body_opts = dict(options)
    body_opts['position'] = {'x': x, 'y': y}
    body_opts['label'] = body_opts.get('label', 'Body')
    
    parts = []
    
    for vertices in vertex_sets:
        if not vertices:
            continue
        
        # Ensure we have proper vertex format
        if len(vertices) < 3:
            continue
        
        # Create a part for each vertex set
        part = Body.create({
            'position': Vertices.centre(vertices),
            'vertices': vertices
        })
        
        parts.append(part)
    
    if not parts:
        # Fallback to simple rectangle if no valid parts
        return rectangle(x, y, 40, 40, options)
    
    if len(parts) > 1:
        # Compound body
        body = Body.create(body_opts)
        Body.set_parts(body, parts)
        return body
    
    # Single part
    body_opts['vertices'] = parts[0]['vertices']
    return Body.create(body_opts)


# Composite shapes

def stack(x: float, y: float, columns: int, rows: int, column_gap: float, row_gap: float, callback) -> List[Dict]:
    """Creates a stack of bodies in a grid arrangement."""
    from ..body import composite as Composite
    
    stack = Composite.create({'label': 'Stack'})
    
    current_x = x
    current_y = y
    last_body = None
    
    for row in range(rows):
        last_size_y = 0
        
        for column in range(columns):
            body = callback(current_x, current_y, column, row, last_body, row)
            
            if body:
                last_size_y = max(last_size_y, body['bounds']['max']['y'] - body['bounds']['min']['y'])
                body_width = body['bounds']['max']['x'] - body['bounds']['min']['x']
                
                Body.translate(body, {
                    'x': body_width * 0.5,
                    'y': last_size_y * 0.5
                })
                
                current_x = body['bounds']['max']['x'] + column_gap
                Composite.add_body(stack, body)
                last_body = body
        
        current_x = x
        current_y += last_size_y + row_gap
    
    return stack


def pyramid(x: float, y: float, columns: int, rows: int, column_gap: float, row_gap: float, callback) -> Dict:
    """Creates a pyramid structure of bodies."""
    from ..body import composite as Composite
    
    stack = Composite.create({'label': 'Pyramid'})
    
    for row in range(rows):
        cols_in_row = columns - row
        cols_offset = row * 0.5
        
        current_x = x + cols_offset * (40 + column_gap)  # Assuming 40 is default body width
        current_y = y + row * (40 + row_gap)  # Assuming 40 is default body height
        
        for column in range(cols_in_row):
            body = callback(current_x, current_y, column, row, None, row)
            
            if body:
                body_width = body['bounds']['max']['x'] - body['bounds']['min']['x']
                current_x += body_width + column_gap
                Composite.add_body(stack, body)
    
    return stack


def chain(composite: Dict, x_offset_a: float, y_offset_a: float, x_offset_b: float, y_offset_b: float, options: Optional[Dict] = None) -> Dict:
    """Chains all bodies in the given composite together using constraints."""
    from ..body import composite as Composite
    from ..constraint import constraint as Constraint
    
    bodies = composite.get('bodies', [])
    
    for i in range(1, len(bodies)):
        body_a = bodies[i - 1]
        body_b = bodies[i]
        body_a_height = body_a['bounds']['max']['y'] - body_a['bounds']['min']['y']
        body_a_width = body_a['bounds']['max']['x'] - body_a['bounds']['min']['x']
        body_b_height = body_b['bounds']['max']['y'] - body_b['bounds']['min']['y']
        body_b_width = body_b['bounds']['max']['x'] - body_b['bounds']['min']['x']
        
        constraint_opts = dict(options) if options else {}
        constraint_opts['body_a'] = body_a
        constraint_opts['point_a'] = {'x': body_a_width * x_offset_b, 'y': body_a_height * y_offset_b}
        constraint_opts['body_b'] = body_b
        constraint_opts['point_b'] = {'x': body_b_width * x_offset_a, 'y': body_b_height * y_offset_a}
        
        constraint = Constraint.create(constraint_opts)
        Composite.add_constraint(composite, constraint)
    
    return composite


def mesh(composite: Dict, columns: int, rows: int, cross_brace: bool, options: Optional[Dict] = None) -> Dict:
    """Creates a mesh constraint connection between bodies in a grid."""
    from ..body import composite as Composite
    from ..constraint import constraint as Constraint
    
    bodies = composite.get('bodies', [])
    
    for row in range(rows):
        for column in range(columns):
            if column > 0:
                body_a = bodies[(row * columns) + column - 1]
                body_b = bodies[(row * columns) + column]
                
                constraint_opts = dict(options) if options else {}
                constraint_opts['body_a'] = body_a
                constraint_opts['body_b'] = body_b
                
                Composite.add_constraint(composite, Constraint.create(constraint_opts))
            
            if row > 0:
                body_a = bodies[(row - 1) * columns + column]
                body_b = bodies[row * columns + column]
                
                constraint_opts = dict(options) if options else {}
                constraint_opts['body_a'] = body_a
                constraint_opts['body_b'] = body_b
                
                Composite.add_constraint(composite, Constraint.create(constraint_opts))
            
            if cross_brace and column > 0 and row > 0:
                body_a = bodies[(row - 1) * columns + column - 1]
                body_b = bodies[row * columns + column]
                
                constraint_opts = dict(options) if options else {}
                constraint_opts['body_a'] = body_a
                constraint_opts['body_b'] = body_b
                
                Composite.add_constraint(composite, Constraint.create(constraint_opts))
                
                body_a = bodies[(row - 1) * columns + column]
                body_b = bodies[row * columns + column - 1]
                
                constraint_opts = dict(options) if options else {}
                constraint_opts['body_a'] = body_a
                constraint_opts['body_b'] = body_b
                
                Composite.add_constraint(composite, Constraint.create(constraint_opts))
    
    return composite
