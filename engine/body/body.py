import math
from typing import Dict, Any, List, Optional

from ..geometry import vector as Vector
from ..geometry import vertices as Vertices
from ..geometry import bounds as Bounds
from ..geometry import axes as Axes
from ..core import common as Common


# Module constants
_time_correction = True
_inertia_scale = 4
_next_colliding_group_id = 1
_next_non_colliding_group_id = -1
_next_category = 0x0001
_base_delta = 1000 / 60


def create(options: Optional[Dict] = None) -> Dict:
    """
    Creates a new rigid body model.
    All properties have default values, and many are pre-calculated automatically.
    Vertices must be specified in clockwise order.
    """
    options = options or {}
    
    defaults = {
        'id': Common.next_id(),
        'type': 'body',
        'label': 'Body',
        'parts': [],
        'plugin': {},
        'angle': 0,
        'vertices': Vertices.from_path('L 0 0 L 40 0 L 40 40 L 0 40'),
        'position': {'x': 0, 'y': 0},
        'force': {'x': 0, 'y': 0},
        'torque': 0,
        'position_impulse': {'x': 0, 'y': 0},
        'constraint_impulse': {'x': 0, 'y': 0, 'angle': 0},
        'total_contacts': 0,
        'speed': 0,
        'angular_speed': 0,
        'velocity': {'x': 0, 'y': 0},
        'angular_velocity': 0,
        'is_sensor': False,
        'is_static': False,
        'is_sleeping': False,
        'motion': 0,
        'sleep_threshold': 60,
        'density': 0.001,
        'restitution': 0,
        'friction': 0.1,
        'friction_static': 0.5,
        'friction_air': 0.01,
        'collision_filter': {
            'category': 0x0001,
            'mask': 0xFFFFFFFF,
            'group': 0
        },
        'slop': 0.05,
        'time_scale': 1,
        'render': {
            'visible': True,
            'opacity': 1,
            'stroke_style': None,
            'fill_style': None,
            'line_width': None,
            'sprite': {
                'x_scale': 1,
                'y_scale': 1,
                'x_offset': 0,
                'y_offset': 0
            }
        },
        'events': None,
        'bounds': None,
        'chamfer': None,
        'circle_radius': 0,
        'position_prev': None,
        'angle_prev': 0,
        'parent': None,
        'axes': None,
        'area': 0,
        'mass': 0,
        'inertia': 0,
        'delta_time': 1000 / 60,
        '_original': None
    }
    
    body = Common.extend(defaults, options)
    _init_properties(body, options)
    
    return body


def next_group(is_non_colliding: bool = False) -> int:
    """
    Returns the next unique group index for which bodies will collide.
    If is_non_colliding is True, returns a group index for which bodies will NOT collide.
    """
    global _next_colliding_group_id, _next_non_colliding_group_id
    
    if is_non_colliding:
        result = _next_non_colliding_group_id
        _next_non_colliding_group_id -= 1
        return result
    
    result = _next_colliding_group_id
    _next_colliding_group_id += 1
    return result


def next_category() -> int:
    """Returns the next unique category bitfield."""
    global _next_category
    _next_category = _next_category << 1
    return _next_category


def _init_properties(body: Dict, options: Optional[Dict] = None) -> None:
    """Initialises body properties."""
    options = options or {}
    
    # Init required properties (order is important)
    set_prop(body, {
        'bounds': body['bounds'] or Bounds.create(body['vertices']),
        'position_prev': body['position_prev'] or Vector.clone(body['position']),
        'angle_prev': body['angle_prev'] or body['angle'],
        'vertices': body['vertices'],
        'parts': body['parts'] or [body],
        'is_static': body['is_static'],
        'is_sleeping': body['is_sleeping'],
        'parent': body['parent'] or body
    })
    
    Vertices.rotate(body['vertices'], body['angle'], body['position'])
    Axes.rotate(body['axes'], body['angle'])
    Bounds.update(body['bounds'], body['vertices'], body['velocity'])
    
    # Allow options to override automatically calculated properties
    set_prop(body, {
        'axes': options.get('axes') or body['axes'],
        'area': options.get('area') or body['area'],
        'mass': options.get('mass') or body['mass'],
        'inertia': options.get('inertia') or body['inertia']
    })
    
    # Render properties
    default_fill = '#14151f' if body['is_static'] else Common.choose(['#f19648', '#f5d259', '#f55a3c', '#063e7b', '#ececd1'])
    default_stroke = '#555' if body['is_static'] else '#ccc'
    default_line_width = 1 if body['is_static'] and body['render']['fill_style'] is None else 0
    
    body['render']['fill_style'] = body['render']['fill_style'] or default_fill
    body['render']['stroke_style'] = body['render']['stroke_style'] or default_stroke
    body['render']['line_width'] = body['render']['line_width'] if body['render']['line_width'] is not None else default_line_width


