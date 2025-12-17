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
        
    def integrate(self,dt):
        # semi euler's method
        if self.mass==0:
            a = 0 #immovable objects !!
        else:
            a = Vector(self.total_force.x/self.mass,self.total_force.y/self.mass)
            self.velocity.add(a*dt)
            self.position.add(Vector(self.velocity.x*dt,self.velocity.y*dt))
            
        self.total_force= Vector(0,0)