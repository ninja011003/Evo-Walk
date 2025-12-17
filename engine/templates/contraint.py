from engine.templates.vector import Vector
from engine.templates.body import Body



class Contraint:    
    def __init__(self,b1: Body , b2: Body , l :float):
        self.b1 = b1
        self.b2 = b2
        self.l = l
    
    def solve(self):
        #correction cal
        dist= Vector(self.b2.position.x-self.b1.position.x , self.b2.position.y-self.b1.position.y)
        mod_dist = dist.length()
        if mod_dist==0:
            return self
        err = mod_dist - self.l
        corr = Vector(dist.x/mod_dist,dist.y/mod_dist)
        corr.x*=err
        corr.y*=err
        
        #infinite mass handling
        if self.b1.mass:
            w1 = 1/self.b1.mass
        else:
            w1 = 0
            
        if self.b2.mass:
            w2 = 1/self.b2.mass
        else:
            w2 = 0
        
        if w1+w2!=0:
            cor_b1 = w1/(w1+w2)
            cor_b2 = -w2/(w1+w2)
            self.b1.position.x+= cor_b1*corr.x
            self.b1.position.y+= cor_b1*corr.y
            self.b2.position.x+= cor_b2*corr.x
            self.b2.position.y+= cor_b2*corr.y
        return self
        