def set_prop(body: Dict, settings: Any, value: Any = None) -> None:
    """
    Sets the property(s) on the body, using appropriate setter functions if they exist.
    """
    if isinstance(settings, str):
        prop = settings
        settings = {prop: value}
    
    for prop, val in settings.items():
        if prop == 'is_static':
            set_static(body, val)
        elif prop == 'is_sleeping':
            # Will be handled by sleeping module
            body['is_sleeping'] = val
        elif prop == 'mass':
            set_mass(body, val)
        elif prop == 'density':
            set_density(body, val)
        elif prop == 'inertia':
            set_inertia(body, val)
        elif prop == 'vertices':
            set_vertices(body, val)
        elif prop == 'position':
            set_position(body, val)
        elif prop == 'angle':
            set_angle(body, val)
        elif prop == 'velocity':
            set_velocity(body, val)
        elif prop == 'angular_velocity':
            set_angular_velocity(body, val)
        elif prop == 'speed':
            set_speed(body, val)
        elif prop == 'angular_speed':
            set_angular_speed(body, val)
        elif prop == 'parts':
            set_parts(body, val)
        elif prop == 'centre':
            set_centre(body, val)
        else:
            body[prop] = val


def set_static(body: Dict, is_static: bool) -> None:
    """Sets the body as static, including mass and inertia to Infinity."""
    for part in body['parts']:
        if is_static:
            if not part['is_static']:
                part['_original'] = {
                    'restitution': part['restitution'],
                    'friction': part['friction'],
                    'mass': part['mass'],
                    'inertia': part['inertia'],
                    'density': part['density'],
                    'inverse_mass': part.get('inverse_mass', 0),
                    'inverse_inertia': part.get('inverse_inertia', 0)
                }
            
            part['restitution'] = 0
            part['friction'] = 1
            part['mass'] = float('inf')
            part['inertia'] = float('inf')
            part['density'] = float('inf')
            part['inverse_mass'] = 0
            part['inverse_inertia'] = 0
            
            part['position_prev']['x'] = part['position']['x']
            part['position_prev']['y'] = part['position']['y']
            part['angle_prev'] = part['angle']
            part['angular_velocity'] = 0
            part['speed'] = 0
            part['angular_speed'] = 0
            part['motion'] = 0
        elif part.get('_original'):
            part['restitution'] = part['_original']['restitution']
            part['friction'] = part['_original']['friction']
            part['mass'] = part['_original']['mass']
            part['inertia'] = part['_original']['inertia']
            part['density'] = part['_original']['density']
            part['inverse_mass'] = part['_original']['inverse_mass']
            part['inverse_inertia'] = part['_original']['inverse_inertia']
            part['_original'] = None
        
        part['is_static'] = is_static


def set_mass(body: Dict, mass: float) -> None:
    """Sets the mass of the body. Inverse mass, density and inertia are updated."""
    moment = body['inertia'] / (body['mass'] / 6) if body['mass'] != 0 else 0
    body['inertia'] = moment * (mass / 6)
    body['inverse_inertia'] = 1 / body['inertia'] if body['inertia'] != 0 else 0
    
    body['mass'] = mass
    body['inverse_mass'] = 1 / body['mass'] if body['mass'] != 0 else 0
    body['density'] = body['mass'] / body['area'] if body['area'] != 0 else 0


def set_density(body: Dict, density: float) -> None:
    """Sets the density of the body. Mass and inertia are automatically updated."""
    set_mass(body, density * body['area'])
    body['density'] = density


def set_inertia(body: Dict, inertia: float) -> None:
    """Sets the moment of inertia of the body."""
    body['inertia'] = inertia
    body['inverse_inertia'] = 1 / body['inertia'] if body['inertia'] != 0 else 0


