from typing import Dict, Any, List, Optional, Callable

from ..core import common as Common


def create(options: Optional[Dict] = None) -> Dict:
    """Creates a new composite."""
    options = options or {}
    
    defaults = {
        'id': Common.next_id(),
        'type': 'composite',
        'parent': None,
        'is_modified': False,
        'bodies': [],
        'constraints': [],
        'composites': [],
        'label': 'Composite',
        'plugin': {},
        'cache': {
            'all_bodies': None,
            'all_constraints': None,
            'all_composites': None
        }
    }
    
    return Common.extend(defaults, options)


def set_modified(composite: Dict, is_modified: bool, update_parents: bool = False, update_children: bool = False) -> None:
    """
    Sets the modified flag on the composite and optionally up the tree or down.
    """
    composite['is_modified'] = is_modified
    
    # Invalidate cache
    if is_modified:
        composite['cache']['all_bodies'] = None
        composite['cache']['all_constraints'] = None
        composite['cache']['all_composites'] = None
    
    if update_parents and composite.get('parent'):
        set_modified(composite['parent'], is_modified, update_parents=True, update_children=False)
    
    if update_children:
        for child in composite['composites']:
            set_modified(child, is_modified, update_parents=False, update_children=True)


def add(composite: Dict, obj: Any, deep: bool = False) -> Dict:
    """
    Adds an object (body, constraint, or composite) to the given composite.
    Returns the composite for chaining.
    """
    # Handle lists
    if isinstance(obj, list):
        for item in obj:
            add(composite, item, deep)
        return composite
    
    obj_type = obj.get('type')
    
    if obj_type == 'body':
        # Check if already present
        if obj not in composite['bodies']:
            add_body(composite, obj)
    elif obj_type == 'constraint':
        if obj not in composite['constraints']:
            add_constraint(composite, obj)
    elif obj_type == 'composite':
        if obj not in composite['composites']:
            add_composite(composite, obj)
    
    return composite


def remove(composite: Dict, obj: Any, deep: bool = False) -> Dict:
    """
    Removes an object from the given composite.
    Returns the composite for chaining.
    """
    # Handle lists
    if isinstance(obj, list):
        for item in obj:
            remove(composite, item, deep)
        return composite
    
    obj_type = obj.get('type')
    
    if obj_type == 'body':
        remove_body(composite, obj, deep)
    elif obj_type == 'constraint':
        remove_constraint(composite, obj, deep)
    elif obj_type == 'composite':
        remove_composite(composite, obj, deep)
    
    return composite


def add_body(composite: Dict, body: Dict) -> Dict:
    """Adds a body to the given composite."""
    composite['bodies'].append(body)
    # Note: body['parent'] refers to parent body for compound bodies, not composite container
    # We track the composite via a separate property
    body['composite'] = composite
    set_modified(composite, True, update_parents=True, update_children=False)
    return composite


def remove_body(composite: Dict, body: Dict, deep: bool = False) -> Dict:
    """Removes a body from the given composite."""
    pos = -1
    try:
        pos = composite['bodies'].index(body)
    except ValueError:
        pass
    
    if pos != -1:
        remove_body_at(composite, pos)
    
    if deep:
        for child in composite['composites']:
            remove_body(child, body, deep=True)
    
    return composite


def remove_body_at(composite: Dict, position: int) -> Dict:
    """Removes a body at a given position from the composite."""
    composite['bodies'].pop(position)
    set_modified(composite, True, update_parents=True, update_children=False)
    return composite


def add_constraint(composite: Dict, constraint: Dict) -> Dict:
    """Adds a constraint to the given composite."""
    composite['constraints'].append(constraint)
    constraint['parent'] = composite
    set_modified(composite, True, update_parents=True, update_children=False)
    return composite


def remove_constraint(composite: Dict, constraint: Dict, deep: bool = False) -> Dict:
    """Removes a constraint from the given composite."""
    pos = -1
    try:
        pos = composite['constraints'].index(constraint)
    except ValueError:
        pass
    
    if pos != -1:
        remove_constraint_at(composite, pos)
    
    if deep:
        for child in composite['composites']:
            remove_constraint(child, constraint, deep=True)
    
    return composite


def remove_constraint_at(composite: Dict, position: int) -> Dict:
    """Removes a constraint at a given position from the composite."""
    composite['constraints'].pop(position)
    set_modified(composite, True, update_parents=True, update_children=False)
    return composite


def add_composite(composite: Dict, child: Dict) -> Dict:
    """Adds a composite to the given composite."""
    composite['composites'].append(child)
    child['parent'] = composite
    set_modified(composite, True, update_parents=True, update_children=False)
    return composite


