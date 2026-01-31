import json
import os
import math
from typing import Optional, Dict, Any, List, Tuple

from engine import Engine, Body, Composite, Constraint, Bodies, Vector, Events

TEMPLATES_FILE = os.path.join(os.path.dirname(__file__), "templates.json")

BOB_RADIUS = 10
BOX_WIDTH = 15
BOX_HEIGHT = 80
GRAVITY_X = 0
GRAVITY_Y = 1
GRAVITY = Vector.create(GRAVITY_X, GRAVITY_Y)
FORCE_MAGNITUDE = 5000


class Bob:
    """Circle body wrapper for compatibility with existing code."""
    _id_counter = 0

    def __init__(self, x: float, y: float, pinned: bool = False, engine_world: Dict = None):
        Bob._id_counter += 1
        self.id = Bob._id_counter
        self.radius = BOB_RADIUS
        self.pinned = pinned
        
        mass = 0 if pinned else 1
        self.body = Bodies.circle(x, y, self.radius, {
            'is_static': pinned,
            'label': f'Bob_{self.id}',
            'friction': 0.1,
            'restitution': 0.3,
            'friction_air': 0.01
        })
        
        if not pinned:
            Body.set_mass(self.body, mass)
        
        self.name = f"Bob_{self.id}"
        self._engine_world = engine_world

    @property
    def position(self) -> Dict:
        """Get position as dict."""
        return self.body['position']

    @property
    def velocity(self) -> Dict:
        """Get velocity as dict."""
        return Body.get_velocity(self.body)

    def contains(self, x: float, y: float) -> bool:
        dx = x - self.body['position']['x']
        dy = y - self.body['position']['y']
        return (dx * dx + dy * dy) <= (self.radius + 8) ** 2

    def apply_force(self, force: Dict) -> None:
        Body.apply_force(self.body, self.body['position'], force)

    def apply_torque(self, torque: float) -> None:
        self.body['torque'] += torque

    def apply_point_force(self, force: Dict, point: Dict) -> None:
        Body.apply_force(self.body, point, force)

    def clear_forces(self) -> None:
        self.body['force']['x'] = 0
        self.body['force']['y'] = 0

    def clear_torque(self) -> None:
        self.body['torque'] = 0

    def get_debug_info(self) -> Dict:
        vel = Body.get_velocity(self.body)
        return {
            "type": "Bob",
            "id": self.id,
            "name": self.name,
            "position.x": round(self.body['position']['x'], 2),
            "position.y": round(self.body['position']['y'], 2),
            "velocity.x": round(vel['x'], 2),
            "velocity.y": round(vel['y'], 2),
            "mass": self.body['mass'],
            "pinned": self.pinned,
            "radius": self.radius,
            "force.x": round(self.body['force']['x'], 2),
            "force.y": round(self.body['force']['y'], 2),
            "orientation": round(self.body['angle'], 2),
            "ang_velocity": round(Body.get_angular_velocity(self.body), 2),
            "moi": round(self.body['inertia'], 2),
            "torque": round(self.body['torque'], 2),
            "add_torque": 0.0,
            "add_force.x": 0.0,
            "add_force.y": 0.0,
        }

    def set_property(self, key: str, value: Any) -> None:
        if key == "position.x":
            Body.set_position(self.body, {'x': float(value), 'y': self.body['position']['y']})
        elif key == "position.y":
            Body.set_position(self.body, {'x': self.body['position']['x'], 'y': float(value)})
        elif key == "velocity.x":
            Body.set_velocity(self.body, {'x': float(value), 'y': Body.get_velocity(self.body)['y']})
        elif key == "velocity.y":
            Body.set_velocity(self.body, {'x': Body.get_velocity(self.body)['x'], 'y': float(value)})
        elif key == "mass":
            Body.set_mass(self.body, float(value))
            self.pinned = float(value) == 0
        elif key == "pinned":
            self.pinned = bool(value)
            Body.set_static(self.body, self.pinned)
        elif key == "radius":
            self.radius = max(5, int(value))
        elif key == "orientation":
            Body.set_angle(self.body, float(value))
        elif key == "ang_velocity":
            Body.set_angular_velocity(self.body, float(value))
        elif key == "add_torque":
            self.body['torque'] += float(value)
        elif key == "add_force.x":
            self.body['force']['x'] += float(value)
        elif key == "add_force.y":
            self.body['force']['y'] += float(value)


