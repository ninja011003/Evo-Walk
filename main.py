import pygame
import sys
from engine.templates.vector import Vector
from engine.templates.body import Body
from engine.templates.contraint import Contraint

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1280, 720
TOOLBAR_HEIGHT = 60
CANVAS_TOP = TOOLBAR_HEIGHT

BG_COLOR = (18, 18, 24)
TOOLBAR_BG = (28, 28, 36)
BOB_COLOR = (255, 107, 107)
BOB_HOVER = (255, 140, 140)
BOB_SELECTED = (255, 200, 100)
ROD_COLOR = (100, 181, 246)
BTN_COLOR = (45, 45, 60)
BTN_HOVER = (65, 65, 85)
BTN_ACTIVE = (80, 200, 120)
TEXT_COLOR = (220, 220, 230)
GRID_COLOR = (30, 30, 40)

BOB_RADIUS = 12
GRAVITY = Vector(0, 980)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Physics Simulation")
clock = pygame.time.Clock()

font_large = pygame.font.SysFont("SF Pro Display", 18, bold=True)
font_small = pygame.font.SysFont("SF Pro Display", 14)

class Bob:
    def __init__(self, x, y, pinned=False):
        self.body = Body()
        self.body.position = Vector(x, y)
        self.body.mass = 0 if pinned else 1
        self.pinned = pinned
        self.radius = BOB_RADIUS

    def contains(self, x, y):
        dx = x - self.body.position.x
        dy = y - self.body.position.y
        return (dx * dx + dy * dy) <= (self.radius + 8) ** 2

class Rod:
    def __init__(self, bob1, bob2):
        self.bob1 = bob1
        self.bob2 = bob2
        dx = bob2.body.position.x - bob1.body.position.x
        dy = bob2.body.position.y - bob1.body.position.y
        self.length = (dx * dx + dy * dy) ** 0.5
        self.constraint = Contraint(bob1.body, bob2.body, self.length)

class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.hovered = False
        self.active = False

    def draw(self, surface):
        if self.active:
            color = BTN_ACTIVE
        elif self.hovered:
            color = BTN_HOVER
        else:
            color = BTN_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (60, 60, 80), self.rect, 1, border_radius=6)
        text_surf = font_small.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