def set_vertices(body: Dict, vertices: List[Dict]) -> None:
    """
    Sets the body's vertices and updates body properties accordingly.
    Vertices will be automatically transformed to be around their centre of mass.
    """
    # Change vertices
    if vertices and vertices[0].get('body') == body:
        body['vertices'] = vertices
    else:
        body['vertices'] = Vertices.create(vertices, body)
    
    # Update properties
    body['axes'] = Axes.from_vertices(body['vertices'])
    body['area'] = Vertices.area(body['vertices'])
    set_mass(body, body['density'] * body['area'])
    
    # Orient vertices around the centre of mass at origin (0, 0)
    centre = Vertices.centre(body['vertices'])
    Vertices.translate(body['vertices'], centre, -1)
    
    # Update inertia while vertices are at origin
    set_inertia(body, _inertia_scale * Vertices.inertia(body['vertices'], body['mass']))
    
    # Update geometry
    Vertices.translate(body['vertices'], body['position'])
    Bounds.update(body['bounds'], body['vertices'], body['velocity'])


def set_parts(body: Dict, parts: List[Dict], auto_hull: bool = True) -> None:
    """
    Sets the parts of the body.
    Updates mass, inertia and centroid based on the parts geometry.
    """
    # Add all the parts, ensuring first part is always the parent body
    parts = list(parts)
    body['parts'] = [body]
    body['parent'] = body
    
    for part in parts:
        if part != body:
            part['parent'] = body
            body['parts'].append(part)
    
    if len(body['parts']) == 1:
        return
    
    if auto_hull:
        # Find the convex hull of all parts
        vertices = []
        for part in parts:
            vertices.extend(part['vertices'])
        
        Vertices.clockwise_sort(vertices)
        hull = Vertices.hull(vertices)
        hull_centre = Vertices.centre(hull)
        
        set_vertices(body, hull)
        Vertices.translate(body['vertices'], hull_centre)
    
    # Sum the properties of all compound parts
    total = _total_properties(body)
    
    body['area'] = total['area']
    body['parent'] = body
    body['position']['x'] = total['centre']['x']
    body['position']['y'] = total['centre']['y']
    body['position_prev']['x'] = total['centre']['x']
    body['position_prev']['y'] = total['centre']['y']
    
    set_mass(body, total['mass'])
    set_inertia(body, total['inertia'])
    set_position(body, total['centre'])


def set_centre(body: Dict, centre: Dict, relative: bool = False) -> None:
    """
    Sets the centre of mass of the body.
    This is equal to moving position but not the vertices.
    """
    if not relative:
        body['position_prev']['x'] = centre['x'] - (body['position']['x'] - body['position_prev']['x'])
        body['position_prev']['y'] = centre['y'] - (body['position']['y'] - body['position_prev']['y'])
        body['position']['x'] = centre['x']
        body['position']['y'] = centre['y']
    else:
        body['position_prev']['x'] += centre['x']
        body['position_prev']['y'] += centre['y']
        body['position']['x'] += centre['x']
        body['position']['y'] += centre['y']


def set_position(body: Dict, position: Dict, update_velocity: bool = False) -> None:
    """Sets the position of the body."""
    delta = Vector.sub(position, body['position'])
    
    if update_velocity:
        body['position_prev']['x'] = body['position']['x']
        body['position_prev']['y'] = body['position']['y']
        body['velocity']['x'] = delta['x']
        body['velocity']['y'] = delta['y']
        body['speed'] = Vector.magnitude(delta)
    else:
        body['position_prev']['x'] += delta['x']
        body['position_prev']['y'] += delta['y']
    
    for part in body['parts']:
        part['position']['x'] += delta['x']
        part['position']['y'] += delta['y']
        Vertices.translate(part['vertices'], delta)
        Bounds.update(part['bounds'], part['vertices'], body['velocity'])


def set_angle(body: Dict, angle: float, update_velocity: bool = False) -> None:
    """Sets the angle of the body."""
    delta = angle - body['angle']
    
    if update_velocity:
        body['angle_prev'] = body['angle']
        body['angular_velocity'] = delta
        body['angular_speed'] = abs(delta)
    else:
        body['angle_prev'] += delta
    
    for i, part in enumerate(body['parts']):
        part['angle'] += delta
        Vertices.rotate(part['vertices'], delta, body['position'])
        Axes.rotate(part['axes'], delta)
        Bounds.update(part['bounds'], part['vertices'], body['velocity'])
        if i > 0:
            Vector.rotate_about(part['position'], delta, body['position'], part['position'])


