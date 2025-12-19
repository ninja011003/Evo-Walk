import pygame
import sys
from simulation import SimulationEngine
from vizualize import SimulationUI, WIDTH, HEIGHT

def main():
    engine = SimulationEngine(WIDTH, HEIGHT)
    ui = SimulationUI(engine)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            ui.handle_event(event)

        dt = ui.tick()
        ui.update(dt)
        ui.draw(ui.screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