class Box:
    """Rectangle body wrapper for compatibility with existing code."""
    _id_counter = 0

    ANCHOR_CENTER = "center"
    ANCHOR_LEFT = "left"
    ANCHOR_RIGHT = "right"
    ANCHOR_TOP = "top"
    ANCHOR_BOTTOM = "bottom"

    def __init__(self, x: float, y: float, width: float = BOX_WIDTH, height: float = BOX_HEIGHT, 
                 pinned: bool = False, engine_world: Dict = None):
        Box._id_counter += 1
        self.id = Box._id_counter
        self.width = width
        self.height = height
        self.pinned = pinned
        
        mass = 0 if pinned else 2
        self.body = Bodies.rectangle(x, y, width, height, {
            'is_static': pinned,
            'label': f'Box_{self.id}',
            'friction': 0.1,
            'restitution': 0.2,
            'friction_air': 0.01
        })
        
        if not pinned:
            Body.set_mass(self.body, mass)
        
        self.name = f"Box_{self.id}"
        self._engine_world = engine_world

    @property
    def position(self) -> Dict:
        return self.body['position']

    @property
    def velocity(self) -> Dict:
        return Body.get_velocity(self.body)

    @property
    def orientation(self) -> float:
        return self.body['angle']

    def get_local_anchors(self) -> Dict:
        hw = self.width / 2
        hh = self.height / 2
        return {
            self.ANCHOR_CENTER: {'x': 0, 'y': 0},
            self.ANCHOR_LEFT: {'x': -hw, 'y': 0},
            self.ANCHOR_RIGHT: {'x': hw, 'y': 0},
            self.ANCHOR_TOP: {'x': 0, 'y': -hh},
            self.ANCHOR_BOTTOM: {'x': 0, 'y': hh},
        }

    def get_world_anchor(self, anchor_name: str) -> Dict:
        local = self.get_local_anchors()[anchor_name]
        cos_a = math.cos(self.body['angle'])
        sin_a = math.sin(self.body['angle'])
        wx = self.body['position']['x'] + local['x'] * cos_a - local['y'] * sin_a
        wy = self.body['position']['y'] + local['x'] * sin_a + local['y'] * cos_a
        return {'x': wx, 'y': wy}

    def get_all_world_anchors(self) -> Dict:
        cos_a = math.cos(self.body['angle'])
        sin_a = math.sin(self.body['angle'])
        cx, cy = self.body['position']['x'], self.body['position']['y']
        result = {}
        for name, local in self.get_local_anchors().items():
            wx = cx + local['x'] * cos_a - local['y'] * sin_a
            wy = cy + local['x'] * sin_a + local['y'] * cos_a
            result[name] = (wx, wy)
        return result

    def get_nearest_anchor(self, x: float, y: float) -> str:
        anchors = self.get_all_world_anchors()
        min_dist = float("inf")
        nearest = self.ANCHOR_CENTER
        for name, (ax, ay) in anchors.items():
            dist = (x - ax) ** 2 + (y - ay) ** 2
            if dist < min_dist:
                min_dist = dist
                nearest = name
        return nearest

    def get_resize_handles(self) -> Dict:
        hw = self.width / 2
        hh = self.height / 2
        return {
            "top_left": {'x': -hw, 'y': -hh},
            "top_right": {'x': hw, 'y': -hh},
            "bottom_left": {'x': -hw, 'y': hh},
            "bottom_right": {'x': hw, 'y': hh},
            "top": {'x': 0, 'y': -hh},
            "bottom": {'x': 0, 'y': hh},
            "left": {'x': -hw, 'y': 0},
            "right": {'x': hw, 'y': 0},
        }

    def get_world_resize_handles(self) -> Dict:
        cos_a = math.cos(self.body['angle'])
        sin_a = math.sin(self.body['angle'])
        cx, cy = self.body['position']['x'], self.body['position']['y']
        result = {}
        for name, local in self.get_resize_handles().items():
            wx = cx + local['x'] * cos_a - local['y'] * sin_a
            wy = cy + local['x'] * sin_a + local['y'] * cos_a
            result[name] = (wx, wy)
        return result

    def get_resize_handle_at(self, x: float, y: float, threshold: int = 12) -> Optional[str]:
        handles = self.get_world_resize_handles()
        for name, (hx, hy) in handles.items():
            dist = ((x - hx) ** 2 + (y - hy) ** 2) ** 0.5
            if dist < threshold:
                return name
        return None

    def resize(self, handle: str, world_x: float, world_y: float) -> None:
        cos_a = math.cos(-self.body['angle'])
        sin_a = math.sin(-self.body['angle'])
        dx = world_x - self.body['position']['x']
        dy = world_y - self.body['position']['y']
        local_x = dx * cos_a - dy * sin_a
        local_y = dx * sin_a + dy * cos_a

        min_size = 10

        if handle in ("top_left", "top_right", "bottom_left", "bottom_right"):
            new_hw = abs(local_x)
            new_hh = abs(local_y)
            self.width = max(min_size, new_hw * 2)
            self.height = max(min_size, new_hh * 2)
        elif handle == "left" or handle == "right":
            self.width = max(min_size, abs(local_x) * 2)
        elif handle == "top" or handle == "bottom":
            self.height = max(min_size, abs(local_y) * 2)

        # Recreate vertices for new size
        from engine.geometry import vertices as Vertices
        new_verts = Vertices.from_path(f'L 0 0 L {self.width} 0 L {self.width} {self.height} L 0 {self.height}')
        Body.set_vertices(self.body, new_verts)

    def contains(self, x: float, y: float) -> bool:
        cos_a = math.cos(-self.body['angle'])
        sin_a = math.sin(-self.body['angle'])
        dx = x - self.body['position']['x']
        dy = y - self.body['position']['y']
        local_x = dx * cos_a - dy * sin_a
        local_y = dx * sin_a + dy * cos_a
        return abs(local_x) <= self.width / 2 + 5 and abs(local_y) <= self.height / 2 + 5

    def apply_force(self, force: Dict) -> None:
        Body.apply_force(self.body, self.body['position'], force)

    def apply_torque(self, torque: float) -> None:
        self.body['torque'] += torque

    def apply_point_force(self, force: Dict, point: Dict) -> None:
        Body.apply_force(self.body, point, force)

    def clear_forces(self) -> None:
        self.body['force']['x'] = 0
        self.body['force']['y'] = 0

    def clear_torque(self) -> None:
        self.body['torque'] = 0

    def get_debug_info(self) -> Dict:
        vel = Body.get_velocity(self.body)
        return {
            "type": "Box",
            "id": self.id,
            "name": self.name,
            "position.x": round(self.body['position']['x'], 2),
            "position.y": round(self.body['position']['y'], 2),
            "velocity.x": round(vel['x'], 2),
            "velocity.y": round(vel['y'], 2),
            "mass": self.body['mass'],
            "pinned": self.pinned,
            "width": self.width,
            "height": self.height,
            "force.x": round(self.body['force']['x'], 2),
            "force.y": round(self.body['force']['y'], 2),
            "orientation": round(self.body['angle'], 2),
            "ang_velocity": round(Body.get_angular_velocity(self.body), 2),
            "moi": round(self.body['inertia'], 2),
            "torque": round(self.body['torque'], 2),
            "add_torque": 0.0,
            "add_force.x": 0.0,
            "add_force.y": 0.0,
        }

    def set_property(self, key: str, value: Any) -> None:
        if key == "position.x":
            Body.set_position(self.body, {'x': float(value), 'y': self.body['position']['y']})
        elif key == "position.y":
            Body.set_position(self.body, {'x': self.body['position']['x'], 'y': float(value)})
        elif key == "velocity.x":
            Body.set_velocity(self.body, {'x': float(value), 'y': Body.get_velocity(self.body)['y']})
        elif key == "velocity.y":
            Body.set_velocity(self.body, {'x': Body.get_velocity(self.body)['x'], 'y': float(value)})
        elif key == "mass":
            Body.set_mass(self.body, float(value))
            self.pinned = float(value) == 0
        elif key == "pinned":
            self.pinned = bool(value)
            Body.set_static(self.body, self.pinned)
        elif key == "width":
            self.width = max(10, float(value))
            self.resize("right", self.body['position']['x'] + self.width / 2, self.body['position']['y'])
        elif key == "height":
            self.height = max(10, float(value))
            self.resize("bottom", self.body['position']['x'], self.body['position']['y'] + self.height / 2)
        elif key == "orientation":
            Body.set_angle(self.body, float(value))
        elif key == "ang_velocity":
            Body.set_angular_velocity(self.body, float(value))
        elif key == "add_torque":
            self.body['torque'] += float(value)
        elif key == "add_force.x":
            self.body['force']['x'] += float(value)
        elif key == "add_force.y":
            self.body['force']['y'] += float(value)


