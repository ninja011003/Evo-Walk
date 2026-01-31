import math
from typing import Dict, Any, List, Optional

from ..geometry import vertices as Vertices
from ..geometry import bounds as Bounds
from ..core import common as Common


# Module constants
_resting_thresh = 2
_resting_thresh_tangent = math.sqrt(6)
_position_dampen = 0.9
_position_warming = 0.8
_friction_normal_multiplier = 5
_friction_max_static = float('inf')
_base_delta = 1000 / 60


def pre_solve_position(pairs: List[Dict]) -> None:
    """Prepare pairs for position solving by counting total contacts on each body."""
    for pair in pairs:
        if not pair.get('is_active', False):
            continue
        
        contact_count = pair.get('contact_count', 1)
        collision = pair['collision']
        
        # Use parent bodies for contact counting
        parent_a = collision['parent_a']
        parent_b = collision['parent_b']
        
        parent_a['total_contacts'] = parent_a.get('total_contacts', 0) + contact_count
        parent_b['total_contacts'] = parent_b.get('total_contacts', 0) + contact_count


def solve_position(pairs: List[Dict], delta: float, damping: float = 1) -> None:
    """Find a solution for pair positions."""
    position_dampen = _position_dampen * damping
    slop_dampen = Common.clamp(delta / _base_delta, 0, 1)
    
    # Find impulses required to resolve penetration
    for pair in pairs:
        if not pair.get('is_active', False) or pair.get('is_sensor', False):
            continue
        
        collision = pair['collision']
        body_a = collision['parent_a']
        body_b = collision['parent_b']
        normal = collision['normal']
        
        # Ensure position_impulse exists
        if 'position_impulse' not in body_a:
            body_a['position_impulse'] = {'x': 0, 'y': 0}
        if 'position_impulse' not in body_b:
            body_b['position_impulse'] = {'x': 0, 'y': 0}
        
        # Get current separation between body edges involved in collision
        pair['separation'] = (
            collision['depth'] + 
            normal['x'] * (body_b['position_impulse']['x'] - body_a['position_impulse']['x']) +
            normal['y'] * (body_b['position_impulse']['y'] - body_a['position_impulse']['y'])
        )
    
    for pair in pairs:
        if not pair.get('is_active', False) or pair.get('is_sensor', False):
            continue
        
        collision = pair['collision']
        body_a = collision['parent_a']
        body_b = collision['parent_b']
        normal = collision['normal']
        
        # Ensure position_impulse exists
        if 'position_impulse' not in body_a:
            body_a['position_impulse'] = {'x': 0, 'y': 0}
        if 'position_impulse' not in body_b:
            body_b['position_impulse'] = {'x': 0, 'y': 0}
        
        position_impulse = pair['separation'] - pair.get('slop', 0.05) * slop_dampen
        
        if body_a.get('is_static', False) or body_b.get('is_static', False):
            position_impulse *= 2
        
        if not (body_a.get('is_static', False) or body_a.get('is_sleeping', False)):
            total_contacts_a = body_a.get('total_contacts', 1)
            contact_share = position_dampen / total_contacts_a if total_contacts_a > 0 else position_dampen
            body_a['position_impulse']['x'] += normal['x'] * position_impulse * contact_share
            body_a['position_impulse']['y'] += normal['y'] * position_impulse * contact_share
        
        if not (body_b.get('is_static', False) or body_b.get('is_sleeping', False)):
            total_contacts_b = body_b.get('total_contacts', 1)
            contact_share = position_dampen / total_contacts_b if total_contacts_b > 0 else position_dampen
            body_b['position_impulse']['x'] -= normal['x'] * position_impulse * contact_share
            body_b['position_impulse']['y'] -= normal['y'] * position_impulse * contact_share


def post_solve_position(bodies: List[Dict]) -> None:
    """Apply position resolution."""
    for body in bodies:
        if 'position_impulse' not in body:
            body['position_impulse'] = {'x': 0, 'y': 0}
        position_impulse = body['position_impulse']
        position_impulse_x = position_impulse['x']
        position_impulse_y = position_impulse['y']
        velocity = body.get('velocity', {'x': 0, 'y': 0})
        
        # Reset contact count
        body['total_contacts'] = 0
        
        if position_impulse_x != 0 or position_impulse_y != 0:
            # Update body geometry
            for part in body.get('parts', [body]):
                Vertices.translate(part['vertices'], position_impulse)
                Bounds.update(part['bounds'], part['vertices'], velocity)
                part['position']['x'] += position_impulse_x
                part['position']['y'] += position_impulse_y
            
            # Move the body without changing velocity
            body['position_prev']['x'] += position_impulse_x
            body['position_prev']['y'] += position_impulse_y
            
            if position_impulse_x * velocity['x'] + position_impulse_y * velocity['y'] < 0:
                # Reset cached impulse if the body has velocity along it
                position_impulse['x'] = 0
                position_impulse['y'] = 0
            else:
                # Warm the next iteration
                position_impulse['x'] *= _position_warming
                position_impulse['y'] *= _position_warming


