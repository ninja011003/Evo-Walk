from engine.templates.body import Body
from engine.templates.vector import Vector
import math


def get_rectangle_corners(body: Body):
    cx, cy = body.position.x, body.position.y
    hw, hh = body.width / 2, body.height / 2
    angle = body.orientation
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    corners = [
        Vector(
            cx + (-hw * cos_a - (-hh) * sin_a),
            cy + (-hw * sin_a + (-hh) * cos_a),
        ),
        Vector(
            cx + (hw * cos_a - (-hh) * sin_a), cy + (hw * sin_a + (-hh) * cos_a)
        ),
        Vector(cx + (hw * cos_a - hh * sin_a), cy + (hw * sin_a + hh * cos_a)),
        Vector(
            cx + (-hw * cos_a - hh * sin_a), cy + (-hw * sin_a + hh * cos_a)
        ),
    ]
    return corners


def get_rectangle_axes(body: Body):
    angle = body.orientation
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return [Vector(cos_a, sin_a), Vector(-sin_a, cos_a)]


def project_polygon(corners, axis):
    min_proj = float("inf")
    max_proj = float("-inf")
    for corner in corners:
        proj = corner.x * axis.x + corner.y * axis.y
        min_proj = min(min_proj, proj)
        max_proj = max(max_proj, proj)
    return min_proj, max_proj


def get_overlap(min1, max1, min2, max2):
    if max1 < min2 or max2 < min1:
        return 0, 0
    overlap = min(max1, max2) - max(min1, min2)
    if (min1 + max1) / 2 < (min2 + max2) / 2:
        return overlap, 1
    else:
        return overlap, -1


def point_in_rectangle(point, corners):
    def sign(p1, p2, p3):
        return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)

    d1 = sign(point, corners[0], corners[1])
    d2 = sign(point, corners[1], corners[2])
    d3 = sign(point, corners[2], corners[3])
    d4 = sign(point, corners[3], corners[0])

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0) or (d4 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0) or (d4 > 0)

    return not (has_neg and has_pos)


def closest_point_on_segment(point, seg_start, seg_end):
    dx = seg_end.x - seg_start.x
    dy = seg_end.y - seg_start.y
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return Vector(seg_start.x, seg_start.y)
    t = max(
        0,
        min(
            1,
            ((point.x - seg_start.x) * dx + (point.y - seg_start.y) * dy)
            / length_sq,
        ),
    )
    return Vector(seg_start.x + t * dx, seg_start.y + t * dy)