def remove_composite(composite: Dict, child: Dict, deep: bool = False) -> Dict:
    """Removes a composite from the given composite."""
    pos = -1
    try:
        pos = composite['composites'].index(child)
    except ValueError:
        pass
    
    if pos != -1:
        remove_composite_at(composite, pos)
    
    if deep:
        for comp in composite['composites']:
            remove_composite(comp, child, deep=True)
    
    return composite


def remove_composite_at(composite: Dict, position: int) -> Dict:
    """Removes a composite at a given position from the composite."""
    composite['composites'].pop(position)
    set_modified(composite, True, update_parents=True, update_children=False)
    return composite


def all_bodies(composite: Dict) -> List[Dict]:
    """Returns all bodies (recursively) in the composite."""
    if composite['cache']['all_bodies']:
        return composite['cache']['all_bodies']
    
    bodies = list(composite['bodies'])
    
    for child in composite['composites']:
        bodies.extend(all_bodies(child))
    
    composite['cache']['all_bodies'] = bodies
    return bodies


def all_constraints(composite: Dict) -> List[Dict]:
    """Returns all constraints (recursively) in the composite."""
    if composite['cache']['all_constraints']:
        return composite['cache']['all_constraints']
    
    constraints = list(composite['constraints'])
    
    for child in composite['composites']:
        constraints.extend(all_constraints(child))
    
    composite['cache']['all_constraints'] = constraints
    return constraints


def all_composites(composite: Dict) -> List[Dict]:
    """Returns all composites (recursively) in the composite."""
    if composite['cache']['all_composites']:
        return composite['cache']['all_composites']
    
    composites = list(composite['composites'])
    
    for child in composite['composites']:
        composites.extend(all_composites(child))
    
    composite['cache']['all_composites'] = composites
    return composites


def get(composite: Dict, id_val: int, obj_type: str) -> Optional[Dict]:
    """Gets an object by id and type."""
    if obj_type == 'body':
        objects = all_bodies(composite)
    elif obj_type == 'constraint':
        objects = all_constraints(composite)
    elif obj_type == 'composite':
        objects = all_composites(composite)
        # Also check self
        if composite['id'] == id_val:
            return composite
    else:
        return None
    
    for obj in objects:
        if obj['id'] == id_val:
            return obj
    
    return None


def move(composite: Dict, objects: List[Dict], target_composite: Dict) -> Dict:
    """
    Moves objects from one composite to another.
    """
    for obj in objects:
        remove(composite, obj, deep=True)
        add(target_composite, obj)
    
    return composite


def rebase(composite: Dict) -> Dict:
    """
    Resets the IDs of all objects in the composite.
    """
    for body in all_bodies(composite):
        body['id'] = Common.next_id()
    
    for constraint in all_constraints(composite):
        constraint['id'] = Common.next_id()
    
    for comp in all_composites(composite):
        comp['id'] = Common.next_id()
    
    return composite


def translate(composite: Dict, translation: Dict, recursive: bool = True) -> None:
    """Translates all bodies in the composite by the given vector."""
    from . import body as Body
    
    bodies = all_bodies(composite) if recursive else composite['bodies']
    
    for body in bodies:
        Body.translate(body, translation)


def rotate(composite: Dict, rotation: float, point: Dict, recursive: bool = True) -> None:
    """Rotates all bodies in the composite about the given point."""
    from . import body as Body
    import math
    
    cos_a = math.cos(rotation)
    sin_a = math.sin(rotation)
    
    bodies = all_bodies(composite) if recursive else composite['bodies']
    
    for body in bodies:
        dx = body['position']['x'] - point['x']
        dy = body['position']['y'] - point['y']
        
        Body.set_position(body, {
            'x': point['x'] + (dx * cos_a - dy * sin_a),
            'y': point['y'] + (dx * sin_a + dy * cos_a)
        })
        
        Body.rotate(body, rotation)


def scale(composite: Dict, scale_x: float, scale_y: float, point: Dict, recursive: bool = True) -> None:
    """Scales all bodies in the composite from the given point."""
    from . import body as Body
    
    bodies = all_bodies(composite) if recursive else composite['bodies']
    
    for body in bodies:
        dx = body['position']['x'] - point['x']
        dy = body['position']['y'] - point['y']
        
        Body.set_position(body, {
            'x': point['x'] + dx * scale_x,
            'y': point['y'] + dy * scale_y
        })
        
        Body.scale(body, scale_x, scale_y)


def bounds(composite: Dict) -> Dict:
    """Returns the bounds of all bodies in the composite."""
    bodies = all_bodies(composite)
    vertices = []
    
    for body in bodies:
        vertices.append(body['bounds']['min'])
        vertices.append(body['bounds']['max'])
    
    from ..geometry import bounds as Bounds
    return Bounds.create(vertices)
