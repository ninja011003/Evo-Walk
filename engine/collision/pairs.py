from typing import Dict, Any, List, Optional

from ..core import common as Common


def create(options: Optional[Dict] = None) -> Dict:
    """Creates a new pairs structure."""
    options = options or {}
    
    return {
        'table': {},
        'list': [],
        'collision_start': [],
        'collision_active': [],
        'collision_end': []
    }


def update(pairs: Dict, collisions: List[Dict], timestamp: float) -> None:
    """Updates pairs given a list of collisions."""
    pairs_table = pairs['table']
    pairs_list = pairs['list']
    collision_start = pairs['collision_start']
    collision_active = pairs['collision_active']
    collision_end = pairs['collision_end']
    
    # Clear collision state arrays
    collision_start.clear()
    collision_end.clear()
    collision_active.clear()
    
    # Mark all pairs as not active
    for pair in pairs_list:
        pair['confirmed'] = False
    
    # Process all collisions
    for i, collision in enumerate(collisions):
        pair_id = id_from_bodies(collision['parent_a'], collision['parent_b'])
        
        if pair_id in pairs_table:
            # Pair already exists
            pair = pairs_table[pair_id]
            
            if pair['is_active']:
                # Pair was active, still active
                collision_active.append(pair)
            else:
                # Pair was inactive, now starting
                collision_start.append(pair)
            
            # Update the pair
            pair['is_active'] = True
            pair['time_created'] = timestamp
            pair['time_updated'] = timestamp
            pair['collision'] = collision
            collision['pair'] = pair
            pair['inverse_mass'] = collision['parent_a'].get('inverse_mass', 0) + collision['parent_b'].get('inverse_mass', 0)
            pair['friction'] = min(collision['parent_a'].get('friction', 0.1), collision['parent_b'].get('friction', 0.1))
            pair['friction_static'] = max(collision['parent_a'].get('friction_static', 0.5), collision['parent_b'].get('friction_static', 0.5))
            pair['restitution'] = max(collision['parent_a'].get('restitution', 0), collision['parent_b'].get('restitution', 0))
            pair['slop'] = max(collision['parent_a'].get('slop', 0.05), collision['parent_b'].get('slop', 0.05))
            pair['confirmed'] = True
            
            # Update contacts from collision supports
            supports = collision.get('supports', [])
            support_count = collision.get('support_count', 0)
            pair['contact_count'] = support_count
            contacts = pair['contacts']
            for j in range(min(support_count, len(contacts))):
                contacts[j]['vertex'] = supports[j]
        else:
            # Create a new pair
            pair = _create_pair(collision, timestamp)
            pairs_table[pair_id] = pair
            collision_start.append(pair)
            pairs_list.append(pair)
    
    # Find pairs that have ended
    pairs_to_remove = []
    for pair in pairs_list:
        if not pair['confirmed']:
            # Pair no longer active
            pair['is_active'] = False
            collision_end.append(pair)
            
            # Clear contacts
            for contact in pair['contacts']:
                contact['normal_impulse'] = 0
                contact['tangent_impulse'] = 0
            
            # Mark for removal if old
            if timestamp - pair['time_updated'] > 1000:
                pairs_to_remove.append(pair)
    
    # Remove old pairs
    for pair in pairs_to_remove:
        pair_id = id_from_bodies(pair['collision']['parent_a'], pair['collision']['parent_b'])
        if pair_id in pairs_table:
            del pairs_table[pair_id]
        pairs_list.remove(pair)


def _create_pair(collision: Dict, timestamp: float) -> Dict:
    """Creates a new pair from a collision."""
    body_a = collision['body_a']
    body_b = collision['body_b']
    parent_a = collision['parent_a']
    parent_b = collision['parent_b']
    
    # Get supports from collision
    supports = collision.get('supports', [None, None])
    support_count = collision.get('support_count', 0)
    
    pair = {
        'id': id_from_bodies(parent_a, parent_b),
        'body_a': body_a,
        'body_b': body_b,
        'collision': collision,
        'contacts': [
            {'vertex': supports[0] if support_count > 0 else None, 'normal_impulse': 0, 'tangent_impulse': 0},
            {'vertex': supports[1] if support_count > 1 else None, 'normal_impulse': 0, 'tangent_impulse': 0}
        ],
        'contact_count': support_count,
        'separation': 0,
        'is_active': True,
        'is_sensor': body_a.get('is_sensor', False) or body_b.get('is_sensor', False),
        'confirmed': True,
        'time_created': timestamp,
        'time_updated': timestamp,
        'inverse_mass': parent_a.get('inverse_mass', 0) + parent_b.get('inverse_mass', 0),
        'friction': min(parent_a.get('friction', 0.1), parent_b.get('friction', 0.1)),
        'friction_static': max(parent_a.get('friction_static', 0.5), parent_b.get('friction_static', 0.5)),
        'restitution': max(parent_a.get('restitution', 0), parent_b.get('restitution', 0)),
        'slop': max(parent_a.get('slop', 0.05), parent_b.get('slop', 0.05))
    }
    
    collision['pair'] = pair
    
    return pair


def set_active(pairs: Dict, pair: Dict, is_active: bool, timestamp: float) -> None:
    """Sets a pair as active or inactive."""
    if is_active:
        pair['is_active'] = True
        pair['time_updated'] = timestamp
    else:
        pair['is_active'] = False
        
        for contact in pair['contacts']:
            contact['normal_impulse'] = 0
            contact['tangent_impulse'] = 0


def id_from_bodies(body_a: Dict, body_b: Dict) -> str:
    """Returns a unique pair id given two bodies."""
    if body_a['id'] < body_b['id']:
        return f"A{body_a['id']}B{body_b['id']}"
    else:
        return f"A{body_b['id']}B{body_a['id']}"


def clear(pairs: Dict) -> Dict:
    """Clears all pairs."""
    pairs['table'].clear()
    pairs['list'].clear()
    pairs['collision_start'].clear()
    pairs['collision_active'].clear()
    pairs['collision_end'].clear()
    return pairs
