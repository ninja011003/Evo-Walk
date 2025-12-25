from engine.templates.vector import Vector
from engine.templates.body import Body
from engine.utils.helper import mul


class Contraint:
    def __init__(self, b1: Body, b2: Body, l: float):
        self.b1 = b1
        self.b2 = b2
        self.l = l

    # TODO solve positional contrain iteratively and velocity once per solve
    def solve(self):
        # correction cal
        dist = Vector(
            self.b2.position.x - self.b1.position.x,
            self.b2.position.y - self.b1.position.y,
        )
        mod_dist = dist.length()
        if mod_dist == 0:
            return self
        err = mod_dist - self.l
        corr = Vector(dist.x / mod_dist, dist.y / mod_dist)
        corr.x *= err
        corr.y *= err

        # infinite mass handling
        if self.b1.mass:
            w1 = 1 / self.b1.mass
        else:
            w1 = 0

        if self.b2.mass:
            w2 = 1 / self.b2.mass
        else:
            w2 = 0

        if w1 + w2 != 0:
            # correction ratio based on mass
            cor_b1 = w1 / (w1 + w2)
            cor_b2 = -w2 / (w1 + w2)

            # postional correction
            self.b1.position.x += cor_b1 * corr.x
            self.b1.position.y += cor_b1 * corr.y
            self.b2.position.x += cor_b2 * corr.x
            self.b2.position.y += cor_b2 * corr.y

            # velocity correction
            v_rel = Vector(
                self.b2.velocity.x - self.b1.velocity.x,
                self.b2.velocity.y - self.b1.velocity.y,
            )
            r = Vector(
                self.b2.position.x - self.b1.position.x,
                self.b2.position.y - self.b1.position.y,
            )
            r_cap = r.normalize()
            v_rad_cap = v_rel.dot(r_cap)
            v_rad = Vector(r_cap.x * v_rad_cap, r_cap.y * v_rad_cap)
            # v_rad => velocity correction

            vel_cor_b1 = (
                w1 / (w1 + w2)
            )  # sign convention changes...cuz we look into the change in projection and based on relative velocity defined above
            vel_cor_b2 = -w2 / (w1 + w2)

            """
                err > 0 -> stretched
                err < 0 -> compressed
                v_rel (dot) r_cap > 0 -> separating
                v_rel (dot) r_cap < 0 -> approaching
                **remove velocity of for
                ==>stretched+ seperating
                ==>compressed + compressing
            """
            dist = Vector(
                self.b2.position.x - self.b1.position.x,
                self.b2.position.y - self.b1.position.y,
            )
            mod_dist = dist.length()
            if mod_dist == 0:
                return self
            err = mod_dist - self.l
            _check = (
                v_rel.dot(r_cap) * (err)
            )  # velocity corrected only if err exist after positional correction
            if _check > 0:
                self.b1.velocity.x += vel_cor_b1 * v_rad.x
                self.b1.velocity.y += vel_cor_b1 * v_rad.y
                self.b2.velocity.x += vel_cor_b2 * v_rad.x
                self.b2.velocity.y += vel_cor_b2 * v_rad.y
        return self
