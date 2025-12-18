from engine.templates.vector import Vector
from engine.templates.body import Body


def compute_dist(x1,y1,x2,y2):
    return ((x2-x1)**2 + (y2-y1)**2)**0.5

def mul(v1: Vector,v2:Vector)->Vector:
    return Vector(v1.x*v2.x,v1.y*v2.y)