def pre_solve_velocity(pairs: List[Dict]) -> None:
    """Prepare pairs for velocity solving (warm start)."""
    for pair in pairs:
        if not pair.get('is_active', False) or pair.get('is_sensor', False):
            continue
        
        contacts = pair.get('contacts', [])
        contact_count = pair.get('contact_count', 0)
        collision = pair['collision']
        body_a = collision['parent_a']
        body_b = collision['parent_b']
        normal = collision['normal']
        tangent = collision['tangent']
        
        # Resolve each contact
        for j in range(min(contact_count, len(contacts))):
            contact = contacts[j]
            contact_vertex = contact.get('vertex')
            normal_impulse = contact.get('normal_impulse', 0)
            tangent_impulse = contact.get('tangent_impulse', 0)
            
            if contact_vertex and (normal_impulse != 0 or tangent_impulse != 0):
                # Total impulse from contact
                impulse_x = normal['x'] * normal_impulse + tangent['x'] * tangent_impulse
                impulse_y = normal['y'] * normal_impulse + tangent['y'] * tangent_impulse
                
                # Apply impulse from contact
                if not (body_a.get('is_static', False) or body_a.get('is_sleeping', False)):
                    body_a['position_prev']['x'] += impulse_x * body_a.get('inverse_mass', 0)
                    body_a['position_prev']['y'] += impulse_y * body_a.get('inverse_mass', 0)
                    body_a['angle_prev'] += body_a.get('inverse_inertia', 0) * (
                        (contact_vertex['x'] - body_a['position']['x']) * impulse_y -
                        (contact_vertex['y'] - body_a['position']['y']) * impulse_x
                    )
                
                if not (body_b.get('is_static', False) or body_b.get('is_sleeping', False)):
                    body_b['position_prev']['x'] -= impulse_x * body_b.get('inverse_mass', 0)
                    body_b['position_prev']['y'] -= impulse_y * body_b.get('inverse_mass', 0)
                    body_b['angle_prev'] -= body_b.get('inverse_inertia', 0) * (
                        (contact_vertex['x'] - body_b['position']['x']) * impulse_y -
                        (contact_vertex['y'] - body_b['position']['y']) * impulse_x
                    )


