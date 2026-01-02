import neat
import os
import sys
import select
import tty
import termios
import time
import pygame
from human import Human
from neural_inputs import input_vec
import math

SIMULATION_STEPS = 500
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "neat_config.txt")
NORMAL_TORSO_BALANCE = 500.0

def check_key():
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None

def eval_genome(genome, config):
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    human = Human(headless=True)
    human.start()

    torso = human.engine.boxes[1]
    prev_x = torso.body.position.x

    forward_reward = 0.0
    effort_penalty = 0.0
    penalty = 0.0

    for _ in range(SIMULATION_STEPS):
        inputs = input_vec(human)
        outputs = net.activate(inputs)

        activations = [max(0.0, min(1.0, o)) for o in outputs]
        human.set_activations(activations)
        human.step()

        curr_x = torso.body.position.x
        forward_reward += curr_x - prev_x
        prev_x = curr_x

        if torso.body.position.y > 550.0:
            penalty -= 50

        effort_penalty += sum(abs(a) for a in activations)

    return forward_reward - 0.01 * effort_penalty + penalty




def eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        genome.fitness = eval_genome(genome, config)


def run_best_with_ui(genome, config):
    pygame.init()
    pygame.font.init()
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    human = Human(headless=False)
    human.start()
    initial_x = human.get_center_of_mass()[0]
    score_font = pygame.font.SysFont("SF Mono", 24, bold=True)
    running = True
    while running:
        dt = human.ui.tick()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            else:
                human.ui.handle_event(event)
        inputs = input_vec(human)
        outputs = net.activate(inputs)
        activations = [max(0.0, min(1.0, o)) for o in outputs]
        human.set_activations(activations)
        current_x = human.get_center_of_mass()[0]
        target_camera_x = current_x - human.width / 2
        human.ui.camera_x += (target_camera_x - human.ui.camera_x) * 0.1
        human.ui.update(dt)
        human.ui.draw(human.ui.screen)
        distance = current_x - initial_x
        score_text = f"Distance: {distance:.1f} px | Fitness: {genome.fitness:.1f}"
        score_surface = score_font.render(score_text, True, (80, 200, 120))
        score_bg = pygame.Surface(
            (score_surface.get_width() + 20, score_surface.get_height() + 10),
            pygame.SRCALPHA,
        )
        score_bg.fill((28, 28, 36, 220))
        human.ui.screen.blit(score_bg, (20, 70))
        human.ui.screen.blit(score_surface, (30, 75))
        pygame.display.flip()
    pygame.display.quit()


def run():
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        CONFIG_PATH,
    )
    pop = neat.Population(config)
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        generation = 0
        while True:
            best = pop.run(eval_genomes, 1)
            print(f"\nGeneration {generation} complete. Best fitness: {best.fitness:.2f}")
            print("Press 1 to view best genome with UI...")
            
            end_time = time.time() + 0.5
            show_ui = False
            while time.time() < end_time:
                key = check_key()
                if key == '1':
                    show_ui = True
                    break
                time.sleep(0.01)
            
            if show_ui:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                run_best_with_ui(best, config)
                tty.setcbreak(sys.stdin.fileno())
            
            generation += 1
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    run()

