import pygame

from engine.templates.vector import Vector
from engine.templates.body import Body
from engine.templates.contraint import Contraint
from engine.utils.helper import compute_dist

pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

ball = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("purple")
    pygame.mouse.set_cursor(*pygame.cursors.broken_x)
    
    a =pygame.draw.circle(screen, "red", ball, 40)
    
    
    cur_x, cur_y = pygame.mouse.get_pos()
    cursor =Vector(cur_x,cur_y)
    ball_pos = Vector(ball.x,ball.y)
    if Vector.compute_dist(cursor,ball_pos)<40:
        pygame.draw.circle(screen, "blue", ball, 40)

    pygame.display.flip()

    dt = clock.tick(60) / 1000

pygame.quit()