JOINT_RADIUS = 8


class JointWrapper:
    """Joint (pin constraint hub) wrapper."""
    _id_counter = 0

    def __init__(self, x: float, y: float, radius: int = JOINT_RADIUS, engine_world: Dict = None):
        JointWrapper._id_counter += 1
        self.id = JointWrapper._id_counter
        self.radius = radius
        
        self.body = Bodies.circle(x, y, radius, {
            'label': f'Joint_{self.id}',
            'friction': 0.1,
            'restitution': 0.0,
        })
        Body.set_mass(self.body, 0.5)
        
        self.name = f"Joint_{self.id}"
        self.connected_bodies = []
        self._constraints = []
        self._engine_world = engine_world

    @property
    def position(self) -> Dict:
        return self.body['position']

    def contains(self, x: float, y: float) -> bool:
        dx = x - self.body['position']['x']
        dy = y - self.body['position']['y']
        return (dx * dx + dy * dy) <= (self.radius + 8) ** 2

    def connect(self, wrapper, body_anchor: str = None) -> Dict:
        """Connect a body to this joint."""
        if isinstance(wrapper, Box):
            if body_anchor is None:
                body_anchor = "center"
            local_anchor = wrapper.get_local_anchors()[body_anchor]
        else:
            local_anchor = {'x': 0, 'y': 0}
        
        constraint = Constraint.create({
            'body_a': self.body,
            'body_b': wrapper.body,
            'point_a': {'x': 0, 'y': 0},
            'point_b': local_anchor,
            'length': 0,
            'stiffness': 0.9,
            'damping': 0.1
        })
        
        self._constraints.append(constraint)
        self.connected_bodies.append((wrapper, body_anchor, constraint))
        
        if self._engine_world:
            Composite.add_constraint(self._engine_world, constraint)
        
        return constraint

    def apply_force(self, force: Dict) -> None:
        Body.apply_force(self.body, self.body['position'], force)

    def get_debug_info(self) -> Dict:
        vel = Body.get_velocity(self.body)
        return {
            "type": "Joint",
            "id": self.id,
            "name": self.name,
            "position.x": round(self.body['position']['x'], 2),
            "position.y": round(self.body['position']['y'], 2),
            "velocity.x": round(vel['x'], 2),
            "velocity.y": round(vel['y'], 2),
            "mass": self.body['mass'],
            "radius": self.radius,
            "orientation": round(self.body['angle'], 2),
            "ang_velocity": round(Body.get_angular_velocity(self.body), 2),
            "connections": len(self.connected_bodies),
        }

    def set_property(self, key: str, value: Any) -> None:
        if key == "position.x":
            Body.set_position(self.body, {'x': float(value), 'y': self.body['position']['y']})
        elif key == "position.y":
            Body.set_position(self.body, {'x': self.body['position']['x'], 'y': float(value)})
        elif key == "velocity.x":
            Body.set_velocity(self.body, {'x': float(value), 'y': Body.get_velocity(self.body)['y']})
        elif key == "velocity.y":
            Body.set_velocity(self.body, {'x': Body.get_velocity(self.body)['x'], 'y': float(value)})
        elif key == "mass":
            Body.set_mass(self.body, float(value))
        elif key == "radius":
            self.radius = max(3, int(value))


