from simulation import SimulationEngine, load_templates
from engine.templates.vector import Vector
import pygame
from vizualize import SimulationUI
import argparse
import math


class Human:
    DEFAULT_WIDTH = 1280
    DEFAULT_HEIGHT = 720

    def __init__(
        self, headless: bool = False, width: int = None, height: int = None, config_file: str = None
    ):
        self.headless = headless
        self.width = width or self.DEFAULT_WIDTH
        self.height = height or self.DEFAULT_HEIGHT
        self.config_file = config_file
        self.engine = SimulationEngine(self.width, self.height)
        self._load_bipedal()
        self.motors = self.engine.motors
        self.ui = None
        if not self.headless:
            self._init_ui()

    def _load_bipedal(self):
        import json
        import os
        
        if self.config_file:
            config_path = self.config_file
            if not os.path.isabs(config_path):
                config_path = os.path.join(os.path.dirname(__file__), config_path)
            with open(config_path, "r") as f:
                templates = json.load(f)
        else:
            templates = load_templates()
        
        if "FINAL" not in templates:
            raise ValueError(
                "template 'FINAL' not found in config file. "
            )
        template_data = templates["FINAL"]
        self.engine.load_template(template_data)

    def _init_ui(self):
        pygame.init()
        self.ui = SimulationUI(self.engine)

    def set_activations(self, activations: list) -> dict:
        num_motors = len(self.motors)
        if len(activations) != num_motors:
            raise ValueError(
                f"Expected {num_motors} activation values, got {len(activations)}. "
                "provide one activation value per motor."
            )

        for motor, activation in zip(self.motors, activations):
            clamped = max(0.0, min(1.0, float(activation)))
            target_angle = (clamped - 0.5) * 2 * math.pi
            motor.set_target_angle(target_angle)

        return {
            "x": self.get_center_of_mass()[0],
            "y": self.get_center_of_mass()[1],
            "target_angles": [m.target_angle for m in self.motors],
        }

    def get_center_of_mass(self) -> tuple:
        total_mass = 0.0
        weighted_x = 0.0
        weighted_y = 0.0

        for box in self.engine.boxes:
            if box == self.engine.ground:
                continue

            mass = box.body.mass
            if mass > 0:
                total_mass += mass
                weighted_x += box.body.position.x * mass
                weighted_y += box.body.position.y * mass

        if total_mass > 0:
            return (weighted_x / total_mass, weighted_y / total_mass)
        return (0.0, 0.0)

    def get_boxes_positions(self) -> list:
        positions = []
        for box in self.engine.boxes:
            if box == self.engine.ground:
                continue
            positions.append(
                {
                    "name": box.name,
                    "x": box.body.position.x,
                    "y": box.body.position.y,
                    "orientation": box.body.orientation,
                    "velocity_x": box.body.velocity.x,
                    "velocity_y": box.body.velocity.y,
                }
            )
        return positions

    def get_bobs_positions(self) -> list:
        positions = []
        for bob in self.engine.bobs:
            positions.append(
                {
                    "name": bob.name,
                    "x": bob.body.position.x,
                    "y": bob.body.position.y,
                    "velocity_x": bob.body.velocity.x,
                    "velocity_y": bob.body.velocity.y,
                }
            )
        return positions

    def step(self, dt: float = 1 / 60) -> dict:
        if not self.engine.running:
            self.engine.start()

        self.engine.update(dt)

        com = self.get_center_of_mass()
        return {
            "center_of_mass": {"x": com[0], "y": com[1]},
            "boxes": self.get_boxes_positions(),
            "bobs": self.get_bobs_positions(),
            "motor_target_angles": [m.target_angle for m in self.motors],
        }

    def reset(self):
        self.engine.clear()
        self._load_bipedal()
        self.motors = self.engine.motors

    def start(self):
        self.engine.start()

    def stop(self):
        self.engine.stop()

    def is_running(self) -> bool:
        return self.engine.running

    def run_with_ui(self):
        if self.headless:
            raise RuntimeError("mudiyadhuu podaaa")
        running = True
        frame = 0
        self.engine.start()

        initial_com_x = self.get_center_of_mass()[0]
        score_font = pygame.font.SysFont("SF Mono", 24, bold=True)
        num_motors = len(self.motors)

        while running:
            dt = self.ui.tick()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.ui.handle_event(event)

            if self.engine.running:
                phase = (frame % 60) / 60.0
                activations = []
                for i in range(num_motors):
                    if i % 2 == 0:
                        activations.append(0.8 if phase < 0.5 else 0.2)
                    else:
                        activations.append(0.2 if phase < 0.5 else 0.8)
                self.set_activations(activations)
                frame += 1

            current_com_x = self.get_center_of_mass()[0]
            target_camera_x = current_com_x - self.width / 2
            self.ui.camera_x += (target_camera_x - self.ui.camera_x) * 0.1

            self.ui.update(dt)
            self.ui.draw(self.ui.screen)

            distance_traveled = current_com_x - initial_com_x

            score_text = f"Distance: {distance_traveled:.1f} px"
            score_surface = score_font.render(score_text, True, (80, 200, 120))
            score_bg = pygame.Surface(
                (
                    score_surface.get_width() + 20,
                    score_surface.get_height() + 10,
                ),
                pygame.SRCALPHA,
            )
            score_bg.fill((28, 28, 36, 220))
            self.ui.screen.blit(score_bg, (20, 70))
            self.ui.screen.blit(score_surface, (30, 75))

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Human bipedal walker simulation"
    )
    parser.add_argument(
        "--headless", action="store_true", help="run in headless mode (no UI)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=100,
        help="number of simulation steps to run in headless mode",
    )
    args = parser.parse_args()

    if args.headless:
        print("headless mode...")
        human = Human(headless=True)
        human.start()
        num_motors = len(human.motors)

        for i in range(args.steps):
            phase = (i % 60) / 60.0
            activations = []
            for j in range(num_motors):
                if j % 2 == 0:
                    activations.append(0.8 if phase < 0.5 else 0.2)
                else:
                    activations.append(0.2 if phase < 0.5 else 0.8)

            human.set_activations(activations)
            state = human.step()

            if i % 10 == 0:
                com = state["center_of_mass"]
                print(f"Step {i}: CoM = ({com['x']:.2f}, {com['y']:.2f})")

        print("simulation complete")
    else:
        print("running with UI...")
        human = Human(headless=False)
        human.run_with_ui()
