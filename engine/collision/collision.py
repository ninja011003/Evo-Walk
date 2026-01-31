from typing import Dict, Any, List, Optional

from ..geometry import vertices as Vertices


# Module level reusable objects for efficiency
_supports = [None, None]

_overlap_ab = {
    'overlap': 0,
    'axis': None
}

_overlap_ba = {
    'overlap': 0,
    'axis': None
}


def create(body_a: Dict, body_b: Dict) -> Dict:
    """Creates a new collision record."""
    return {
        'pair': None,
        'collided': False,
        'body_a': body_a,
        'body_b': body_b,
        'parent_a': body_a['parent'],
        'parent_b': body_b['parent'],
        'depth': 0,
        'normal': {'x': 0, 'y': 0},
        'tangent': {'x': 0, 'y': 0},
        'penetration': {'x': 0, 'y': 0},
        'supports': [None, None],
        'support_count': 0
    }


def collides(body_a: Dict, body_b: Dict, pairs: Optional[Dict] = None) -> Optional[Dict]:
    """
    Detect collision between two bodies using SAT.
    Returns a collision record if detected, otherwise None.
    """
    _overlap_axes(_overlap_ab, body_a['vertices'], body_b['vertices'], body_a['axes'])
    
    if _overlap_ab['overlap'] <= 0:
        return None
    
    _overlap_axes(_overlap_ba, body_b['vertices'], body_a['vertices'], body_b['axes'])
    
    if _overlap_ba['overlap'] <= 0:
        return None
    
    # Reuse collision records for efficiency
    pair = None
    if pairs and pairs.get('table'):
        pair_id = _pair_id(body_a, body_b)
        pair = pairs['table'].get(pair_id)
    
    if not pair:
        collision = create(body_a, body_b)
        collision['collided'] = True
        collision['body_a'] = body_a if body_a['id'] < body_b['id'] else body_b
        collision['body_b'] = body_b if body_a['id'] < body_b['id'] else body_a
        collision['parent_a'] = collision['body_a']['parent']
        collision['parent_b'] = collision['body_b']['parent']
    else:
        collision = pair['collision']
    
    body_a = collision['body_a']
    body_b = collision['body_b']
    
    if _overlap_ab['overlap'] < _overlap_ba['overlap']:
        min_overlap = _overlap_ab
    else:
        min_overlap = _overlap_ba
    
    normal = collision['normal']
    tangent = collision['tangent']
    penetration = collision['penetration']
    supports = collision['supports']
    depth = min_overlap['overlap']
    min_axis = min_overlap['axis']
    normal_x = min_axis['x']
    normal_y = min_axis['y']
    delta_x = body_b['position']['x'] - body_a['position']['x']
    delta_y = body_b['position']['y'] - body_a['position']['y']
    
    # Ensure normal is facing away from body_a
    if normal_x * delta_x + normal_y * delta_y >= 0:
        normal_x = -normal_x
        normal_y = -normal_y
    
    normal['x'] = normal_x
    normal['y'] = normal_y
    
    tangent['x'] = -normal_y
    tangent['y'] = normal_x
    
    penetration['x'] = normal_x * depth
    penetration['y'] = normal_y * depth
    
    collision['depth'] = depth
    
    # Find support points (always either 1 or 2)
    supports_b = _find_supports(body_a, body_b, normal, 1)
    support_count = 0
    
    # Find the supports from body_b that are inside body_a
    if Vertices.contains(body_a['vertices'], supports_b[0]):
        supports[support_count] = supports_b[0]
        support_count += 1
    
    if Vertices.contains(body_a['vertices'], supports_b[1]):
        supports[support_count] = supports_b[1]
        support_count += 1
    
    # Find the supports from body_a that are inside body_b
    if support_count < 2:
        supports_a = _find_supports(body_b, body_a, normal, -1)
        
        if Vertices.contains(body_b['vertices'], supports_a[0]):
            supports[support_count] = supports_a[0]
            support_count += 1
        
        if support_count < 2 and Vertices.contains(body_b['vertices'], supports_a[1]):
            supports[support_count] = supports_a[1]
            support_count += 1
    
    # Account for edge case of overlapping but no vertex containment
    if support_count == 0:
        supports[support_count] = supports_b[0]
        support_count += 1
    
    # Update support count
    collision['support_count'] = support_count
    
    return collision