def set_velocity(body: Dict, velocity: Dict) -> None:
    """Sets the current linear velocity of the body."""
    time_scale = body['delta_time'] / _base_delta
    body['position_prev']['x'] = body['position']['x'] - velocity['x'] * time_scale
    body['position_prev']['y'] = body['position']['y'] - velocity['y'] * time_scale
    body['velocity']['x'] = (body['position']['x'] - body['position_prev']['x']) / time_scale
    body['velocity']['y'] = (body['position']['y'] - body['position_prev']['y']) / time_scale
    body['speed'] = Vector.magnitude(body['velocity'])


def get_velocity(body: Dict) -> Dict:
    """Gets the current linear velocity of the body."""
    time_scale = _base_delta / body['delta_time']
    return {
        'x': (body['position']['x'] - body['position_prev']['x']) * time_scale,
        'y': (body['position']['y'] - body['position_prev']['y']) * time_scale
    }


def get_speed(body: Dict) -> float:
    """Gets the current linear speed of the body."""
    return Vector.magnitude(get_velocity(body))


def set_speed(body: Dict, speed: float) -> None:
    """Sets the current linear speed of the body."""
    set_velocity(body, Vector.mult(Vector.normalise(get_velocity(body)), speed))


def set_angular_velocity(body: Dict, velocity: float) -> None:
    """Sets the current rotational velocity of the body."""
    time_scale = body['delta_time'] / _base_delta
    body['angle_prev'] = body['angle'] - velocity * time_scale
    body['angular_velocity'] = (body['angle'] - body['angle_prev']) / time_scale
    body['angular_speed'] = abs(body['angular_velocity'])


def get_angular_velocity(body: Dict) -> float:
    """Gets the current rotational velocity of the body."""
    return (body['angle'] - body['angle_prev']) * _base_delta / body['delta_time']


def get_angular_speed(body: Dict) -> float:
    """Gets the current rotational speed of the body."""
    return abs(get_angular_velocity(body))


def set_angular_speed(body: Dict, speed: float) -> None:
    """Sets the current rotational speed of the body."""
    set_angular_velocity(body, Common.sign(get_angular_velocity(body)) * speed)


def translate(body: Dict, translation: Dict, update_velocity: bool = False) -> None:
    """Moves a body by a given vector relative to its current position."""
    set_position(body, Vector.add(body['position'], translation), update_velocity)


def rotate(body: Dict, rotation: float, point: Optional[Dict] = None, update_velocity: bool = False) -> None:
    """Rotates a body by a given angle relative to its current angle."""
    if point is None:
        set_angle(body, body['angle'] + rotation, update_velocity)
    else:
        cos_a = math.cos(rotation)
        sin_a = math.sin(rotation)
        dx = body['position']['x'] - point['x']
        dy = body['position']['y'] - point['y']
        
        set_position(body, {
            'x': point['x'] + (dx * cos_a - dy * sin_a),
            'y': point['y'] + (dx * sin_a + dy * cos_a)
        }, update_velocity)
        
        set_angle(body, body['angle'] + rotation, update_velocity)


def scale(body: Dict, scale_x: float, scale_y: float, point: Optional[Dict] = None) -> None:
    """Scales the body, including updating physical properties."""
    total_area = 0
    total_inertia = 0
    
    if point is None:
        point = body['position']
    
    for i, part in enumerate(body['parts']):
        # Scale vertices
        Vertices.scale(part['vertices'], scale_x, scale_y, point)
        
        # Update properties
        part['axes'] = Axes.from_vertices(part['vertices'])
        part['area'] = Vertices.area(part['vertices'])
        set_mass(part, body['density'] * part['area'])
        
        # Update inertia (requires vertices to be at origin)
        Vertices.translate(part['vertices'], {'x': -part['position']['x'], 'y': -part['position']['y']})
        set_inertia(part, _inertia_scale * Vertices.inertia(part['vertices'], part['mass']))
        Vertices.translate(part['vertices'], {'x': part['position']['x'], 'y': part['position']['y']})
        
        if i > 0:
            total_area += part['area']
            total_inertia += part['inertia']
        
        # Scale position
        part['position']['x'] = point['x'] + (part['position']['x'] - point['x']) * scale_x
        part['position']['y'] = point['y'] + (part['position']['y'] - point['y']) * scale_y
        
        # Update bounds
        Bounds.update(part['bounds'], part['vertices'], body['velocity'])
    
    # Handle parent body
    if len(body['parts']) > 1:
        body['area'] = total_area
        
        if not body['is_static']:
            set_mass(body, body['density'] * total_area)
            set_inertia(body, total_inertia)
    
    # Handle circles
    if body['circle_radius']:
        if scale_x == scale_y:
            body['circle_radius'] *= scale_x
        else:
            body['circle_radius'] = None


