from typing import Dict, Any, List, Optional

from ..core import common as Common
from . import collision as Collision


def create(options: Optional[Dict] = None) -> Dict:
    """Creates a new collision detector."""
    options = options or {}
    
    defaults = {
        'bodies': [],
        'collisions': [],
        'pairs': None
    }
    
    return Common.extend(defaults, options)


def set_bodies(detector: Dict, bodies: List[Dict]) -> None:
    """Sets the list of bodies in the detector."""
    detector['bodies'] = list(bodies)


def clear(detector: Dict) -> None:
    """Clears the detector including its list of bodies."""
    detector['bodies'] = []
    detector['collisions'] = []


def collisions(detector: Dict) -> List[Dict]:
    """
    Efficiently finds all collisions among all the bodies in detector.bodies
    using a broadphase algorithm (sweep and prune on x-axis).
    """
    pairs = detector['pairs']
    bodies = detector['bodies']
    bodies_length = len(bodies)
    collisions_list = detector['collisions']
    collision_index = 0
    
    # Sort bodies by bounds.min.x (sweep and prune)
    bodies.sort(key=lambda b: b['bounds']['min']['x'])
    
    for i in range(bodies_length):
        body_a = bodies[i]
        bounds_a = body_a['bounds']
        bound_x_max = bounds_a['max']['x']
        bound_y_max = bounds_a['max']['y']
        bound_y_min = bounds_a['min']['y']
        body_a_static = body_a.get('is_static', False) or body_a.get('is_sleeping', False)
        parts_a_length = len(body_a.get('parts', [body_a]))
        parts_a_single = parts_a_length == 1
        
        for j in range(i + 1, bodies_length):
            body_b = bodies[j]
            bounds_b = body_b['bounds']
            
            # Sweep: if body_b.bounds.min.x > bound_x_max, no more potential collisions
            if bounds_b['min']['x'] > bound_x_max:
                break
            
            # Prune: check y-axis overlap
            if bound_y_max < bounds_b['min']['y'] or bound_y_min > bounds_b['max']['y']:
                continue
            
            # Skip if both are static/sleeping
            if body_a_static and (body_b.get('is_static', False) or body_b.get('is_sleeping', False)):
                continue
            
            # Check collision filter
            if not can_collide(body_a.get('collision_filter', {}), body_b.get('collision_filter', {})):
                continue
            
            parts_b_length = len(body_b.get('parts', [body_b]))
            
            if parts_a_single and parts_b_length == 1:
                # Simple case: single part bodies
                collision = Collision.collides(body_a, body_b, pairs)
                
                if collision:
                    if collision_index < len(collisions_list):
                        collisions_list[collision_index] = collision
                    else:
                        collisions_list.append(collision)
                    collision_index += 1
            else:
                # Complex case: compound bodies
                parts_a_start = 1 if parts_a_length > 1 else 0
                parts_b_start = 1 if parts_b_length > 1 else 0
                
                for k in range(parts_a_start, parts_a_length):
                    part_a = body_a['parts'][k]
                    bounds_a_part = part_a['bounds']
                    
                    for z in range(parts_b_start, parts_b_length):
                        part_b = body_b['parts'][z]
                        bounds_b_part = part_b['bounds']
                        
                        # AABB check for parts
                        if (bounds_a_part['min']['x'] > bounds_b_part['max']['x'] or
                            bounds_a_part['max']['x'] < bounds_b_part['min']['x'] or
                            bounds_a_part['max']['y'] < bounds_b_part['min']['y'] or
                            bounds_a_part['min']['y'] > bounds_b_part['max']['y']):
                            continue
                        
                        collision = Collision.collides(part_a, part_b, pairs)
                        
                        if collision:
                            if collision_index < len(collisions_list):
                                collisions_list[collision_index] = collision
                            else:
                                collisions_list.append(collision)
                            collision_index += 1
    
    # Trim collisions list if needed
    if len(collisions_list) != collision_index:
        del collisions_list[collision_index:]
    
    return collisions_list


def can_collide(filter_a: Dict, filter_b: Dict) -> bool:
    """
    Returns True if both supplied collision filters will allow a collision to occur.
    """
    group_a = filter_a.get('group', 0)
    group_b = filter_b.get('group', 0)
    
    # Same group and non-zero: use group sign to determine collision
    if group_a == group_b and group_a != 0:
        return group_a > 0
    
    # Different groups or zero: use category/mask
    category_a = filter_a.get('category', 0x0001)
    category_b = filter_b.get('category', 0x0001)
    mask_a = filter_a.get('mask', 0xFFFFFFFF)
    mask_b = filter_b.get('mask', 0xFFFFFFFF)
    
    return (category_a & mask_b) != 0 and (category_b & mask_a) != 0
