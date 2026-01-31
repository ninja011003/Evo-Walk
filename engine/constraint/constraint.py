import math
from typing import Dict, Any, List, Optional

from ..geometry import vector as Vector
from ..geometry import vertices as Vertices
from ..geometry import bounds as Bounds
from ..geometry import axes as Axes
from ..core import common as Common


# Module constants
_warming = 0.4
_torque_dampen = 1
_min_length = 0.000001
_base_delta = 1000 / 60


def create(options: Optional[Dict] = None) -> Dict:
    """
    Creates a new constraint.
    To simulate a revolute constraint (pin joint), set length: 0 and a high stiffness (0.7+).
    """
    options = options or {}
    constraint = dict(options)
    
    # If bodies defined but no points, use body centre
    if constraint.get('body_a') and not constraint.get('point_a'):
        constraint['point_a'] = {'x': 0, 'y': 0}
    if constraint.get('body_b') and not constraint.get('point_b'):
        constraint['point_b'] = {'x': 0, 'y': 0}
    
    # Calculate static length using initial world space points
    body_a = constraint.get('body_a')
    body_b = constraint.get('body_b')
    point_a = constraint.get('point_a')
    point_b = constraint.get('point_b')
    
    initial_point_a = Vector.add(body_a['position'], point_a) if body_a else point_a
    initial_point_b = Vector.add(body_b['position'], point_b) if body_b else point_b
    
    length = Vector.magnitude(Vector.sub(initial_point_a, initial_point_b)) if initial_point_a and initial_point_b else 0
    
    constraint['length'] = constraint.get('length') if 'length' in constraint else length
    
    # Option defaults
    constraint['id'] = constraint.get('id') or Common.next_id()
    constraint['label'] = constraint.get('label') or 'Constraint'
    constraint['type'] = 'constraint'
    constraint['stiffness'] = constraint.get('stiffness') if 'stiffness' in constraint else (1 if constraint['length'] > 0 else 0.7)
    constraint['damping'] = constraint.get('damping') if 'damping' in constraint else 0
    constraint['angular_stiffness'] = constraint.get('angular_stiffness') if 'angular_stiffness' in constraint else 0
    constraint['angle_a'] = body_a['angle'] if body_a else constraint.get('angle_a', 0)
    constraint['angle_b'] = body_b['angle'] if body_b else constraint.get('angle_b', 0)
    constraint['plugin'] = {}
    
    # Render options
    render = {
        'visible': True,
        'line_width': 2,
        'stroke_style': '#ffffff',
        'type': 'line',
        'anchors': True
    }
    
    if constraint['length'] == 0 and constraint['stiffness'] > 0.1:
        render['type'] = 'pin'
        render['anchors'] = False
    elif constraint['stiffness'] < 0.9:
        render['type'] = 'spring'
    
    constraint['render'] = Common.extend(render, constraint.get('render', {}))
    
    return constraint


def pre_solve_all(bodies: List[Dict]) -> None:
    """Prepares for solving by constraint warming."""
    for body in bodies:
        if 'constraint_impulse' not in body:
            body['constraint_impulse'] = {'x': 0, 'y': 0, 'angle': 0}
        impulse = body['constraint_impulse']
        
        if body.get('is_static', False) or (impulse['x'] == 0 and impulse['y'] == 0 and impulse['angle'] == 0):
            continue
        
        body['position']['x'] += impulse['x']
        body['position']['y'] += impulse['y']
        body['angle'] += impulse['angle']


def solve_all(constraints: List[Dict], delta: float) -> None:
    """Solves all constraints in a list."""
    time_scale = Common.clamp(delta / _base_delta, 0, 1)
    
    # Solve fixed constraints first
    for constraint in constraints:
        body_a = constraint.get('body_a')
        body_b = constraint.get('body_b')
        fixed_a = not body_a or (body_a and body_a.get('is_static', False))
        fixed_b = not body_b or (body_b and body_b.get('is_static', False))
        
        if fixed_a or fixed_b:
            solve(constraint, time_scale)
    
    # Solve free constraints last
    for constraint in constraints:
        body_a = constraint.get('body_a')
        body_b = constraint.get('body_b')
        fixed_a = not body_a or (body_a and body_a.get('is_static', False))
        fixed_b = not body_b or (body_b and body_b.get('is_static', False))
        
        if not fixed_a and not fixed_b:
            solve(constraint, time_scale)


