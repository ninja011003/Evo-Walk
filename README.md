# Human Locomotion

A 2D rigid body physics engine built from scratch in Python, designed as a foundation for neural network-based walking simulations.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.6+-green?logo=pygame&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## Features

- **Rigid Body Physics** — Circles (Bobs) and Rectangles (Boxes) with mass, velocity, and rotational dynamics
- **Constraint System** — Rod-based distance constraints connecting bodies
- **Collision Detection** — Full collision handling between all body types
- **Interactive UI** — Create, manipulate, and inspect physics objects in real-time
- **Debug Inspector** — Live property editing and monitoring panel
- **Force Application** — Apply directional forces at specific points on bodies

---

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/ninja011003/Evo-Walk.git
   cd Evo-Walk
   ```

2. **Install dependencies**

   Using uv (recommended):
   ```bash
   uv sync
   ```

   Or using pip:
   ```bash
   pip install pygame>=2.6.1
   ```

### Running the Simulation

```bash
# With uv
uv run python main.py

# Or directly
python main.py
```

---

## Controls

| Action | Control |
|--------|---------|
| **Start/Stop Simulation** | `SPACE` |
| **Toggle Debug Panel** | `D` |
| **Delete Object** | `DELETE` / `BACKSPACE` |
| **Cancel Action** | `ESC` |
| **Inspect Object** | `Right-Click` |
| **Drag Object** | `Left-Click + Drag` |

### Toolbar Modes

| Mode | Description |
|------|-------------|
| **Bob** | Create circular rigid bodies |
| **Box** | Create rectangular rigid bodies |
| **Rod** | Connect two bodies with a distance constraint |
| **Pin** | Toggle pinning (fix in place) for a body |
| **Force** | Apply directional force to a body |

---

## Project Structure

```
Evo-Walk/
├── main.py              # Application entry point
├── simulation.py        # Physics simulation engine & body definitions
├── vizualize.py         # Pygame-based UI and rendering
├── engine/
│   ├── templates/
│   │   ├── body.py              # Rigid body class
│   │   ├── vector.py            # 2D vector math utilities
│   │   ├── contraint.py         # Distance constraint solver
│   │   └── collision_handler.py # Collision detection & response
│   └── utils/
│       └── helper.py            # Utility functions
├── pyproject.toml       # Project configuration & dependencies
└── README.md
```

---

## Neural Network Walking Simulation

> **Work in Progress**
>
> A neural network-based walking agent is currently under development. The goal is to train an agent to learn bipedal locomotion using this physics engine as the simulation environment.

---

## License

This project is open source and available under the [MIT License](LICENSE).
