from engine.templates.vector import Vector
from engine.templates.body import Body
from engine.templates.contraint import Contraint
from engine.templates.collision_handler import Collision_Handler

BOB_RADIUS = 12
BOX_WIDTH = 60
BOX_HEIGHT = 40
GRAVITY = Vector(0, 980)
FORCE_MAGNITUDE = 5000


class Bob:
    _id_counter = 0

    def __init__(self, x, y, pinned=False):
        Bob._id_counter += 1
        self.id = Bob._id_counter
        self.radius = BOB_RADIUS
        mass = 0 if pinned else 1
        self.body = Body(
            mass=mass, position=Vector(x, y), shape="circle", radius=self.radius
        )
        self.pinned = pinned
        if self.pinned:
            self.body.inv_moi = 0
        self.name = f"Bob_{self.id}"

    def contains(self, x, y):
        dx = x - self.body.position.x
        dy = y - self.body.position.y
        return (dx * dx + dy * dy) <= (self.radius + 8) ** 2

    def apply_force(self, force):
        self.body.apply_force(force)

    def apply_torque(self, torque):
        self.body.apply_torque(torque)

    def apply_point_force(self, force, point):
        self.body.apply_point_force(force, point)

    def clear_forces(self):
        self.body.clear_forces()

    def clear_torque(self):
        self.body.clear_torque()

    def get_debug_info(self):
        return {
            "type": "Bob",
            "id": self.id,
            "name": self.name,
            "position.x": round(self.body.position.x, 2),
            "position.y": round(self.body.position.y, 2),
            "velocity.x": round(self.body.velocity.x, 2),
            "velocity.y": round(self.body.velocity.y, 2),
            "mass": self.body.mass,
            "pinned": self.pinned,
            "radius": self.radius,
            "force.x": round(self.body.total_force.x, 2),
            "force.y": round(self.body.total_force.y, 2),
            "orientation": round(self.body.orientation, 2),
            "ang_velocity": round(self.body.ang_velocity, 2),
            "moi": round(self.body.moi, 2),
            "torque": round(self.body.total_torque, 2),
            "add_torque": 0.0,
            "add_force.x": 0.0,
            "add_force.y": 0.0,
        }

    def set_property(self, key, value):
        if key == "position.x":
            self.body.position.x = float(value)
        elif key == "position.y":
            self.body.position.y = float(value)
        elif key == "velocity.x":
            self.body.velocity.x = float(value)
        elif key == "velocity.y":
            self.body.velocity.y = float(value)
        elif key == "mass":
            self.body.mass = float(value)
            self.body.inv_mass = 1 / self.body.mass if self.body.mass > 0 else 0
            self.pinned = self.body.mass == 0
            self.radius = BOB_RADIUS * (self.body.mass / 5)
            self.body.radius = self.radius
        elif key == "pinned":
            self.pinned = bool(value)
            self.body.mass = 0 if self.pinned else 1
            self.body.inv_mass = 1 / self.body.mass if self.body.mass > 0 else 0
            self.body.inv_moi = (
                0
                if self.pinned
                else (1 / self.body.moi if self.body.moi > 0 else 0)
            )
        elif key == "radius":
            self.radius = max(5, int(value))
            self.body.radius = self.radius
        elif key == "orientation":
            self.body.orientation = float(value)
        elif key == "ang_velocity":
            self.body.ang_velocity = float(value)
        elif key == "add_torque":
            self.body.apply_torque(float(value))
        elif key == "add_force.x":
            self.body.apply_force(Vector(float(value), 0))
        elif key == "add_force.y":
            self.body.apply_force(Vector(0, float(value)))


