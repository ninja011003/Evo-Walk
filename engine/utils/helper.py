from engine.templates.vector import Vector




def mul(v1: Vector,v2:Vector)->Vector:
    return Vector(v1.x*v2.x,v1.y*v2.y)

def sub(v1: Vector,v2:Vector)->Vector:
    return Vector(v2.x-v1.x,v2.y-v1.y)

def cross(v1: Vector,v2:Vector)->float:
    return v1.x*v2.y - v1.y*v2.x

def compute_moi(**kwargs):
    if kwargs.get("shape")=="circle":
        if kwargs.get("radius") is None:
            raise ValueError("radius is required")
        return 0.5*kwargs.get("mass",0.0)*(kwargs.get("radius")**2) # I = 1/2 * m * r^2
    if kwargs.get("shape")=="rectangle":
        if kwargs.get("height") is None or  kwargs.get("width") is None:
            raise ValueError("height and width required")
        return (1/12)* kwargs.get("mass",0.0) * (kwargs.get("width")**2 + kwargs.get("height")**2) # I = 1/12 * m * (w^2 + h^2)
    return 0