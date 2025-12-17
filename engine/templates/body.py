from engine.templates.vector import Vector
from typing import List

class Body:
    def __init__(self):
        self.position = Vector(0,0)
        self.velocity = Vector(0,0)
        self.mass = 0
        self.total_force  = Vector(0,0)
        
    def apply_force(self,force:Vector):
        self.total_force.add(force)
        
    def clear_forces(self):
        self.total_force = Vector(0,0)
    
    def compute_dist(b1:"Body",b2:"Body"):
        v1,v2 = b1.position,b2.position
        return ((v2.x-v1.x)**2 + (v2.y-v1.y)**2)**0.5
        
    def integrate(self,dt):
        # semi euler's method
        if self.mass==0:
            a = 0 #immovable objects !!
        else:
            a = Vector(self.total_force.x/self.mass,self.total_force.y/self.mass)
            self.velocity.add(Vector(a.x*dt,a.y*dt))
            self.position.add(Vector(self.velocity.x*dt,self.velocity.y*dt))
            
        self.total_force= Vector(0,0)