class Box:
    _id_counter = 0

    def __init__(self, x, y, width=BOX_WIDTH, height=BOX_HEIGHT, pinned=False):
        Box._id_counter += 1
        self.id = Box._id_counter
        self.width = width
        self.height = height
        mass = 0 if pinned else 2
        self.body = Body(
            mass=mass,
            position=Vector(x, y),
            shape="rectangle",
            width=self.width,
            height=self.height,
        )
        self.pinned = pinned
        if self.pinned:
            self.body.inv_moi = 0
        self.name = f"Box_{self.id}"

    def contains(self, x, y):
        import math

        cos_a = math.cos(-self.body.orientation)
        sin_a = math.sin(-self.body.orientation)
        dx = x - self.body.position.x
        dy = y - self.body.position.y
        local_x = dx * cos_a - dy * sin_a
        local_y = dx * sin_a + dy * cos_a
        return (
            abs(local_x) <= self.width / 2 + 5
            and abs(local_y) <= self.height / 2 + 5
        )

    def apply_force(self, force):
        self.body.apply_force(force)

    def apply_torque(self, torque):
        self.body.apply_torque(torque)

    def apply_point_force(self, force, point):
        self.body.apply_point_force(force, point)

    def clear_forces(self):
        self.body.clear_forces()

    def clear_torque(self):
        self.body.clear_torque()

    def get_debug_info(self):
        return {
            "type": "Box",
            "id": self.id,
            "name": self.name,
            "position.x": round(self.body.position.x, 2),
            "position.y": round(self.body.position.y, 2),
            "velocity.x": round(self.body.velocity.x, 2),
            "velocity.y": round(self.body.velocity.y, 2),
            "mass": self.body.mass,
            "pinned": self.pinned,
            "width": self.width,
            "height": self.height,
            "force.x": round(self.body.total_force.x, 2),
            "force.y": round(self.body.total_force.y, 2),
            "orientation": round(self.body.orientation, 2),
            "ang_velocity": round(self.body.ang_velocity, 2),
            "moi": round(self.body.moi, 2),
            "torque": round(self.body.total_torque, 2),
            "add_torque": 0.0,
            "add_force.x": 0.0,
            "add_force.y": 0.0,
        }

    def set_property(self, key, value):
        if key == "position.x":
            self.body.position.x = float(value)
        elif key == "position.y":
            self.body.position.y = float(value)
        elif key == "velocity.x":
            self.body.velocity.x = float(value)
        elif key == "velocity.y":
            self.body.velocity.y = float(value)
        elif key == "mass":
            self.body.mass = float(value)
            self.body.inv_mass = 1 / self.body.mass if self.body.mass > 0 else 0
            self.pinned = self.body.mass == 0
        elif key == "pinned":
            self.pinned = bool(value)
            self.body.mass = 0 if self.pinned else 2
            self.body.inv_mass = 1 / self.body.mass if self.body.mass > 0 else 0
            self.body.inv_moi = (
                0
                if self.pinned
                else (1 / self.body.moi if self.body.moi > 0 else 0)
            )
        elif key == "width":
            self.width = max(10, float(value))
            self.body.width = self.width
        elif key == "height":
            self.height = max(10, float(value))
            self.body.height = self.height
        elif key == "orientation":
            self.body.orientation = float(value)
        elif key == "ang_velocity":
            self.body.ang_velocity = float(value)
        elif key == "add_torque":
            self.body.apply_torque(float(value))
        elif key == "add_force.x":
            self.body.apply_force(Vector(float(value), 0))
        elif key == "add_force.y":
            self.body.apply_force(Vector(0, float(value)))


