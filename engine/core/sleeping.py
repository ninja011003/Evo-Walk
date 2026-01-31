from typing import Dict, Any, List, Optional

from . import common as Common


# Module constants
_motion_wake_threshold = 0.18
_motion_sleep_threshold = 0.08
_min_bias = 0.9


def update(bodies: List[Dict], delta: float) -> None:
    """Updates sleeping state for all bodies."""
    time_factor = delta / Common._base_delta
    
    for body in bodies:
        motion = body.get('speed', 0) ** 2 + body.get('angular_speed', 0) ** 2
        
        # Wake up body if motion exceeds threshold
        min_motion = min(body.get('motion', 0), motion)
        max_motion = max(body.get('motion', 0), motion)
        
        # Biased average motion
        body['motion'] = _min_bias * min_motion + (1 - _min_bias) * max_motion
        
        if body.get('sleep_threshold', 60) > 0 and body['motion'] < _motion_sleep_threshold * time_factor:
            body['sleep_counter'] = body.get('sleep_counter', 0) + 1
            
            if body['sleep_counter'] >= body['sleep_threshold'] / time_factor:
                set_sleeping(body, True)
        elif body.get('sleep_counter', 0) > 0:
            body['sleep_counter'] -= 1


def after_collisions(pairs: List[Dict]) -> None:
    """Wake bodies involved in collisions."""
    for pair in pairs:
        if not pair.get('is_active', False):
            continue
        
        collision = pair['collision']
        body_a = collision['parent_a']
        body_b = collision['parent_b']
        
        # Don't wake if both bodies are static
        if (body_a.get('is_static', False) or body_a.get('is_sleeping', False)) and \
           (body_b.get('is_static', False) or body_b.get('is_sleeping', False)):
            continue
        
        if body_a.get('is_sleeping', False) or body_b.get('is_sleeping', False):
            sleeping_body = body_a if body_a.get('is_sleeping', False) and not body_a.get('is_static', False) else body_b
            awake_body = body_b if sleeping_body == body_a else body_a
            
            if not (awake_body.get('is_static', False) or awake_body.get('is_sleeping', False)):
                motion_a = sleeping_body.get('motion', 0)
                motion_b = awake_body.get('motion', 0)
                
                if motion_b > motion_a * _motion_wake_threshold:
                    set_sleeping(sleeping_body, False)


def set_sleeping(body: Dict, is_sleeping: bool) -> None:
    """Sets a body as sleeping or awake."""
    if is_sleeping:
        body['is_sleeping'] = True
        body['sleep_counter'] = body.get('sleep_threshold', 60)
        
        body['position_impulse']['x'] = 0
        body['position_impulse']['y'] = 0
        
        body['position_prev']['x'] = body['position']['x']
        body['position_prev']['y'] = body['position']['y']
        
        body['angle_prev'] = body['angle']
        body['speed'] = 0
        body['angular_speed'] = 0
        body['motion'] = 0
    else:
        body['is_sleeping'] = False
        body['sleep_counter'] = 0
