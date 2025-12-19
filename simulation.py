from engine.templates.vector import Vector
from engine.templates.body import Body
from engine.templates.contraint import Contraint

BOB_RADIUS = 12
GRAVITY = Vector(0, 980)

class Bob:
    _id_counter = 0
    
    def __init__(self, x, y, pinned=False):
        Bob._id_counter += 1
        self.id = Bob._id_counter
        self.body = Body()
        self.body.position = Vector(x, y)
        self.body.mass = 0 if pinned else 1
        self.pinned = pinned
        self.radius = BOB_RADIUS
        self.name = f"Bob_{self.id}"

    def contains(self, x, y):
        dx = x - self.body.position.x
        dy = y - self.body.position.y
        return (dx * dx + dy * dy) <= (self.radius + 8) ** 2

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
            self.pinned = (self.body.mass == 0)
            self.radius = BOB_RADIUS*(self.body.mass/5)
        elif key == "pinned":
            self.pinned = bool(value)
            self.body.mass = 0 if self.pinned else 1
        elif key == "radius":
            self.radius = max(5, int(value))

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
        
        t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / (line_len ** 2)))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        dist = ((x - proj_x) ** 2 + (y - proj_y) ** 2) ** 0.5
        return dist <= 8

    def get_current_length(self):
        dx = self.bob2.body.position.x - self.bob1.body.position.x
        dy = self.bob2.body.position.y - self.bob1.body.position.y
        return (dx * dx + dy * dy) ** 0.5

    def get_debug_info(self):
        current_len = self.get_current_length()
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
        self.rods = []
        self.running = False
        self.iterations = 8
        self.dragging_bob = None

    def create_bob(self, x, y, pinned=False):
        bob = Bob(x, y, pinned)
        self.bobs.append(bob)
        return bob

    def create_rod(self, bob1, bob2):
        for rod in self.rods:
            if (rod.bob1 == bob1 and rod.bob2 == bob2) or \
               (rod.bob1 == bob2 and rod.bob2 == bob1):
                return None
        rod = Rod(bob1, bob2)
        self.rods.append(rod)
        return rod

    def delete_bob(self, bob):
        self.rods = [r for r in self.rods if r.bob1 != bob and r.bob2 != bob]
        if bob in self.bobs:
            self.bobs.remove(bob)

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

    def toggle_pin(self, bob):
        bob.pinned = not bob.pinned
        bob.body.mass = 0 if bob.pinned else 1

    def set_dragging(self, bob):
        self.dragging_bob = bob

    def release_dragging(self):
        self.dragging_bob = None

    def move_bob(self, bob, x, y):
        bob.body.position.x = x
        bob.body.position.y = y
        if self.running:
            bob.body.velocity = Vector(0, 0)

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def toggle(self):
        self.running = not self.running

    def clear(self):
        self.bobs = []
        self.rods = []
        self.running = False
        self.dragging_bob = None
        Bob._id_counter = 0
        Rod._id_counter = 0

    def update(self, dt):
        if not self.running:
            return
        
        for bob in self.bobs:
            if bob != self.dragging_bob and not bob.pinned:
                bob.body.apply_force(Vector(GRAVITY.x * bob.body.mass, GRAVITY.y * bob.body.mass))

        for bob in self.bobs:
            if bob != self.dragging_bob:
                bob.body.integrate(dt)

        for _ in range(self.iterations):
            for rod in self.rods:
                rod.constraint.solve()

        for bob in self.bobs:
            if bob.body.position.y > self.height - BOB_RADIUS:
                bob.body.position.y = self.height - BOB_RADIUS
                bob.body.velocity.y *= -0.5
            if bob.body.position.x < BOB_RADIUS:
                bob.body.position.x = BOB_RADIUS
                bob.body.velocity.x *= -0.5
            if bob.body.position.x > self.width - BOB_RADIUS:
                bob.body.position.x = self.width - BOB_RADIUS
                bob.body.velocity.x *= -0.5

    def get_debug_info(self, fps, dt):
        return {
            "type": "Simulation",
            "name": "World",
            "is_running": self.running,
            "bob_count": len(self.bobs),
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