class Rod:
    _id_counter = 0

    def __init__(self, bob1, bob2):
        Rod._id_counter += 1
        self.id = Rod._id_counter
        self.bob1 = bob1
        self.bob2 = bob2
        dx = bob2.body.position.x - bob1.body.position.x
        dy = bob2.body.position.y - bob1.body.position.y
        self.length = (dx * dx + dy * dy) ** 0.5
        self.constraint = Contraint(bob1.body, bob2.body, self.length)
        self.name = f"Rod_{self.id}"

    def contains(self, x, y):
        x1, y1 = self.bob1.body.position.x, self.bob1.body.position.y
        x2, y2 = self.bob2.body.position.x, self.bob2.body.position.y

        line_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if line_len == 0:
            return False

        t = max(
            0,
            min(
                1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / (line_len**2)
            ),
        )
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)

        dist = ((x - proj_x) ** 2 + (y - proj_y) ** 2) ** 0.5
        return dist <= 8

    def cur_length(self):
        dx = self.bob2.body.position.x - self.bob1.body.position.x
        dy = self.bob2.body.position.y - self.bob1.body.position.y
        return (dx * dx + dy * dy) ** 0.5

    def get_debug_info(self):
        current_len = self.cur_length()
        return {
            "type": "Rod",
            "id": self.id,
            "name": self.name,
            "bob1": self.bob1.name,
            "bob2": self.bob2.name,
            "rest_length": round(self.length, 2),
            "current_length": round(current_len, 2),
            "stretch": round(current_len - self.length, 2),
            "bob1.x": round(self.bob1.body.position.x, 2),
            "bob1.y": round(self.bob1.body.position.y, 2),
            "bob2.x": round(self.bob2.body.position.x, 2),
            "bob2.y": round(self.bob2.body.position.y, 2),
        }

    def set_property(self, key, value):
        if key == "rest_length":
            self.length = max(1, float(value))
            self.constraint.l = self.length
        elif key == "bob1.x":
            self.bob1.body.position.x = float(value)
        elif key == "bob1.y":
            self.bob1.body.position.y = float(value)
        elif key == "bob2.x":
            self.bob2.body.position.x = float(value)
        elif key == "bob2.y":
            self.bob2.body.position.y = float(value)


class SimulationEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.bobs = []
        self.boxes = []
        self.rods = []
        self.running = False
        self.iterations = 8
        self.dragging_bob = None
        self.dragging_box = None
        self.collision_handler = Collision_Handler()
        self.ground = self.create_box(
            width / 2, height - 20, width, 40, pinned=True
        )

    def create_bob(self, x, y, pinned=False):
        bob = Bob(x, y, pinned)
        self.bobs.append(bob)
        self.collision_handler.add_body(bob.body)
        return bob

    def create_box(
        self, x, y, width=BOX_WIDTH, height=BOX_HEIGHT, pinned=False
    ):
        box = Box(x, y, width, height, pinned)
        self.boxes.append(box)
        self.collision_handler.add_body(box.body)
        return box

    def delete_box(self, box):
        self.rods = [r for r in self.rods if r.bob1 != box and r.bob2 != box]
        if box in self.boxes:
            self.boxes.remove(box)
            self.collision_handler.remove_body(box.body)

    def get_box_at(self, x, y):
        for box in reversed(self.boxes):
            if box.contains(x, y):
                return box
        return None

    def body_at(self, x, y):
        bob = self.get_bob_at(x, y)
        if bob:
            return bob
        box = self.get_box_at(x, y)
        if box:
            return box
        return None

    def force_at(self, x, y, fx, fy):
        body = self.body_at(x, y)
        if body:
            body.body.apply_point_force(Vector(fx, fy), Vector(x, y))
            return body
        return None

    def create_rod(self, bob1, bob2):
        for rod in self.rods:
            if (rod.bob1 == bob1 and rod.bob2 == bob2) or (
                rod.bob1 == bob2 and rod.bob2 == bob1
            ):
                return None
        rod = Rod(bob1, bob2)
        self.rods.append(rod)
        return rod

    def delete_bob(self, bob):
        self.rods = [r for r in self.rods if r.bob1 != bob and r.bob2 != bob]
        if bob in self.bobs:
            self.bobs.remove(bob)
            self.collision_handler.remove_body(bob.body)

    def get_bob_at(self, x, y):
        for bob in reversed(self.bobs):
            if bob.contains(x, y):
                return bob
        return None

    def get_rod_at(self, x, y):
        for rod in reversed(self.rods):
            if rod.contains(x, y):
                return rod
        return None

    def toggle_pin(self, obj):
        obj.pinned = not obj.pinned
        default_mass = 1 if isinstance(obj, Bob) else 2
        obj.body.mass = 0 if obj.pinned else default_mass
        obj.body.inv_mass = 1 / obj.body.mass if obj.body.mass > 0 else 0
        obj.body.inv_moi = (
            0 if obj.pinned else (1 / obj.body.moi if obj.body.moi > 0 else 0)
        )

    def set_dragging(self, obj):
        if isinstance(obj, Bob):
            self.dragging_bob = obj
        elif isinstance(obj, Box):
            self.dragging_box = obj

    def release(self):
        self.dragging_bob = None
        self.dragging_box = None

    def move(self, obj, x, y):
        obj.body.position.x = x
        obj.body.position.y = y
        if self.running:
            obj.body.velocity = Vector(0, 0)
            obj.body.ang_velocity = 0.0

    def clear_forces(self):
        for bob in self.bobs:
            bob.body.clear_forces()
            bob.body.clear_torque()

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def toggle(self):
        self.running = not self.running

    def clear(self):
        for bob in self.bobs:
            bob.body.clear_forces()
            bob.body.clear_torque()
        for box in self.boxes:
            box.body.clear_forces()
            box.body.clear_torque()
        self.bobs = []
        self.boxes = []
        self.rods = []
        self.running = False
        self.dragging_bob = None
        self.dragging_box = None
        self.collision_handler = Collision_Handler()
        Bob._id_counter = 0
        Box._id_counter = 0
        Rod._id_counter = 0
        self.ground = self.create_box(
            self.width / 2, self.height - 20, self.width, 40, pinned=True
        )

    def update(self, dt):
        if not self.running:
            return

        for bob in self.bobs:
            if bob != self.dragging_bob and not bob.pinned:
                bob.body.apply_point_force(
                    Vector(
                        GRAVITY.x * bob.body.mass, GRAVITY.y * bob.body.mass
                    ),
                    bob.body.position,
                )

        for box in self.boxes:
            if box != self.dragging_box and not box.pinned:
                box.body.apply_point_force(
                    Vector(
                        GRAVITY.x * box.body.mass, GRAVITY.y * box.body.mass
                    ),
                    box.body.position,
                )

        for bob in self.bobs:
            if bob != self.dragging_bob:
                bob.body.integrate(dt)

        for box in self.boxes:
            if box != self.dragging_box:
                box.body.integrate(dt)

        for _ in range(self.iterations):
            for rod in self.rods:
                rod.constraint.solve()

        self.collision_handler.update()

        # for bob in self.bobs:
        #     if bob.body.position.y > self.height - BOB_RADIUS:
        #         bob.body.position.y = self.height - BOB_RADIUS
        #         bob.body.velocity.y *= -0.5
        #     if bob.body.position.x < BOB_RADIUS:
        #         bob.body.position.x = BOB_RADIUS
        #         bob.body.velocity.x *= -0.5
        #     if bob.body.position.x > self.width - BOB_RADIUS:
        #         bob.body.position.x = self.width - BOB_RADIUS
        #         bob.body.velocity.x *= -0.5

        # for box in self.boxes:
        #     half_h = box.height / 2
        #     half_w = box.width / 2
        #     if box.body.position.y > self.height - half_h:
        #         box.body.position.y = self.height - half_h
        #         box.body.velocity.y *= -0.5
        #     if box.body.position.x < half_w:
        #         box.body.position.x = half_w
        #         box.body.velocity.x *= -0.5
        #     if box.body.position.x > self.width - half_w:
        #         box.body.position.x = self.width - half_w
        #         box.body.velocity.x *= -0.5

    def get_debug_info(self, fps, dt):
        return {
            "type": "Simulation",
            "name": "World",
            "is_running": self.running,
            "bob_count": len(self.bobs),
            "box_count": len(self.boxes),
            "rod_count": len(self.rods),
            "iterations": self.iterations,
            "gravity.x": GRAVITY.x,
            "gravity.y": GRAVITY.y,
            "fps": int(fps),
            "dt": round(dt * 1000, 2),
        }

    def set_property(self, key, value):
        global GRAVITY
        if key == "iterations":
            self.iterations = max(1, int(value))
        elif key == "gravity.x":
            GRAVITY = Vector(float(value), GRAVITY.y)
        elif key == "gravity.y":
            GRAVITY = Vector(GRAVITY.x, float(value))