class MotorWrapper:
    """Motor wrapper that applies torque between two bodies via PD control."""
    _id_counter = 0

    def __init__(self, joint_wrapper: JointWrapper, body1, body2, 
                 min_angle: float = -math.pi, max_angle: float = math.pi):
        MotorWrapper._id_counter += 1
        self.id = MotorWrapper._id_counter
        self.joint_wrapper = joint_wrapper
        self.body1 = body1
        self.body2 = body2
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.target_angle = 0.0
        self.name = f"Motor_{self.id}"
        
        # PD controller parameters
        self.kp_motor = 500.0
        self.kd_motor = 50.0
        self.max_torque = 10000.0

    def update(self, target_angle: float = None) -> None:
        """Apply PD control torque to maintain target angle."""
        if target_angle is not None:
            self.target_angle = target_angle
        
        # Clamp target to limits
        clamped_target = max(self.min_angle, min(self.max_angle, self.target_angle))
        
        rel_angle = self.body2.body['angle'] - self.body1.body['angle']
        rel_ang_vel = Body.get_angular_velocity(self.body2.body) - Body.get_angular_velocity(self.body1.body)
        
        # PD control
        error = clamped_target - rel_angle
        torque = self.kp_motor * error - self.kd_motor * rel_ang_vel
        
        # Clamp torque
        torque = max(-self.max_torque, min(self.max_torque, torque))
        
        if not self.body1.pinned:
            self.body1.body['torque'] -= torque
        if not self.body2.pinned:
            self.body2.body['torque'] += torque

    def set_target_angle(self, angle: float) -> None:
        self.target_angle = angle

    def get_debug_info(self) -> Dict:
        rel_angle = self.body2.body['angle'] - self.body1.body['angle']
        return {
            "type": "Motor",
            "id": self.id,
            "name": self.name,
            "joint": self.joint_wrapper.name,
            "body1": self.body1.name,
            "body2": self.body2.name,
            "target_angle": round(self.target_angle, 4),
            "rel_angle": round(rel_angle, 4),
            "min_angle": round(self.min_angle, 4),
            "max_angle": round(self.max_angle, 4),
            "kp_motor": round(self.kp_motor, 2),
            "kd_motor": round(self.kd_motor, 2),
            "max_torque": round(self.max_torque, 2),
        }

    def set_property(self, key: str, value: Any) -> None:
        if key == "target_angle":
            self.target_angle = float(value)
        elif key == "min_angle":
            self.min_angle = float(value)
        elif key == "max_angle":
            self.max_angle = float(value)
        elif key == "kp_motor":
            self.kp_motor = max(0, float(value))
        elif key == "kd_motor":
            self.kd_motor = max(0, float(value))
        elif key == "max_torque":
            self.max_torque = max(0, float(value))


class Rod:
    """Distance constraint between two bodies."""
    _id_counter = 0

    def __init__(self, obj1, obj2, anchor1: str = None, anchor2: str = None, engine_world: Dict = None):
        Rod._id_counter += 1
        self.id = Rod._id_counter
        self.bob1 = obj1
        self.bob2 = obj2
        self.anchor1 = anchor1
        self.anchor2 = anchor2
        self._engine_world = engine_world

        p1 = self._get_position(obj1, anchor1)
        p2 = self._get_position(obj2, anchor2)
        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        self.length = (dx * dx + dy * dy) ** 0.5

        point_a = self._get_local_anchor(obj1, anchor1)
        point_b = self._get_local_anchor(obj2, anchor2)

        self.constraint = Constraint.create({
            'body_a': obj1.body,
            'body_b': obj2.body,
            'point_a': point_a,
            'point_b': point_b,
            'length': self.length,
            'stiffness': 1.0,
            'damping': 0.0
        })

        self.name = f"Rod_{self.id}"

        if self._engine_world:
            Composite.add_constraint(self._engine_world, self.constraint)

    def _get_local_anchor(self, obj, anchor: str) -> Dict:
        if isinstance(obj, Box) and anchor:
            return obj.get_local_anchors()[anchor]
        return {'x': 0, 'y': 0}

    def _get_position(self, obj, anchor: str) -> Dict:
        if isinstance(obj, Box) and anchor:
            return obj.get_world_anchor(anchor)
        return obj.body['position']

    def get_endpoint1(self) -> Tuple[float, float]:
        pos = self._get_position(self.bob1, self.anchor1)
        return (pos['x'], pos['y'])

    def get_endpoint2(self) -> Tuple[float, float]:
        pos = self._get_position(self.bob2, self.anchor2)
        return (pos['x'], pos['y'])

    def cur_length(self) -> float:
        p1 = self._get_position(self.bob1, self.anchor1)
        p2 = self._get_position(self.bob2, self.anchor2)
        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        return (dx * dx + dy * dy) ** 0.5

    def contains(self, x: float, y: float) -> bool:
        x1, y1 = self.get_endpoint1()
        x2, y2 = self.get_endpoint2()

        line_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if line_len == 0:
            return False

        t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / (line_len ** 2)))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)

        dist = ((x - proj_x) ** 2 + (y - proj_y) ** 2) ** 0.5
        return dist <= 8

    def get_debug_info(self) -> Dict:
        current_len = self.cur_length()
        p1 = self.get_endpoint1()
        p2 = self.get_endpoint2()
        return {
            "type": "Rod",
            "id": self.id,
            "name": self.name,
            "bob1": self.bob1.name,
            "bob2": self.bob2.name,
            "anchor1": self.anchor1 or "center",
            "anchor2": self.anchor2 or "center",
            "rest_length": round(self.length, 2),
            "current_length": round(current_len, 2),
            "stretch": round(current_len - self.length, 2),
            "bob1.x": round(p1[0], 2),
            "bob1.y": round(p1[1], 2),
            "bob2.x": round(p2[0], 2),
            "bob2.y": round(p2[1], 2),
        }

    def set_property(self, key: str, value: Any) -> None:
        if key == "rest_length":
            self.length = max(1, float(value))
            self.constraint['length'] = self.length
        elif key == "bob1.x":
            Body.set_position(self.bob1.body, {'x': float(value), 'y': self.bob1.body['position']['y']})
        elif key == "bob1.y":
            Body.set_position(self.bob1.body, {'x': self.bob1.body['position']['x'], 'y': float(value)})
        elif key == "bob2.x":
            Body.set_position(self.bob2.body, {'x': float(value), 'y': self.bob2.body['position']['y']})
        elif key == "bob2.y":
            Body.set_position(self.bob2.body, {'x': self.bob2.body['position']['x'], 'y': float(value)})