class Collision_Handler:
    def __init__(
        self,
        bodies=None,
        position_correction_percent=0.4,
        slop=0.01,
        resting_threshold=0.5,
    ):
        self.bodies = (
            bodies if bodies is not None else []
        )  # fix for shared List problem
        self.position_correction_percent = position_correction_percent
        self.slop = slop
        self.resting_threshold = resting_threshold

    def add_body(self, body: Body):
        self.bodies.append(body)

    def remove_body(self, body: Body):
        if body in self.bodies:
            self.bodies.remove(body)

    def update(self):
        collisions = []
        for i in range(len(self.bodies)):
            for j in range(i + 1, len(self.bodies)):
                b1 = self.bodies[i]
                b2 = self.bodies[j]
                result = self.detect_collision(b1, b2)
                if result is not None:
                    n, penetration, contact_point = result
                    collisions.append((b1, b2, n, penetration, contact_point))

        collisions.sort(key=lambda c: c[3], reverse=True)

        for b1, b2, n, penetration, contact_point in collisions:
            self.resolve_collision(b1, b2, n, penetration, contact_point)

    def detect_collision(self, b1: Body, b2: Body):
        p1, p2 = b1.position, b2.position

        if b1.shape == "circle" and b2.shape == "circle":
            d = Body.compute_dist(b1, b2)
            if d >= (b1.radius + b2.radius):
                return None
            if d == 0:
                rel_v = Vector(
                    b2.velocity.x - b1.velocity.x, b2.velocity.y - b1.velocity.y
                )
                if rel_v.length() > 0:
                    n = rel_v.normalize()
                else:
                    n = Vector(1, 0)
                penetration = b1.radius + b2.radius
            else:
                n = Vector(p2.x - p1.x, p2.y - p1.y).normalize()
                penetration = (b1.radius + b2.radius) - d

            contact_pt = Vector(p1.x + n.x * b1.radius, p1.y + n.y * b1.radius)
            return n, penetration, contact_pt

        if b1.shape == "rectangle" and b2.shape == "rectangle":
            corners1 = get_rectangle_corners(b1)
            corners2 = get_rectangle_corners(b2)

            axes = get_rectangle_axes(b1) + get_rectangle_axes(b2)

            min_overlap = float("inf")
            collision_normal = None

            for axis in axes:
                min1, max1 = project_polygon(corners1, axis)
                min2, max2 = project_polygon(corners2, axis)

                overlap, direction = get_overlap(min1, max1, min2, max2)

                if overlap <= 0:
                    return None

                if overlap < min_overlap:
                    min_overlap = overlap
                    collision_normal = Vector(
                        axis.x * direction, axis.y * direction
                    )

            penetration = min_overlap

            contact_points = []
            for corner in corners1:
                if point_in_rectangle(corner, corners2):
                    contact_points.append(corner)
            for corner in corners2:
                if point_in_rectangle(corner, corners1):
                    contact_points.append(corner)

            if len(contact_points) == 0:
                for i in range(4):
                    for j in range(4):
                        seg1_start = corners1[i]
                        seg1_end = corners1[(i + 1) % 4]
                        seg2_start = corners2[j]
                        seg2_end = corners2[(j + 1) % 4]

                        cp1 = closest_point_on_segment(
                            seg2_start, seg1_start, seg1_end
                        )
                        cp2 = closest_point_on_segment(
                            seg2_end, seg1_start, seg1_end
                        )
                        cp3 = closest_point_on_segment(
                            seg1_start, seg2_start, seg2_end
                        )
                        cp4 = closest_point_on_segment(
                            seg1_end, seg2_start, seg2_end
                        )

                        contact_points.extend([cp1, cp2, cp3, cp4])

            if len(contact_points) == 0:
                contact_pt = Vector((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
            else:
                avg_x = sum(cp.x for cp in contact_points) / len(contact_points)
                avg_y = sum(cp.y for cp in contact_points) / len(contact_points)
                contact_pt = Vector(avg_x, avg_y)

            return collision_normal, penetration, contact_pt

        if b1.shape == "circle" and b2.shape == "rectangle":
            circle = b1
            rect = b2
            flip_normal = False
        elif b1.shape == "rectangle" and b2.shape == "circle":
            circle = b2
            rect = b1
            flip_normal = True
        else:
            return None

        cx, cy = circle.position.x, circle.position.y
        rx, ry = rect.position.x, rect.position.y
        angle = rect.orientation

        cos_a = math.cos(-angle)
        sin_a = math.sin(-angle)
        local_cx = cos_a * (cx - rx) - sin_a * (cy - ry)
        local_cy = sin_a * (cx - rx) + cos_a * (cy - ry)

        hw, hh = rect.width / 2, rect.height / 2
        closest_x = max(-hw, min(local_cx, hw))
        closest_y = max(-hh, min(local_cy, hh))

        dx = local_cx - closest_x
        dy = local_cy - closest_y
        dist_sq = dx * dx + dy * dy

        if dist_sq >= circle.radius * circle.radius:
            return None

        dist = math.sqrt(dist_sq)

        if dist == 0:
            if abs(local_cx) / hw > abs(local_cy) / hh:
                if local_cx > 0:
                    local_normal = Vector(1, 0)
                else:
                    local_normal = Vector(-1, 0)
                penetration = hw - abs(local_cx) + circle.radius
            else:
                if local_cy > 0:
                    local_normal = Vector(0, 1)
                else:
                    local_normal = Vector(0, -1)
                penetration = hh - abs(local_cy) + circle.radius
            local_contact = Vector(closest_x, closest_y)
        else:
            local_normal = Vector(dx / dist, dy / dist)
            penetration = circle.radius - dist
            local_contact = Vector(closest_x, closest_y)

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        world_normal = Vector(
            cos_a * local_normal.x - sin_a * local_normal.y,
            sin_a * local_normal.x + cos_a * local_normal.y,
        )
        world_contact = Vector(
            rx + cos_a * local_contact.x - sin_a * local_contact.y,
            ry + sin_a * local_contact.x + cos_a * local_contact.y,
        )

        if flip_normal:
            world_normal = Vector(-world_normal.x, -world_normal.y)

        return world_normal, penetration, world_contact

    def compute_relative_velocity(
        self, b1: Body, b2: Body, contact_point: Vector
    ):
        r1 = Vector(
            contact_point.x - b1.position.x, contact_point.y - b1.position.y
        )
        r2 = Vector(
            contact_point.x - b2.position.x, contact_point.y - b2.position.y
        )
        v1_at_contact = Vector(
            b1.velocity.x - b1.ang_velocity * r1.y,
            b1.velocity.y + b1.ang_velocity * r1.x,
        )
        v2_at_contact = Vector(
            b2.velocity.x - b2.ang_velocity * r2.y,
            b2.velocity.y + b2.ang_velocity * r2.x,
        )
        return Vector(
            v2_at_contact.x - v1_at_contact.x, v2_at_contact.y - v1_at_contact.y
        )

    def resolve_collision(
        self,
        b1: Body,
        b2: Body,
        n: Vector,
        penetration: float,
        contact_point: Vector,
    ):
        rel_vel = self.compute_relative_velocity(b1, b2, contact_point)
        vel_along_normal = rel_vel.x * n.x + rel_vel.y * n.y

        if vel_along_normal > 0:
            n = Vector(-n.x, -n.y)
            vel_along_normal = -vel_along_normal

        if vel_along_normal >= -1e-6:
            return

        self.apply_pos_corr(b1, b2, n, penetration)
        self.apply_impulse(b1, b2, n, contact_point)

    def apply_pos_corr(self, b1: Body, b2: Body, n: Vector, penetration: float):
        total_inv_mass = b1.inv_mass + b2.inv_mass
        if total_inv_mass == 0:
            return

        correction_magnitude = (
            max(penetration - self.slop, 0)
            * self.position_correction_percent
            / total_inv_mass
        )

        correction = Vector(
            n.x * correction_magnitude, n.y * correction_magnitude
        )

        b1.position.x -= correction.x * b1.inv_mass
        b1.position.y -= correction.y * b1.inv_mass
        b2.position.x += correction.x * b2.inv_mass
        b2.position.y += correction.y * b2.inv_mass

    def apply_impulse(
        self, b1: Body, b2: Body, n: Vector, contact_point: Vector
    ):
        friction = math.sqrt(b1.friction * b2.friction)

        r1 = Vector(
            contact_point.x - b1.position.x, contact_point.y - b1.position.y
        )
        r2 = Vector(
            contact_point.x - b2.position.x, contact_point.y - b2.position.y
        )

        v1_at_contact = Vector(
            b1.velocity.x - b1.ang_velocity * r1.y,
            b1.velocity.y + b1.ang_velocity * r1.x,
        )
        v2_at_contact = Vector(
            b2.velocity.x - b2.ang_velocity * r2.y,
            b2.velocity.y + b2.ang_velocity * r2.x,
        )

        rel_vel = Vector(
            v2_at_contact.x - v1_at_contact.x, v2_at_contact.y - v1_at_contact.y
        )

        vel_along_normal = rel_vel.x * n.x + rel_vel.y * n.y

        if abs(vel_along_normal) < self.resting_threshold:
            restitution = 0.0
        else:
            restitution = math.sqrt(b1.restitution * b2.restitution)

        r1_cross_n = r1.x * n.y - r1.y * n.x
        r2_cross_n = r2.x * n.y - r2.y * n.x

        inv_mass_sum = (
            b1.inv_mass
            + b2.inv_mass
            + (r1_cross_n * r1_cross_n) * b1.inv_moi
            + (r2_cross_n * r2_cross_n) * b2.inv_moi
        )

        if inv_mass_sum == 0:
            return

        j = -(1 + restitution) * vel_along_normal / inv_mass_sum

        if j < 0:
            return

        impulse = Vector(n.x * j, n.y * j)

        b1.velocity.x -= impulse.x * b1.inv_mass
        b1.velocity.y -= impulse.y * b1.inv_mass
        b2.velocity.x += impulse.x * b2.inv_mass
        b2.velocity.y += impulse.y * b2.inv_mass

        b1.ang_velocity -= (r1.x * impulse.y - r1.y * impulse.x) * b1.inv_moi
        b2.ang_velocity += (r2.x * impulse.y - r2.y * impulse.x) * b2.inv_moi

        tangent = Vector(
            rel_vel.x - vel_along_normal * n.x,
            rel_vel.y - vel_along_normal * n.y,
        )
        tangent_length = math.sqrt(
            tangent.x * tangent.x + tangent.y * tangent.y
        )

        if tangent_length < 1e-10:
            return

        tangent = Vector(tangent.x / tangent_length, tangent.y / tangent_length)

        r1_cross_t = r1.x * tangent.y - r1.y * tangent.x
        r2_cross_t = r2.x * tangent.y - r2.y * tangent.x

        inv_mass_sum_tangent = (
            b1.inv_mass
            + b2.inv_mass
            + (r1_cross_t * r1_cross_t) * b1.inv_moi
            + (r2_cross_t * r2_cross_t) * b2.inv_moi
        )

        if inv_mass_sum_tangent == 0:
            return

        vel_along_tangent = rel_vel.x * tangent.x + rel_vel.y * tangent.y

        jt = -vel_along_tangent / inv_mass_sum_tangent

        max_friction = j * friction
        if jt > max_friction:
            jt = max_friction
        elif jt < -max_friction:
            jt = -max_friction

        friction_impulse = Vector(tangent.x * jt, tangent.y * jt)

        b1.velocity.x -= friction_impulse.x * b1.inv_mass
        b1.velocity.y -= friction_impulse.y * b1.inv_mass
        b2.velocity.x += friction_impulse.x * b2.inv_mass
        b2.velocity.y += friction_impulse.y * b2.inv_mass

        b1.ang_velocity -= (
            r1.x * friction_impulse.y - r1.y * friction_impulse.x
        ) * b1.inv_moi
        b2.ang_velocity += (
            r2.x * friction_impulse.y - r2.y * friction_impulse.x
        ) * b2.inv_moi