class Simulation:
    def __init__(self):
        self.bobs = []
        self.rods = []
        self.selected_bob = None
        self.dragging_bob = None
        self.connecting_bob = None
        self.running = False
        self.mode = "bob"
        self.iterations = 8

        self.buttons = []
        self.setup_ui()

    def setup_ui(self):
        btn_y = 12
        btn_h = 36
        
        self.bob_btn = Button(20, btn_y, 80, btn_h, "Bob", self.set_bob_mode)
        self.rod_btn = Button(110, btn_y, 80, btn_h, "Rod", self.set_rod_mode)
        self.pin_btn = Button(200, btn_y, 80, btn_h, "Pin", self.set_pin_mode)
        self.start_btn = Button(WIDTH - 200, btn_y, 80, btn_h, "Start", self.toggle_simulation)
        self.clear_btn = Button(WIDTH - 100, btn_y, 80, btn_h, "Clear", self.clear_all)
        
        self.buttons = [self.bob_btn, self.rod_btn, self.pin_btn, self.start_btn, self.clear_btn]
        self.bob_btn.active = True

    def set_bob_mode(self):
        self.mode = "bob"
        self.bob_btn.active = True
        self.rod_btn.active = False
        self.pin_btn.active = False

    def set_rod_mode(self):
        self.mode = "rod"
        self.bob_btn.active = False
        self.rod_btn.active = True
        self.pin_btn.active = False

    def set_pin_mode(self):
        self.mode = "pin"
        self.bob_btn.active = False
        self.rod_btn.active = False
        self.pin_btn.active = True

    def toggle_simulation(self):
        self.running = not self.running
        self.start_btn.text = "Stop" if self.running else "Start"
        self.start_btn.active = self.running

    def clear_all(self):
        self.bobs = []
        self.rods = []
        self.running = False
        self.start_btn.text = "Start"
        self.start_btn.active = False
        self.connecting_bob = None

    def get_bob_at(self, x, y):
        for bob in reversed(self.bobs):
            if bob.contains(x, y):
                return bob
        return None

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            if y < CANVAS_TOP:
                return
            
            clicked_bob = self.get_bob_at(x, y)
            
            if self.running:
                if clicked_bob:
                    self.dragging_bob = clicked_bob
            else:
                if self.mode == "bob":
                    if clicked_bob:
                        self.dragging_bob = clicked_bob
                    else:
                        new_bob = Bob(x, y, pinned=False)
                        self.bobs.append(new_bob)
                        self.dragging_bob = new_bob
                elif self.mode == "pin":
                    if clicked_bob:
                        clicked_bob.pinned = not clicked_bob.pinned
                        clicked_bob.body.mass = 0 if clicked_bob.pinned else 1
                    else:
                        new_bob = Bob(x, y, pinned=True)
                        self.bobs.append(new_bob)
                elif self.mode == "rod":
                    if clicked_bob:
                        if self.connecting_bob is None:
                            self.connecting_bob = clicked_bob
                        elif self.connecting_bob != clicked_bob:
                            exists = False
                            for rod in self.rods:
                                if (rod.bob1 == self.connecting_bob and rod.bob2 == clicked_bob) or \
                                   (rod.bob1 == clicked_bob and rod.bob2 == self.connecting_bob):
                                    exists = True
                                    break
                            if not exists:
                                new_rod = Rod(self.connecting_bob, clicked_bob)
                                self.rods.append(new_rod)
                            self.connecting_bob = None

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_bob = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_bob:
                x, y = event.pos
                y = max(CANVAS_TOP + BOB_RADIUS, y)
                self.dragging_bob.body.position.x = x
                self.dragging_bob.body.position.y = y
                if self.running:
                    self.dragging_bob.body.velocity = Vector(0, 0)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.connecting_bob = None
            elif event.key == pygame.K_SPACE:
                self.toggle_simulation()
            elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                x, y = pygame.mouse.get_pos()
                bob_to_delete = self.get_bob_at(x, y)
                if bob_to_delete and not self.running:
                    self.rods = [r for r in self.rods if r.bob1 != bob_to_delete and r.bob2 != bob_to_delete]
                    self.bobs.remove(bob_to_delete)
                    if self.connecting_bob == bob_to_delete:
                        self.connecting_bob = None

    def update(self, dt):
        if not self.running:
            return
        
        for bob in self.bobs:
            if bob != self.dragging_bob and not bob.pinned:
                bob.body.apply_force(Vector(GRAVITY.x * bob.body.mass, GRAVITY.y * bob.body.mass))

        for bob in self.bobs:
            if bob != self.dragging_bob:
                bob.body.integrate(dt)

        for _ in range(self.iterations):
            for rod in self.rods:
                rod.constraint.solve()

        for bob in self.bobs:
            if bob.body.position.y > HEIGHT - BOB_RADIUS:
                bob.body.position.y = HEIGHT - BOB_RADIUS
                bob.body.velocity.y *= -0.5
            if bob.body.position.x < BOB_RADIUS:
                bob.body.position.x = BOB_RADIUS
                bob.body.velocity.x *= -0.5
            if bob.body.position.x > WIDTH - BOB_RADIUS:
                bob.body.position.x = WIDTH - BOB_RADIUS
                bob.body.velocity.x *= -0.5

    def draw_grid(self, surface):
        spacing = 40
        for x in range(0, WIDTH, spacing):
            pygame.draw.line(surface, GRID_COLOR, (x, CANVAS_TOP), (x, HEIGHT), 1)
        for y in range(CANVAS_TOP, HEIGHT, spacing):
            pygame.draw.line(surface, GRID_COLOR, (0, y), (WIDTH, y), 1)

    def draw(self, surface):
        surface.fill(BG_COLOR)
        self.draw_grid(surface)
        
        pygame.draw.rect(surface, TOOLBAR_BG, (0, 0, WIDTH, TOOLBAR_HEIGHT))
        pygame.draw.line(surface, (40, 40, 55), (0, TOOLBAR_HEIGHT - 1), (WIDTH, TOOLBAR_HEIGHT - 1), 1)

        for btn in self.buttons:
            btn.draw(surface)

        mode_text = font_small.render(f"Mode: {self.mode.upper()}", True, (120, 120, 140))
        surface.blit(mode_text, (300, 22))

        if self.running:
            status = font_small.render("RUNNING", True, (80, 200, 120))
        else:
            status = font_small.render("PAUSED", True, (255, 107, 107))
        surface.blit(status, (WIDTH - 300, 22))

        for rod in self.rods:
            x1 = int(rod.bob1.body.position.x)
            y1 = int(rod.bob1.body.position.y)
            x2 = int(rod.bob2.body.position.x)
            y2 = int(rod.bob2.body.position.y)
            pygame.draw.line(surface, ROD_COLOR, (x1, y1), (x2, y2), 3)

        if self.connecting_bob:
            mx, my = pygame.mouse.get_pos()
            x1 = int(self.connecting_bob.body.position.x)
            y1 = int(self.connecting_bob.body.position.y)
            pygame.draw.line(surface, (80, 80, 100), (x1, y1), (mx, my), 2)

        mx, my = pygame.mouse.get_pos()
        hovered_bob = self.get_bob_at(mx, my)

        for bob in self.bobs:
            x = int(bob.body.position.x)
            y = int(bob.body.position.y)
            
            if bob == self.dragging_bob or bob == self.connecting_bob:
                color = BOB_SELECTED
            elif bob == hovered_bob:
                color = BOB_HOVER
            else:
                color = BOB_COLOR

            pygame.draw.circle(surface, color, (x, y), bob.radius)
            
            if bob.pinned:
                pygame.draw.circle(surface, (255, 255, 255), (x, y), 4)

        help_text = font_small.render("SPACE: Start/Stop | DEL: Delete | ESC: Cancel", True, (80, 80, 100))
        surface.blit(help_text, (20, HEIGHT - 30))

def main():
    sim = Simulation()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            sim.handle_event(event)

        dt = clock.tick(60) / 1000.0
        sim.update(dt)
        sim.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