class Actuator:
    """Spring-like actuator between two bodies."""
    _id_counter = 0

    def __init__(self, obj1, obj2, anchor1: str = None, anchor2: str = None, engine_world: Dict = None):
        Actuator._id_counter += 1
        self.id = Actuator._id_counter
        self.obj1 = obj1
        self.obj2 = obj2
        self.anchor1 = anchor1
        self.anchor2 = anchor2
        self._engine_world = engine_world
        self.name = f"Actuator_{self.id}"

        p1 = self._get_position(obj1, anchor1)
        p2 = self._get_position(obj2, anchor2)
        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        self.rest_length = (dx * dx + dy * dy) ** 0.5

        # Actuator parameters
        self.max_force = 1000.0
        self.max_stiffness = 100.0
        self.damping = 10.0
        self.activation = 0.0  # 0 to 1, controls stiffness

    def _get_local_anchor(self, obj, anchor: str) -> Dict:
        if isinstance(obj, Box) and anchor:
            return obj.get_local_anchors()[anchor]
        return {'x': 0, 'y': 0}

    def _get_position(self, obj, anchor: str) -> Dict:
        if isinstance(obj, Box) and anchor:
            return obj.get_world_anchor(anchor)
        return obj.body['position']

    def get_endpoint1(self) -> Tuple[float, float]:
        pos = self._get_position(self.obj1, self.anchor1)
        return (pos['x'], pos['y'])

    def get_endpoint2(self) -> Tuple[float, float]:
        pos = self._get_position(self.obj2, self.anchor2)
        return (pos['x'], pos['y'])

    def cur_length(self) -> float:
        p1 = self._get_position(self.obj1, self.anchor1)
        p2 = self._get_position(self.obj2, self.anchor2)
        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        return (dx * dx + dy * dy) ** 0.5

    def apply_forces(self, dt: float) -> None:
        """Apply spring-like forces based on activation level."""
        p1 = self._get_position(self.obj1, self.anchor1)
        p2 = self._get_position(self.obj2, self.anchor2)

        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        dist = (dx * dx + dy * dy) ** 0.5

        if dist < 0.001:
            return

        # Normalize direction
        nx = dx / dist
        ny = dy / dist

        # Spring force
        stiffness = self.max_stiffness * self.activation
        stretch = dist - self.rest_length
        spring_force = stiffness * stretch

        # Damping (approximate velocity along axis)
        v1 = Body.get_velocity(self.obj1.body)
        v2 = Body.get_velocity(self.obj2.body)
        rel_vel = (v2['x'] - v1['x']) * nx + (v2['y'] - v1['y']) * ny
        damping_force = self.damping * rel_vel

        # Total force
        total_force = spring_force + damping_force
        total_force = max(-self.max_force, min(self.max_force, total_force))

        force = {'x': total_force * nx, 'y': total_force * ny}
        neg_force = {'x': -total_force * nx, 'y': -total_force * ny}

        Body.apply_force(self.obj1.body, p1, force)
        Body.apply_force(self.obj2.body, p2, neg_force)

    def contains(self, x: float, y: float) -> bool:
        x1, y1 = self.get_endpoint1()
        x2, y2 = self.get_endpoint2()

        line_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if line_len == 0:
            return False

        t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / (line_len ** 2)))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)

        dist = ((x - proj_x) ** 2 + (y - proj_y) ** 2) ** 0.5
        return dist <= 10

    def get_debug_info(self) -> Dict:
        current_len = self.cur_length()
        p1 = self.get_endpoint1()
        p2 = self.get_endpoint2()
        return {
            "type": "Actuator",
            "id": self.id,
            "name": self.name,
            "obj1": self.obj1.name,
            "obj2": self.obj2.name,
            "anchor1": self.anchor1 or "center",
            "anchor2": self.anchor2 or "center",
            "rest_length": round(self.rest_length, 2),
            "current_length": round(current_len, 2),
            "activation": round(self.activation, 3),
            "max_force": round(self.max_force, 2),
            "max_stiffness": round(self.max_stiffness, 2),
            "damping": round(self.damping, 2),
        }

    def set_property(self, key: str, value: Any) -> None:
        if key == "rest_length":
            self.rest_length = max(1, float(value))
        elif key == "activation":
            self.activation = max(0, min(1, float(value)))
        elif key == "max_force":
            self.max_force = max(0, float(value))
        elif key == "max_stiffness":
            self.max_stiffness = max(0, float(value))
        elif key == "damping":
            self.damping = max(0, float(value))