def _overlap_axes(result: Dict, vertices_a: List[Dict], vertices_b: List[Dict], axes: List[Dict]) -> None:
    """Find the overlap between two sets of vertices along given axes."""
    vertices_a_length = len(vertices_a)
    vertices_b_length = len(vertices_b)
    vertices_a_x = vertices_a[0]['x']
    vertices_a_y = vertices_a[0]['y']
    vertices_b_x = vertices_b[0]['x']
    vertices_b_y = vertices_b[0]['y']
    axes_length = len(axes)
    overlap_min = float('inf')
    overlap_axis_number = 0
    
    for i in range(axes_length):
        axis = axes[i]
        axis_x = axis['x']
        axis_y = axis['y']
        min_a = vertices_a_x * axis_x + vertices_a_y * axis_y
        min_b = vertices_b_x * axis_x + vertices_b_y * axis_y
        max_a = min_a
        max_b = min_b
        
        for j in range(1, vertices_a_length):
            dot = vertices_a[j]['x'] * axis_x + vertices_a[j]['y'] * axis_y
            if dot > max_a:
                max_a = dot
            elif dot < min_a:
                min_a = dot
        
        for j in range(1, vertices_b_length):
            dot = vertices_b[j]['x'] * axis_x + vertices_b[j]['y'] * axis_y
            if dot > max_b:
                max_b = dot
            elif dot < min_b:
                min_b = dot
        
        overlap_ab = max_a - min_b
        overlap_ba = max_b - min_a
        overlap = overlap_ab if overlap_ab < overlap_ba else overlap_ba
        
        if overlap < overlap_min:
            overlap_min = overlap
            overlap_axis_number = i
            
            if overlap <= 0:
                # Cannot be intersecting
                break
    
    result['axis'] = axes[overlap_axis_number]
    result['overlap'] = overlap_min


def _find_supports(body_a: Dict, body_b: Dict, normal: Dict, direction: int) -> List[Dict]:
    """
    Finds supporting vertices given two bodies along a given direction using hill-climbing.
    """
    vertices = body_b['vertices']
    vertices_length = len(vertices)
    body_a_position_x = body_a['position']['x']
    body_a_position_y = body_a['position']['y']
    normal_x = normal['x'] * direction
    normal_y = normal['y'] * direction
    vertex_a = vertices[0]
    vertex_b = vertex_a
    nearest_distance = normal_x * (body_a_position_x - vertex_b['x']) + normal_y * (body_a_position_y - vertex_b['y'])
    
    # Find deepest vertex relative to the axis
    for j in range(1, vertices_length):
        vertex_b = vertices[j]
        distance = normal_x * (body_a_position_x - vertex_b['x']) + normal_y * (body_a_position_y - vertex_b['y'])
        
        # Convex hill-climbing
        if distance < nearest_distance:
            nearest_distance = distance
            vertex_a = vertex_b
    
    # Measure next vertex
    vertex_c = vertices[(vertices_length + vertex_a['index'] - 1) % vertices_length]
    nearest_distance = normal_x * (body_a_position_x - vertex_c['x']) + normal_y * (body_a_position_y - vertex_c['y'])
    
    # Compare with previous vertex
    vertex_b = vertices[(vertex_a['index'] + 1) % vertices_length]
    if normal_x * (body_a_position_x - vertex_b['x']) + normal_y * (body_a_position_y - vertex_b['y']) < nearest_distance:
        _supports[0] = vertex_a
        _supports[1] = vertex_b
        return _supports
    
    _supports[0] = vertex_a
    _supports[1] = vertex_c
    return _supports


def _pair_id(body_a: Dict, body_b: Dict) -> str:
    """Generate a unique pair ID from two bodies."""
    if body_a['id'] < body_b['id']:
        return f"A{body_a['id']}B{body_b['id']}"
    else:
        return f"A{body_b['id']}B{body_a['id']}"