def update(body: Dict, delta_time: Optional[float] = None) -> None:
    """
    Performs an update by integrating the equations of motion on the body.
    Uses Verlet integration for stability.
    """
    delta_time = (delta_time if delta_time is not None else (1000 / 60)) * body['time_scale']
    
    delta_time_squared = delta_time * delta_time
    correction = delta_time / (body['delta_time'] or delta_time) if _time_correction else 1
    
    # From the previous step
    friction_air = 1 - body['friction_air'] * (delta_time / Common._base_delta)
    velocity_prev_x = (body['position']['x'] - body['position_prev']['x']) * correction
    velocity_prev_y = (body['position']['y'] - body['position_prev']['y']) * correction
    
    # Update velocity with Verlet integration
    body['velocity']['x'] = (velocity_prev_x * friction_air) + (body['force']['x'] / body['mass']) * delta_time_squared
    body['velocity']['y'] = (velocity_prev_y * friction_air) + (body['force']['y'] / body['mass']) * delta_time_squared
    
    body['position_prev']['x'] = body['position']['x']
    body['position_prev']['y'] = body['position']['y']
    body['position']['x'] += body['velocity']['x']
    body['position']['y'] += body['velocity']['y']
    body['delta_time'] = delta_time
    
    # Update angular velocity with Verlet integration
    body['angular_velocity'] = ((body['angle'] - body['angle_prev']) * friction_air * correction) + \
                               (body['torque'] / body['inertia']) * delta_time_squared
    body['angle_prev'] = body['angle']
    body['angle'] += body['angular_velocity']
    
    # Transform the body geometry
    for i, part in enumerate(body['parts']):
        Vertices.translate(part['vertices'], body['velocity'])
        
        if i > 0:
            part['position']['x'] += body['velocity']['x']
            part['position']['y'] += body['velocity']['y']
        
        if body['angular_velocity'] != 0:
            Vertices.rotate(part['vertices'], body['angular_velocity'], body['position'])
            Axes.rotate(part['axes'], body['angular_velocity'])
            if i > 0:
                Vector.rotate_about(part['position'], body['angular_velocity'], body['position'], part['position'])
        
        Bounds.update(part['bounds'], part['vertices'], body['velocity'])


def update_velocities(body: Dict) -> None:
    """
    Updates velocity, speed, angular_velocity and angular_speed properties
    which are normalised in relation to _base_delta.
    """
    time_scale = _base_delta / body['delta_time']
    
    body['velocity']['x'] = (body['position']['x'] - body['position_prev']['x']) * time_scale
    body['velocity']['y'] = (body['position']['y'] - body['position_prev']['y']) * time_scale
    body['speed'] = math.sqrt(body['velocity']['x'] ** 2 + body['velocity']['y'] ** 2)
    
    body['angular_velocity'] = (body['angle'] - body['angle_prev']) * time_scale
    body['angular_speed'] = abs(body['angular_velocity'])


def apply_force(body: Dict, position: Dict, force: Dict) -> None:
    """
    Applies the force to the body from the force origin position in world-space.
    """
    offset = {'x': position['x'] - body['position']['x'], 'y': position['y'] - body['position']['y']}
    body['force']['x'] += force['x']
    body['force']['y'] += force['y']
    body['torque'] += offset['x'] * force['y'] - offset['y'] * force['x']


def _total_properties(body: Dict) -> Dict:
    """Returns the sums of the properties of all compound parts."""
    properties = {
        'mass': 0,
        'area': 0,
        'inertia': 0,
        'centre': {'x': 0, 'y': 0}
    }
    
    # Sum the properties of all compound parts
    start_idx = 0 if len(body['parts']) == 1 else 1
    for i in range(start_idx, len(body['parts'])):
        part = body['parts'][i]
        mass = part['mass'] if part['mass'] != float('inf') else 1
        
        properties['mass'] += mass
        properties['area'] += part['area']
        properties['inertia'] += part['inertia']
        properties['centre'] = Vector.add(properties['centre'], Vector.mult(part['position'], mass))
    
    properties['centre'] = Vector.div(properties['centre'], properties['mass'])
    
    return properties