def solve(constraint: Dict, time_scale: float) -> None:
    """Solves a distance constraint with Gauss-Siedel method."""
    body_a = constraint.get('body_a')
    body_b = constraint.get('body_b')
    point_a = constraint.get('point_a')
    point_b = constraint.get('point_b')
    
    if not body_a and not body_b:
        return
    
    # Update reference angle
    if body_a and not body_a.get('is_static', False):
        Vector.rotate(point_a, body_a['angle'] - constraint['angle_a'], point_a)
        constraint['angle_a'] = body_a['angle']
    
    # Update reference angle
    if body_b and not body_b.get('is_static', False):
        Vector.rotate(point_b, body_b['angle'] - constraint['angle_b'], point_b)
        constraint['angle_b'] = body_b['angle']
    
    point_a_world = point_a
    point_b_world = point_b
    
    if body_a:
        point_a_world = Vector.add(body_a['position'], point_a)
    if body_b:
        point_b_world = Vector.add(body_b['position'], point_b)
    
    if not point_a_world or not point_b_world:
        return
    
    delta = Vector.sub(point_a_world, point_b_world)
    current_length = Vector.magnitude(delta)
    
    # Prevent singularity
    if current_length < _min_length:
        current_length = _min_length
    
    # Solve distance constraint with Gauss-Siedel method
    difference = (current_length - constraint['length']) / current_length
    is_rigid = constraint['stiffness'] >= 1 or constraint['length'] == 0
    stiffness = constraint['stiffness'] * time_scale if is_rigid else constraint['stiffness'] * time_scale * time_scale
    damping = constraint['damping'] * time_scale
    force = Vector.mult(delta, difference * stiffness)
    mass_total = (body_a.get('inverse_mass', 0) if body_a else 0) + (body_b.get('inverse_mass', 0) if body_b else 0)
    inertia_total = (body_a.get('inverse_inertia', 0) if body_a else 0) + (body_b.get('inverse_inertia', 0) if body_b else 0)
    resistance_total = mass_total + inertia_total
    
    normal = None
    normal_velocity = 0
    relative_velocity = None
    
    if damping > 0:
        zero = Vector.create()
        normal = Vector.div(delta, current_length)
        
        relative_velocity = Vector.sub(
            Vector.sub(body_b['position'], body_b['position_prev']) if body_b else zero,
            Vector.sub(body_a['position'], body_a['position_prev']) if body_a else zero
        )
        
        normal_velocity = Vector.dot(normal, relative_velocity)
    
    if body_a and not body_a.get('is_static', False):
        share = body_a.get('inverse_mass', 0) / mass_total if mass_total != 0 else 0
        
        # Ensure constraint_impulse exists
        if 'constraint_impulse' not in body_a:
            body_a['constraint_impulse'] = {'x': 0, 'y': 0, 'angle': 0}
        
        # Keep track of applied impulses for post solving
        body_a['constraint_impulse']['x'] -= force['x'] * share
        body_a['constraint_impulse']['y'] -= force['y'] * share
        
        # Apply forces
        body_a['position']['x'] -= force['x'] * share
        body_a['position']['y'] -= force['y'] * share
        
        # Apply damping
        if damping > 0:
            body_a['position_prev']['x'] -= damping * normal['x'] * normal_velocity * share
            body_a['position_prev']['y'] -= damping * normal['y'] * normal_velocity * share
        
        # Apply torque
        torque = (Vector.cross(point_a, force) / resistance_total) * _torque_dampen * body_a.get('inverse_inertia', 0) * (1 - constraint['angular_stiffness'])
        body_a['constraint_impulse']['angle'] -= torque
        body_a['angle'] -= torque
    
    if body_b and not body_b.get('is_static', False):
        share = body_b.get('inverse_mass', 0) / mass_total if mass_total != 0 else 0
        
        # Ensure constraint_impulse exists
        if 'constraint_impulse' not in body_b:
            body_b['constraint_impulse'] = {'x': 0, 'y': 0, 'angle': 0}
        
        # Keep track of applied impulses for post solving
        body_b['constraint_impulse']['x'] += force['x'] * share
        body_b['constraint_impulse']['y'] += force['y'] * share
        
        # Apply forces
        body_b['position']['x'] += force['x'] * share
        body_b['position']['y'] += force['y'] * share
        
        # Apply damping
        if damping > 0:
            body_b['position_prev']['x'] += damping * normal['x'] * normal_velocity * share
            body_b['position_prev']['y'] += damping * normal['y'] * normal_velocity * share
        
        # Apply torque
        torque = (Vector.cross(point_b, force) / resistance_total) * _torque_dampen * body_b.get('inverse_inertia', 0) * (1 - constraint['angular_stiffness'])
        body_b['constraint_impulse']['angle'] += torque
        body_b['angle'] += torque


