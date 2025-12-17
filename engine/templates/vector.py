class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def length(self):
        return (self.x**2 + self.y**2)**0.5
    
    def normalize(self):
        l = self.length()
        if l == 0:
            return Vector(0, 0)
        return Vector(self.x / l, self.y / l)
    
    def mul(self, scalar):
        self.x *= scalar
        self.y *= scalar
        return self
    
    def add(self, vector: "Vector"):
        self.x += vector.x
        self.y += vector.y
        return self
    
    def sub(self, vector: "Vector"):
        self.x -= vector.x
        self.y -= vector.y
        return self
    
    def div(self, scalar):
        if scalar == 0:
            raise ZeroDivisionError("zero division error")
        self.x /= scalar
        self.y /= scalar
        return self
        
    def dot(self, vector: "Vector"):
        return self.x * vector.x + self.y * vector.y
    
    def __repr__(self):
        return f"Vector({self.x}, {self.y})"