def solve_velocity(pairs: List[Dict], delta: float) -> None:
    """Find a solution for pair velocities."""
    time_scale = delta / _base_delta
    time_scale_squared = time_scale * time_scale
    time_scale_cubed = time_scale_squared * time_scale
    resting_thresh = -_resting_thresh * time_scale
    resting_thresh_tangent = _resting_thresh_tangent
    friction_normal_multiplier = _friction_normal_multiplier * time_scale
    friction_max_static = _friction_max_static
    
    for pair in pairs:
        if not pair.get('is_active', False) or pair.get('is_sensor', False):
            continue
        
        collision = pair.get('collision')
        if not collision:
            continue
        
        body_a = collision.get('parent_a')
        body_b = collision.get('parent_b')
        
        # Ensure bodies are valid
        if not body_a or not body_b or 'position' not in body_a or 'position' not in body_b:
            continue
        
        normal_x = collision['normal']['x']
        normal_y = collision['normal']['y']
        tangent_x = collision['tangent']['x']
        tangent_y = collision['tangent']['y']
        inverse_mass_total = pair.get('inverse_mass', 0)
        friction = pair.get('friction', 0.1) * pair.get('friction_static', 0.5) * friction_normal_multiplier
        contacts = pair.get('contacts', [])
        contact_count = pair.get('contact_count', 1)
        contact_share = 1 / contact_count if contact_count > 0 else 1
        
        # Get body velocities
        body_a_velocity_x = body_a['position']['x'] - body_a.get('position_prev', body_a['position'])['x']
        body_a_velocity_y = body_a['position']['y'] - body_a.get('position_prev', body_a['position'])['y']
        body_a_angular_velocity = body_a['angle'] - body_a.get('angle_prev', body_a['angle'])
        body_b_velocity_x = body_b['position']['x'] - body_b.get('position_prev', body_b['position'])['x']
        body_b_velocity_y = body_b['position']['y'] - body_b.get('position_prev', body_b['position'])['y']
        body_b_angular_velocity = body_b['angle'] - body_b.get('angle_prev', body_b['angle'])
        
        # Resolve each contact
        for j in range(min(contact_count, len(contacts))):
            contact = contacts[j]
            contact_vertex = contact.get('vertex')
            
            if not contact_vertex:
                continue
            
            offset_a_x = contact_vertex['x'] - body_a['position']['x']
            offset_a_y = contact_vertex['y'] - body_a['position']['y']
            offset_b_x = contact_vertex['x'] - body_b['position']['x']
            offset_b_y = contact_vertex['y'] - body_b['position']['y']
            
            velocity_point_a_x = body_a_velocity_x - offset_a_y * body_a_angular_velocity
            velocity_point_a_y = body_a_velocity_y + offset_a_x * body_a_angular_velocity
            velocity_point_b_x = body_b_velocity_x - offset_b_y * body_b_angular_velocity
            velocity_point_b_y = body_b_velocity_y + offset_b_x * body_b_angular_velocity
            
            relative_velocity_x = velocity_point_a_x - velocity_point_b_x
            relative_velocity_y = velocity_point_a_y - velocity_point_b_y
            
            normal_velocity = normal_x * relative_velocity_x + normal_y * relative_velocity_y
            tangent_velocity = tangent_x * relative_velocity_x + tangent_y * relative_velocity_y
            
            # Coulomb friction
            normal_overlap = pair.get('separation', 0) + normal_velocity
            normal_force = min(normal_overlap, 1)
            normal_force = 0 if normal_overlap < 0 else normal_force
            
            friction_limit = normal_force * friction
            
            if tangent_velocity < -friction_limit or tangent_velocity > friction_limit:
                max_friction = abs(tangent_velocity)
                tangent_impulse = pair.get('friction', 0.1) * (1 if tangent_velocity > 0 else -1) * time_scale_cubed
                
                if tangent_impulse < -max_friction:
                    tangent_impulse = -max_friction
                elif tangent_impulse > max_friction:
                    tangent_impulse = max_friction
            else:
                tangent_impulse = tangent_velocity
                max_friction = friction_max_static
            
            # Account for mass, inertia and contact offset
            o_a_c_n = offset_a_x * normal_y - offset_a_y * normal_x
            o_b_c_n = offset_b_x * normal_y - offset_b_y * normal_x
            share = contact_share / (
                inverse_mass_total + 
                body_a.get('inverse_inertia', 0) * o_a_c_n * o_a_c_n + 
                body_b.get('inverse_inertia', 0) * o_b_c_n * o_b_c_n
            )
            
            # Raw impulses
            normal_impulse = (1 + pair.get('restitution', 0)) * normal_velocity * share
            tangent_impulse *= share
            
            # Handle high velocity and resting collisions separately
            if normal_velocity < resting_thresh:
                # High normal velocity so clear cached contact normal impulse
                contact['normal_impulse'] = 0
            else:
                # Solve resting collision constraints using Erin Catto's method (GDC08)
                contact_normal_impulse = contact.get('normal_impulse', 0)
                contact['normal_impulse'] = contact_normal_impulse + normal_impulse
                if contact['normal_impulse'] > 0:
                    contact['normal_impulse'] = 0
                normal_impulse = contact['normal_impulse'] - contact_normal_impulse
            
            # Handle high velocity and resting collisions separately
            if tangent_velocity < -resting_thresh_tangent or tangent_velocity > resting_thresh_tangent:
                # High tangent velocity so clear cached contact tangent impulse
                contact['tangent_impulse'] = 0
            else:
                # Solve resting collision constraints
                contact_tangent_impulse = contact.get('tangent_impulse', 0)
                contact['tangent_impulse'] = contact_tangent_impulse + tangent_impulse
                if contact['tangent_impulse'] < -max_friction:
                    contact['tangent_impulse'] = -max_friction
                if contact['tangent_impulse'] > max_friction:
                    contact['tangent_impulse'] = max_friction
                tangent_impulse = contact['tangent_impulse'] - contact_tangent_impulse
            
            # Total impulse from contact
            impulse_x = normal_x * normal_impulse + tangent_x * tangent_impulse
            impulse_y = normal_y * normal_impulse + tangent_y * tangent_impulse
            
            # Apply impulse from contact
            if not (body_a.get('is_static', False) or body_a.get('is_sleeping', False)):
                body_a['position_prev']['x'] += impulse_x * body_a.get('inverse_mass', 0)
                body_a['position_prev']['y'] += impulse_y * body_a.get('inverse_mass', 0)
                body_a['angle_prev'] += (offset_a_x * impulse_y - offset_a_y * impulse_x) * body_a.get('inverse_inertia', 0)
            
            if not (body_b.get('is_static', False) or body_b.get('is_sleeping', False)):
                body_b['position_prev']['x'] -= impulse_x * body_b.get('inverse_mass', 0)
                body_b['position_prev']['y'] -= impulse_y * body_b.get('inverse_mass', 0)
                body_b['angle_prev'] -= (offset_b_x * impulse_y - offset_b_y * impulse_x) * body_b.get('inverse_inertia', 0)
