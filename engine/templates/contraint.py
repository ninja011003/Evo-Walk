from engine.templates.vector import Vector
from engine.templates.body import Body
from engine.utils.helper import cross
import math


class Contraint:
    def __init__(self, body_a: Body, body_b: Body, local_a: Vector = None, local_b: Vector = None, length: float = 0.0):
        self.body_a = body_a
        self.body_b = body_b
        self.local_a = local_a if local_a else Vector(0, 0)
        self.local_b = local_b if local_b else Vector(0, 0)
        self.length = length

    def local_to_world(self, body, local_point):
        cos_a = math.cos(body.orientation)
        sin_a = math.sin(body.orientation)
        rotated_x = local_point.x * cos_a - local_point.y * sin_a
        rotated_y = local_point.x * sin_a + local_point.y * cos_a
        return Vector(body.position.x + rotated_x, body.position.y + rotated_y)

    def get_world_anchors(self):
        world_a = self.local_to_world(self.body_a, self.local_a)
        world_b = self.local_to_world(self.body_b, self.local_b)
        return world_a, world_b

    def solve(self):
        world_a, world_b = self.get_world_anchors()

        dist = Vector(world_b.x - world_a.x, world_b.y - world_a.y)
        mod_dist = dist.length()
        if mod_dist == 0:
            return self

        err = mod_dist - self.length
        if abs(err) < 1e-6:
            return self

        n = Vector(dist.x / mod_dist, dist.y / mod_dist)

        r_a = Vector(world_a.x - self.body_a.position.x, world_a.y - self.body_a.position.y)
        r_b = Vector(world_b.x - self.body_b.position.x, world_b.y - self.body_b.position.y)

        r_a_cross_n = cross(r_a, n)
        r_b_cross_n = cross(r_b, n)

        w_a = self.body_a.inv_mass + self.body_a.inv_moi * r_a_cross_n * r_a_cross_n
        w_b = self.body_b.inv_mass + self.body_b.inv_moi * r_b_cross_n * r_b_cross_n

        total_w = w_a + w_b
        if total_w == 0:
            return self

        lam = err / total_w

        impulse = Vector(n.x * lam, n.y * lam)

        self.body_a.position.x += impulse.x * self.body_a.inv_mass
        self.body_a.position.y += impulse.y * self.body_a.inv_mass
        self.body_a.orientation += self.body_a.inv_moi * cross(r_a, impulse)

        self.body_b.position.x -= impulse.x * self.body_b.inv_mass
        self.body_b.position.y -= impulse.y * self.body_b.inv_mass
        self.body_b.orientation -= self.body_b.inv_moi * cross(r_b, impulse)

        world_a, world_b = self.get_world_anchors()
        dist = Vector(world_b.x - world_a.x, world_b.y - world_a.y)
        mod_dist = dist.length()
        if mod_dist == 0:
            return self

        err = mod_dist - self.length
        n = Vector(dist.x / mod_dist, dist.y / mod_dist)

        r_a = Vector(world_a.x - self.body_a.position.x, world_a.y - self.body_a.position.y)
        r_b = Vector(world_b.x - self.body_b.position.x, world_b.y - self.body_b.position.y)

        v_a = Vector(
            self.body_a.velocity.x - self.body_a.ang_velocity * r_a.y,
            self.body_a.velocity.y + self.body_a.ang_velocity * r_a.x
        )
        v_b = Vector(
            self.body_b.velocity.x - self.body_b.ang_velocity * r_b.y,
            self.body_b.velocity.y + self.body_b.ang_velocity * r_b.x
        )

        v_rel = Vector(v_b.x - v_a.x, v_b.y - v_a.y)
        v_n = v_rel.dot(n)

        if abs(v_n) < 1e-6:
            return self

        r_a_cross_n = cross(r_a, n)
        r_b_cross_n = cross(r_b, n)
        w_a = self.body_a.inv_mass + self.body_a.inv_moi * r_a_cross_n * r_a_cross_n
        w_b = self.body_b.inv_mass + self.body_b.inv_moi * r_b_cross_n * r_b_cross_n
        total_w = w_a + w_b

        if total_w == 0:
            return self

        lam_v = v_n / total_w
        impulse_v = Vector(n.x * lam_v, n.y * lam_v)

        self.body_a.velocity.x += impulse_v.x * self.body_a.inv_mass
        self.body_a.velocity.y += impulse_v.y * self.body_a.inv_mass
        self.body_a.ang_velocity += self.body_a.inv_moi * cross(r_a, impulse_v)

        self.body_b.velocity.x -= impulse_v.x * self.body_b.inv_mass
        self.body_b.velocity.y -= impulse_v.y * self.body_b.inv_mass
        self.body_b.ang_velocity -= self.body_b.inv_moi * cross(r_b, impulse_v)

        return self