def post_solve_all(bodies: List[Dict]) -> None:
    """Performs body updates required after solving constraints."""
    for body in bodies:
        if 'constraint_impulse' not in body:
            body['constraint_impulse'] = {'x': 0, 'y': 0, 'angle': 0}
        impulse = body['constraint_impulse']
        
        if body.get('is_static', False) or (impulse['x'] == 0 and impulse['y'] == 0 and impulse['angle'] == 0):
            continue
        
        # Wake body if sleeping
        if body.get('is_sleeping', False):
            body['is_sleeping'] = False
        
        # Update geometry and reset
        for part in body.get('parts', [body]):
            Vertices.translate(part['vertices'], impulse)
            
            if part != body:
                part['position']['x'] += impulse['x']
                part['position']['y'] += impulse['y']
            
            if impulse['angle'] != 0:
                Vertices.rotate(part['vertices'], impulse['angle'], body['position'])
                Axes.rotate(part['axes'], impulse['angle'])
                if part != body:
                    Vector.rotate_about(part['position'], impulse['angle'], body['position'], part['position'])
            
            Bounds.update(part['bounds'], part['vertices'], body.get('velocity', {'x': 0, 'y': 0}))
        
        # Dampen the cached impulse for warming next step
        impulse['angle'] *= _warming
        impulse['x'] *= _warming
        impulse['y'] *= _warming


def point_a_world(constraint: Dict) -> Dict:
    """Returns the world-space position of constraint.point_a."""
    return {
        'x': (constraint['body_a']['position']['x'] if constraint.get('body_a') else 0) +
             (constraint['point_a']['x'] if constraint.get('point_a') else 0),
        'y': (constraint['body_a']['position']['y'] if constraint.get('body_a') else 0) +
             (constraint['point_a']['y'] if constraint.get('point_a') else 0)
    }


def point_b_world(constraint: Dict) -> Dict:
    """Returns the world-space position of constraint.point_b."""
    return {
        'x': (constraint['body_b']['position']['x'] if constraint.get('body_b') else 0) +
             (constraint['point_b']['x'] if constraint.get('point_b') else 0),
        'y': (constraint['body_b']['position']['y'] if constraint.get('body_b') else 0) +
             (constraint['point_b']['y'] if constraint.get('point_b') else 0)
    }


def current_length(constraint: Dict) -> float:
    """Returns the current length of the constraint."""
    point_a_x = (constraint['body_a']['position']['x'] if constraint.get('body_a') else 0) + \
                (constraint['point_a']['x'] if constraint.get('point_a') else 0)
    point_a_y = (constraint['body_a']['position']['y'] if constraint.get('body_a') else 0) + \
                (constraint['point_a']['y'] if constraint.get('point_a') else 0)
    point_b_x = (constraint['body_b']['position']['x'] if constraint.get('body_b') else 0) + \
                (constraint['point_b']['x'] if constraint.get('point_b') else 0)
    point_b_y = (constraint['body_b']['position']['y'] if constraint.get('body_b') else 0) + \
                (constraint['point_b']['y'] if constraint.get('point_b') else 0)
    
    delta_x = point_a_x - point_b_x
    delta_y = point_a_y - point_b_y
    
    return math.sqrt(delta_x * delta_x + delta_y * delta_y)