class SimulationEngine:
    """Main simulation engine using Matter.js-style physics."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        
        self.engine = Engine.create({
            'gravity': {'x': GRAVITY_X, 'y': GRAVITY_Y, 'scale': 0.001},
            'enable_sleeping': False,
            'position_iterations': 6,
            'velocity_iterations': 4,
            'constraint_iterations': 4
        })
        
        self.world = self.engine['world']
        
        self.bobs = []
        self.boxes = []
        self.rods = []
        self.actuators = []
        self.joints = []
        self.motors = []
        self.running = False
        self.iterations = 8
        self.dragging_bob = None
        self.dragging_box = None
        self.dragging_joint = None
        
        self.ground = self.create_box(
            width / 2, height - 20, width * 2, 40, pinned=True
        )

    def create_bob(self, x: float, y: float, pinned: bool = False) -> Bob:
        bob = Bob(x, y, pinned, engine_world=self.world)
        self.bobs.append(bob)
        Composite.add_body(self.world, bob.body)
        return bob

    def create_box(self, x: float, y: float, width: float = BOX_WIDTH, 
                   height: float = BOX_HEIGHT, pinned: bool = False) -> Box:
        box = Box(x, y, width, height, pinned, engine_world=self.world)
        self.boxes.append(box)
        Composite.add_body(self.world, box.body)
        return box

    def delete_box(self, box: Box) -> None:
        self.rods = [r for r in self.rods if r.bob1 != box and r.bob2 != box]
        self.actuators = [a for a in self.actuators if a.obj1 != box and a.obj2 != box]
        if box in self.boxes:
            self.boxes.remove(box)
            Composite.remove(self.world, box.body)

    def get_box_at(self, x: float, y: float) -> Optional[Box]:
        for box in reversed(self.boxes):
            if box.contains(x, y):
                return box
        return None

    def body_at(self, x: float, y: float):
        bob = self.get_bob_at(x, y)
        if bob:
            return bob
        box = self.get_box_at(x, y)
        if box:
            return box
        return None

    def force_at(self, x: float, y: float, fx: float, fy: float):
        body = self.body_at(x, y)
        if body:
            Body.apply_force(body.body, {'x': x, 'y': y}, {'x': fx, 'y': fy})
            return body
        return None

    def create_rod(self, bob1, bob2, anchor1: str = None, anchor2: str = None) -> Rod:
        rod = Rod(bob1, bob2, anchor1, anchor2, engine_world=self.world)
        self.rods.append(rod)
        return rod

    def create_actuator(self, obj1, obj2, anchor1: str = None, anchor2: str = None) -> Actuator:
        actuator = Actuator(obj1, obj2, anchor1, anchor2, engine_world=self.world)
        self.actuators.append(actuator)
        return actuator

    def create_joint(self, x: float, y: float) -> JointWrapper:
        joint = JointWrapper(x, y, engine_world=self.world)
        self.joints.append(joint)
        Composite.add_body(self.world, joint.body)
        return joint

    def get_joint_at(self, x: float, y: float) -> Optional[JointWrapper]:
        for joint in reversed(self.joints):
            if joint.contains(x, y):
                return joint
        return None

    def delete_joint(self, joint: JointWrapper) -> None:
        if joint in self.joints:
            self.joints.remove(joint)
            Composite.remove(self.world, joint.body)
            for constraint in joint._constraints:
                Composite.remove(self.world, constraint)

    def connect_to_joint(self, joint: JointWrapper, body, anchor: str = None) -> None:
        constraint = joint.connect(body, anchor)
        Composite.add_constraint(self.world, constraint)

    def create_motor(self, joint_wrapper: JointWrapper, body1, body2, 
                     min_angle: float = -math.pi, max_angle: float = math.pi) -> MotorWrapper:
        motor = MotorWrapper(joint_wrapper, body1, body2, min_angle, max_angle)
        self.motors.append(motor)
        return motor

    def get_motor_at(self, x: float, y: float) -> Optional[MotorWrapper]:
        for motor in reversed(self.motors):
            jx = motor.joint_wrapper.body['position']['x']
            jy = motor.joint_wrapper.body['position']['y']
            dx = x - jx
            dy = y - jy
            if (dx * dx + dy * dy) <= (motor.joint_wrapper.radius + 12) ** 2:
                return motor
        return None

    def delete_motor(self, motor: MotorWrapper) -> None:
        if motor in self.motors:
            self.motors.remove(motor)

    def get_actuator_at(self, x: float, y: float) -> Optional[Actuator]:
        for actuator in reversed(self.actuators):
            if actuator.contains(x, y):
                return actuator
        return None

    def delete_actuator(self, actuator: Actuator) -> None:
        if actuator in self.actuators:
            self.actuators.remove(actuator)

    def delete_bob(self, bob: Bob) -> None:
        self.rods = [r for r in self.rods if r.bob1 != bob and r.bob2 != bob]
        self.actuators = [a for a in self.actuators if a.obj1 != bob and a.obj2 != bob]
        if bob in self.bobs:
            self.bobs.remove(bob)
            Composite.remove(self.world, bob.body)

    def get_bob_at(self, x: float, y: float) -> Optional[Bob]:
        for bob in reversed(self.bobs):
            if bob.contains(x, y):
                return bob
        return None

    def get_rod_at(self, x: float, y: float) -> Optional[Rod]:
        for rod in reversed(self.rods):
            if rod.contains(x, y):
                return rod
        return None

    def toggle_pin(self, obj) -> None:
        obj.pinned = not obj.pinned
        Body.set_static(obj.body, obj.pinned)

    def set_dragging(self, obj) -> None:
        if isinstance(obj, Bob):
            self.dragging_bob = obj
        elif isinstance(obj, Box):
            self.dragging_box = obj
        elif isinstance(obj, JointWrapper):
            self.dragging_joint = obj

    def release(self) -> None:
        self.dragging_bob = None
        self.dragging_box = None
        self.dragging_joint = None

    def move(self, obj, x: float, y: float) -> None:
        Body.set_position(obj.body, {'x': x, 'y': y}, update_velocity=False)
        if self.running:
            Body.set_velocity(obj.body, {'x': 0, 'y': 0})
            Body.set_angular_velocity(obj.body, 0)

    def clear_forces(self) -> None:
        for bob in self.bobs:
            bob.clear_forces()
            bob.clear_torque()
        for box in self.boxes:
            box.clear_forces()
            box.clear_torque()

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def toggle(self) -> None:
        self.running = not self.running

    def clear(self) -> None:
        self.bobs = []
        self.boxes = []
        self.rods = []
        self.actuators = []
        self.joints = []
        self.motors = []
        self.running = False
        self.dragging_bob = None
        self.dragging_box = None
        self.dragging_joint = None
        
        # Reset counters
        Bob._id_counter = 0
        Box._id_counter = 0
        Rod._id_counter = 0
        Actuator._id_counter = 0
        JointWrapper._id_counter = 0
        MotorWrapper._id_counter = 0
        
        # Recreate engine
        self.engine = Engine.create({
            'gravity': {'x': GRAVITY_X, 'y': GRAVITY_Y, 'scale': 0.001},
            'enable_sleeping': False,
            'position_iterations': 6,
            'velocity_iterations': 4,
            'constraint_iterations': 4
        })
        self.world = self.engine['world']
        
        # Recreate ground
        self.ground = self.create_box(
            self.width / 2, self.height - 20, self.width * 2, 40, pinned=True
        )

    def update(self, dt: float) -> None:
        if not self.running:
            return

        for actuator in self.actuators:
            actuator.apply_forces(dt)

        for motor in self.motors:
            motor.update()

        Engine.update(self.engine, dt * 1000)

    def get_debug_info(self, fps: float, dt: float) -> Dict:
        return {
            "type": "Simulation",
            "name": "World",
            "is_running": self.running,
            "bob_count": len(self.bobs),
            "box_count": len(self.boxes),
            "rod_count": len(self.rods),
            "joint_count": len(self.joints),
            "motor_count": len(self.motors),
            "iterations": self.iterations,
            "gravity.x": self.engine['gravity']['x'],
            "gravity.y": self.engine['gravity']['y'],
            "fps": int(fps),
            "dt": round(dt * 1000, 2),
        }

    def set_property(self, key: str, value: Any) -> None:
        if key == "iterations":
            self.iterations = max(1, int(value))
            self.engine['position_iterations'] = self.iterations
            self.engine['velocity_iterations'] = self.iterations // 2
        elif key == "gravity.x":
            self.engine['gravity']['x'] = float(value)
        elif key == "gravity.y":
            self.engine['gravity']['y'] = float(value)

    def serialize(self) -> Dict:
        bob_map = {}
        bobs_data = []
        for i, bob in enumerate(self.bobs):
            bob_map[bob] = i
            bobs_data.append({
                "x": bob.body['position']['x'],
                "y": bob.body['position']['y'],
                "pinned": bob.pinned,
                "radius": bob.radius,
                "mass": bob.body['mass'],
            })

        box_map = {}
        boxes_data = []
        box_idx = 0
        for box in self.boxes:
            if box == self.ground:
                continue
            box_map[box] = box_idx
            boxes_data.append({
                "x": box.body['position']['x'],
                "y": box.body['position']['y'],
                "width": box.width,
                "height": box.height,
                "pinned": box.pinned,
                "orientation": box.body['angle'],
            })
            box_idx += 1

        rods_data = []
        for rod in self.rods:
            bob1_type = "bob" if rod.bob1 in bob_map else "box"
            bob2_type = "bob" if rod.bob2 in bob_map else "box"
            bob1_idx = bob_map.get(rod.bob1, box_map.get(rod.bob1, -1))
            bob2_idx = bob_map.get(rod.bob2, box_map.get(rod.bob2, -1))
            if bob1_idx >= 0 and bob2_idx >= 0:
                rods_data.append({
                    "bob1_type": bob1_type,
                    "bob1_idx": bob1_idx,
                    "bob2_type": bob2_type,
                    "bob2_idx": bob2_idx,
                    "anchor1": rod.anchor1,
                    "anchor2": rod.anchor2,
                    "length": rod.length,
                })

        actuators_data = []
        for actuator in self.actuators:
            obj1_type = "bob" if actuator.obj1 in bob_map else "box"
            obj2_type = "bob" if actuator.obj2 in bob_map else "box"
            obj1_idx = bob_map.get(actuator.obj1, box_map.get(actuator.obj1, -1))
            obj2_idx = bob_map.get(actuator.obj2, box_map.get(actuator.obj2, -1))
            if obj1_idx >= 0 and obj2_idx >= 0:
                actuators_data.append({
                    "obj1_type": obj1_type,
                    "obj1_idx": obj1_idx,
                    "obj2_type": obj2_type,
                    "obj2_idx": obj2_idx,
                    "anchor1": actuator.anchor1,
                    "anchor2": actuator.anchor2,
                    "rest_length": actuator.rest_length,
                    "max_force": actuator.max_force,
                    "max_stiffness": actuator.max_stiffness,
                    "damping": actuator.damping,
                })

        joint_map = {}
        joints_data = []
        for i, joint in enumerate(self.joints):
            joint_map[joint] = i
            connections = []
            for body, anchor, constraint in joint.connected_bodies:
                if body in bob_map:
                    connections.append({
                        "body_type": "bob",
                        "body_idx": bob_map[body],
                        "anchor": anchor,
                    })
                elif body in box_map:
                    connections.append({
                        "body_type": "box",
                        "body_idx": box_map[body],
                        "anchor": anchor,
                    })
            joints_data.append({
                "x": joint.body['position']['x'],
                "y": joint.body['position']['y'],
                "radius": joint.radius,
                "mass": joint.body['mass'],
                "orientation": joint.body['angle'],
                "connections": connections,
            })

        motors_data = []
        for motor in self.motors:
            joint_idx = joint_map.get(motor.joint_wrapper, -1)
            body1_type = "bob" if motor.body1 in bob_map else "box"
            body2_type = "bob" if motor.body2 in bob_map else "box"
            body1_idx = bob_map.get(motor.body1, box_map.get(motor.body1, -1))
            body2_idx = bob_map.get(motor.body2, box_map.get(motor.body2, -1))
            if joint_idx >= 0 and body1_idx >= 0 and body2_idx >= 0:
                motors_data.append({
                    "joint_idx": joint_idx,
                    "body1_type": body1_type,
                    "body1_idx": body1_idx,
                    "body2_type": body2_type,
                    "body2_idx": body2_idx,
                    "min_angle": motor.min_angle,
                    "max_angle": motor.max_angle,
                    "target_angle": motor.target_angle,
                    "kp_motor": motor.kp_motor,
                    "kd_motor": motor.kd_motor,
                    "max_torque": motor.max_torque,
                })

        return {
            "bobs": bobs_data,
            "boxes": boxes_data,
            "rods": rods_data,
            "actuators": actuators_data,
            "joints": joints_data,
            "motors": motors_data,
        }

    def load_template(self, data: Dict, offset_x: float = 0, offset_y: float = 0) -> None:
        bob_map = {}
        box_map = {}

        for i, bob_data in enumerate(data.get("bobs", [])):
            bob = self.create_bob(
                bob_data["x"] + offset_x,
                bob_data["y"] + offset_y,
                pinned=bob_data.get("pinned", False),
            )
            if "radius" in bob_data:
                bob.radius = bob_data["radius"]
            if "mass" in bob_data and bob_data["mass"] > 0:
                Body.set_mass(bob.body, bob_data["mass"])
            bob_map[i] = bob

        for i, box_data in enumerate(data.get("boxes", [])):
            box = self.create_box(
                box_data["x"] + offset_x,
                box_data["y"] + offset_y,
                width=box_data.get("width", BOX_WIDTH),
                height=box_data.get("height", BOX_HEIGHT),
                pinned=box_data.get("pinned", False),
            )
            if "orientation" in box_data:
                Body.set_angle(box.body, box_data["orientation"])
            box_map[i] = box

        for rod_data in data.get("rods", []):
            bob1_type = rod_data.get("bob1_type", "bob")
            bob2_type = rod_data.get("bob2_type", "bob")
            bob1_idx = rod_data["bob1_idx"]
            bob2_idx = rod_data["bob2_idx"]

            bob1 = bob_map.get(bob1_idx) if bob1_type == "bob" else box_map.get(bob1_idx)
            bob2 = bob_map.get(bob2_idx) if bob2_type == "bob" else box_map.get(bob2_idx)

            if bob1 and bob2:
                anchor1 = rod_data.get("anchor1")
                anchor2 = rod_data.get("anchor2")
                rod = self.create_rod(bob1, bob2, anchor1, anchor2)
                if rod and "length" in rod_data:
                    rod.length = rod_data["length"]
                    rod.constraint['length'] = rod_data["length"]

        for actuator_data in data.get("actuators", []):
            obj1_type = actuator_data.get("obj1_type", "bob")
            obj2_type = actuator_data.get("obj2_type", "bob")
            obj1_idx = actuator_data["obj1_idx"]
            obj2_idx = actuator_data["obj2_idx"]

            obj1 = bob_map.get(obj1_idx) if obj1_type == "bob" else box_map.get(obj1_idx)
            obj2 = bob_map.get(obj2_idx) if obj2_type == "bob" else box_map.get(obj2_idx)

            if obj1 and obj2:
                anchor1 = actuator_data.get("anchor1")
                anchor2 = actuator_data.get("anchor2")
                actuator = self.create_actuator(obj1, obj2, anchor1, anchor2)
                if actuator:
                    if "rest_length" in actuator_data:
                        actuator.rest_length = actuator_data["rest_length"]
                    if "max_force" in actuator_data:
                        actuator.max_force = actuator_data["max_force"]
                    if "max_stiffness" in actuator_data:
                        actuator.max_stiffness = actuator_data["max_stiffness"]
                    if "damping" in actuator_data:
                        actuator.damping = actuator_data["damping"]

        joint_map = {}
        for i, joint_data in enumerate(data.get("joints", [])):
            joint = self.create_joint(
                joint_data["x"] + offset_x,
                joint_data["y"] + offset_y,
            )
            joint_map[i] = joint
            if "radius" in joint_data:
                joint.radius = joint_data["radius"]
            if "mass" in joint_data:
                Body.set_mass(joint.body, joint_data["mass"])
            if "orientation" in joint_data:
                Body.set_angle(joint.body, joint_data["orientation"])
            for conn in joint_data.get("connections", []):
                body_type = conn.get("body_type", "bob")
                body_idx = conn.get("body_idx", -1)
                anchor = conn.get("anchor")
                body = bob_map.get(body_idx) if body_type == "bob" else box_map.get(body_idx)
                if body:
                    self.connect_to_joint(joint, body, anchor)

        for motor_data in data.get("motors", []):
            joint_idx = motor_data.get("joint_idx", -1)
            body1_type = motor_data.get("body1_type", "bob")
            body2_type = motor_data.get("body2_type", "bob")
            body1_idx = motor_data.get("body1_idx", -1)
            body2_idx = motor_data.get("body2_idx", -1)

            joint = joint_map.get(joint_idx)
            body1 = bob_map.get(body1_idx) if body1_type == "bob" else box_map.get(body1_idx)
            body2 = bob_map.get(body2_idx) if body2_type == "bob" else box_map.get(body2_idx)

            if joint and body1 and body2:
                min_angle = motor_data.get("min_angle", -math.pi)
                max_angle = motor_data.get("max_angle", math.pi)
                motor = self.create_motor(joint, body1, body2, min_angle, max_angle)
                if motor:
                    if "target_angle" in motor_data:
                        motor.target_angle = motor_data["target_angle"]
                    if "kp_motor" in motor_data:
                        motor.kp_motor = motor_data["kp_motor"]
                    if "kd_motor" in motor_data:
                        motor.kd_motor = motor_data["kd_motor"]
                    if "max_torque" in motor_data:
                        motor.max_torque = motor_data["max_torque"]


def load_templates() -> Dict:
    if os.path.exists(TEMPLATES_FILE):
        try:
            with open(TEMPLATES_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_template(name: str, data: Dict) -> None:
    templates = load_templates()
    templates[name] = data
    with open(TEMPLATES_FILE, "w") as f:
        json.dump(templates, f, indent=2)


def delete_template(name: str) -> None:
    templates = load_templates()
    if name in templates:
        del templates[name]
        with open(TEMPLATES_FILE, "w") as f:
            json.dump(templates, f, indent=2)
