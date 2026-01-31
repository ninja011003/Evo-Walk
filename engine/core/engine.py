from typing import Dict, Any, List, Optional

from . import common as Common
from . import events as Events
from . import sleeping as Sleeping
from ..body import body as Body
from ..body import composite as Composite
from ..collision import detector as Detector
from ..collision import pairs as Pairs
from ..collision import resolver as Resolver
from ..constraint import constraint as Constraint


# Module constants
_base_delta = 1000 / 60


def create(options: Optional[Dict] = None) -> Dict:
    """Creates a new engine."""
    options = options or {}
    
    defaults = {
        'position_iterations': 6,
        'velocity_iterations': 4,
        'constraint_iterations': 2,
        'enable_sleeping': False,
        'events': {},
        'plugin': {},
        'gravity': {
            'x': 0,
            'y': 1,
            'scale': 0.001
        },
        'timing': {
            'timestamp': 0,
            'time_scale': 1,
            'last_delta': 0,
            'last_elapsed': 0
        }
    }
    
    engine = Common.extend(defaults, options)
    
    engine['world'] = options.get('world') or Composite.create({'label': 'World'})
    engine['pairs'] = options.get('pairs') or Pairs.create()
    engine['detector'] = options.get('detector') or Detector.create()
    
    return engine


def update(engine: Dict, delta: float = None) -> Dict:
    """
    Moves the simulation forward in time by delta.
    Uses Verlet integration for body physics and Gauss-Siedel for constraints.
    """
    delta = delta if delta is not None else _base_delta
    
    world = engine['world']
    timing = engine['timing']
    detector = engine['detector']
    pairs = engine['pairs']
    
    # Increment timestamp
    timing['timestamp'] += delta * timing['time_scale']
    timing['last_delta'] = delta * timing['time_scale']
    
    # Fire beforeUpdate event
    Events.trigger(engine, 'beforeUpdate', {'timestamp': timing['timestamp'], 'delta': delta})
    
    # Get all bodies and constraints (flatten composite hierarchy)
    all_bodies = Composite.all_bodies(world)
    all_constraints = Composite.all_constraints(world)
    
    # Update detector bodies
    Detector.set_bodies(detector, all_bodies)
    
    # Apply gravity to all bodies
    _bodies_apply_gravity(all_bodies, engine['gravity'])
    
    # Update all bodies
    for body in all_bodies:
        if body.get('is_static', False) or body.get('is_sleeping', False):
            continue
        Body.update(body, delta)
    
    # Update all constraints (pre-solve)
    Constraint.pre_solve_all(all_bodies)
    
    for _ in range(engine['constraint_iterations']):
        Constraint.solve_all(all_constraints, delta)
    
    Constraint.post_solve_all(all_bodies)
    
    # Find all collisions (broadphase + narrow-phase)
    detector['pairs'] = pairs
    collisions = Detector.collisions(detector)
    
    # Update collision pairs
    Pairs.update(pairs, collisions, timing['timestamp'])
    
    # Wake sleeping bodies on collision start
    if engine['enable_sleeping']:
        Sleeping.after_collisions(pairs['collision_start'])
    
    # Fire collision events
    if pairs['collision_start']:
        Events.trigger(engine, 'collisionStart', {'pairs': pairs['collision_start']})
    
    # Solve position
    Resolver.pre_solve_position(pairs['list'])
    
    for _ in range(engine['position_iterations']):
        Resolver.solve_position(pairs['list'], delta)
    
    Resolver.post_solve_position(all_bodies)
    
    # Solve velocity (pre-solve for warm start)
    Resolver.pre_solve_velocity(pairs['list'])
    
    for _ in range(engine['velocity_iterations']):
        Resolver.solve_velocity(pairs['list'], delta)
    
    # Update sleeping state
    if engine['enable_sleeping']:
        Sleeping.update(all_bodies, delta)
    
    # Fire collision events
    if pairs['collision_active']:
        Events.trigger(engine, 'collisionActive', {'pairs': pairs['collision_active']})
    
    if pairs['collision_end']:
        Events.trigger(engine, 'collisionEnd', {'pairs': pairs['collision_end']})
    
    # Update body velocities
    for body in all_bodies:
        Body.update_velocities(body)
    
    # Clear all forces
    _bodies_clear_forces(all_bodies)
    
    # Fire afterUpdate event
    Events.trigger(engine, 'afterUpdate', {'timestamp': timing['timestamp'], 'delta': delta})
    
    return engine


def merge(engine_a: Dict, engine_b: Dict) -> None:
    """Merges two engines by keeping the configuration of engineA but adding the bodies from engineB."""
    bodies = Composite.all_bodies(engine_b['world'])
    
    for body in bodies:
        Composite.add(engine_a['world'], body)


def clear(engine: Dict) -> None:
    """Clears the engine including the world and all pairs."""
    Pairs.clear(engine['pairs'])
    Detector.clear(engine['detector'])


def _bodies_apply_gravity(bodies: List[Dict], gravity: Dict) -> None:
    """Applies gravitational acceleration to all given bodies."""
    gravity_x = (gravity.get('x', 0) or 0) * gravity.get('scale', 0.001)
    gravity_y = (gravity.get('y', 1) or 0) * gravity.get('scale', 0.001)
    
    if gravity_x == 0 and gravity_y == 0:
        return
    
    for body in bodies:
        if body.get('is_static', False) or body.get('is_sleeping', False):
            continue
        
        # Apply gravity as a force
        body['force']['x'] += body['mass'] * gravity_x
        body['force']['y'] += body['mass'] * gravity_y


def _bodies_clear_forces(bodies: List[Dict]) -> None:
    """Clears force accumulator on all bodies."""
    for body in bodies:
        body['force']['x'] = 0
        body['force']['y'] = 0
        body['torque'] = 0
