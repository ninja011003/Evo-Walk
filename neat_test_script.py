import neat
import os
import sys
import select
import tty
import termios
import time
import pygame
import pickle
from human import Human
from neural_inputs import input_vec
import math

SIMULATION_STEPS = 100
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "neat_config.txt")
CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "best_genome.pkl")
ANGLE_RATE = 0.6

NUM_INPUTS = 24
NUM_OUTPUTS = 11

def check_key():
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None

def compute_activations(net, human):
    inputs = input_vec(human)
    outputs = net.activate(inputs)
    activations = [(outputs[i] + 1.0) / 2.0 for i in range(len(outputs))]
    return inputs, activations

def simulation_step(human, activations):
    human.set_activations(activations)
    human.step()

def eval_genome(genome, config):
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    human = Human(headless=True)
    human.start()

    torso = human.engine.boxes[1]
    prev_x = torso.body.position.x

    fitness = 0.0
    effort_penalty = 0.0

    for _ in range(SIMULATION_STEPS):
        inputs, activations = compute_activations(net, human)
        left_foot_contact = inputs[16]
        right_foot_contact = inputs[18]

        simulation_step(human, activations)

        y = torso.body.position.y
        torso_angle = torso.body.orientation

        if y > 750:
            return fitness - 500.0

        curr_x = torso.body.position.x
        dx = curr_x - prev_x
        prev_x = curr_x

        if y <= 550:
            fitness += 2.0
            fitness += dx * 100.0

            if -0.25 <= torso_angle <= 0.25:
                fitness += 10000.0

            if left_foot_contact > 0.0 and right_foot_contact > 0.0:
                fitness += 5.0
        else:
            fitness -= 20.0

        effort_penalty += sum(abs(a - 0.5) for a in activations)

    return fitness - 0.01 * effort_penalty


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
        
        inputs, activations = compute_activations(net, human)
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


def run(start_fresh=True):
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        CONFIG_PATH,
    )
    
    if start_fresh or not os.path.exists(CHECKPOINT_PATH):
        pop = neat.Population(config)
        generation = 0
    else:
        with open(CHECKPOINT_PATH, "rb") as f:
            checkpoint = pickle.load(f)
        pop = checkpoint["population"]
        generation = checkpoint["generation"]
        pop.reporters.reporters.clear()
        print(f"Resuming from generation {generation}")
    
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    
    best = None
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
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
    except KeyboardInterrupt:
        print("\nSaving checkpoint...")
        with open(CHECKPOINT_PATH, "wb") as f:
            pickle.dump({"population": pop, "generation": generation}, f)
        print(f"Checkpoint saved to {CHECKPOINT_PATH}")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    start_fresh = "--continue" not in sys.argv
    run(start_fresh=start_fresh)
