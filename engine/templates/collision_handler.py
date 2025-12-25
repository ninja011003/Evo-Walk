from engine.templates.body import Body
from engine.templates.vector import Vector



class Collision_Handler:
    def __init__(self,bodies = []):
        self.bodies = bodies
    
    def detect_collision(b1: Body, b2: Body):
        p1,p2 = b1.position,b2.position
        if b1.shape=="circle" and b2.shape=="circle":
            d = Body.compute_dist(b1,b2)
            if d >= (b1.radius + b2.radius):
                return None
            if d==0:
                rel_v = Vector(b2.velocity.x-b1.velocity.x, b2.velocity.y-b1.velocity.y)
                if rel_v.length()>0:
                    n = rel_v.normalize()
                else:
                    n = Vector(1,0)
                penetration = b1.radius+b2.radius
            else:
                n = Vector(p2.x-p1.x, p2.y-p1.y).normalize()
                penetration = (b1.radius + b2.radius) - d
                
            contact_pt = Vector(p1.x + n.x* b1.radius , p1.y + n.y * b1.radius) #this line is cursed and highly approximated !
            
            return n, penetration, contact_pt
        
    
        
        