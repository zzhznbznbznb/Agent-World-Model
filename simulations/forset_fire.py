import io
import random

import numpy as np
from matplotlib import pyplot as plt
from mesa import Model
from mesa.space import MultiGrid


class ForestFireAdapter:
    def __init__(self, width=20, height=20, density=0.65, steps=20, seed=None, wind_direction="none"):
        self.width = width
        self.height = height
        self.density = density
        self.steps = steps
        self.wind_direction = wind_direction
        self.seed = seed if seed is not None else random.randint(0, 10**9)
        self.cleared_cells = set()
        self.history = []
        self.model = None
        self._create_model()

    def _create_model(self):
        rng = random.Random(self.seed)

        class ForestFireModel(Model):
            def __init__(self, width, height, density, wind_direction):
                super().__init__()
                self.width = width
                self.height = height
                self.grid = MultiGrid(width, height, torus=False)
                self.density = density
                self.wind_direction = wind_direction
                self.rng = rng

                for x in range(width):
                    for y in range(height):
                        if self.rng.random() < density:
                            self.grid[x][y] = 1
                        else:
                            self.grid[x][y] = 0

                cx, cy = width // 2, height // 2
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        x = cx + dx
                        y = cy + dy
                        if 0 <= x < width and 0 <= y < height and self.grid[x][y] == 1:
                            self.grid[x][y] = 2

                for _ in range(max(2, width // 8)):
                    x = self.rng.randint(0, width - 1)
                    y = self.rng.randint(0, height - 1)
                    if self.grid[x][y] == 1:
                        self.grid[x][y] = 2

            def step(self):
                new_grid = np.zeros((self.height, self.width), dtype=int)
                burning_found = False

                for x in range(self.width):
                    for y in range(self.height):
                        state = self.grid[x][y]
                        if state == 2:
                            new_grid[y, x] = 2 if self.rng.random() < 0.8 else 0
                            burning_found = True
                        elif state == 1:
                            neighbors = self.grid.get_neighborhood((x, y), moore=True, include_center=False)
                            burning_neighbors = [
                                (nx, ny) for nx, ny in neighbors if self.grid[nx][ny] == 2
                            ]
                            if burning_neighbors:
                                downwind_burning = any(
                                    (self.wind_direction == "east" and nx < x)
                                    or (self.wind_direction == "west" and nx > x)
                                    or (self.wind_direction == "north" and ny > y)
                                    or (self.wind_direction == "south" and ny < y)
                                    for nx, ny in burning_neighbors
                                )
                                ignition_chance = 0.95 if downwind_burning else 0.45
                                if self.rng.random() >= ignition_chance:
                                    new_grid[y, x] = 1
                                    continue
                                new_grid[y, x] = 2
                                burning_found = True
                            else:
                                new_grid[y, x] = 1
                        else:
                            new_grid[y, x] = 0

                if burning_found:
                    for _ in range(4):
                        x = self.rng.randint(0, self.width - 1)
                        y = self.rng.randint(0, self.height - 1)
                        if self.grid[x][y] == 1:
                            new_grid[y, x] = 2

                for x in range(self.width):
                    for y in range(self.height):
                        self.grid[x][y] = new_grid[y, x]

            def render(self):
                arr = np.zeros((self.height, self.width), dtype=int)
                for x in range(self.width):
                    for y in range(self.height):
                        arr[y, x] = self.grid[x][y]

                if not np.any(arr == 2):
                    cx = self.width // 2
                    cy = self.height // 2
                    for dx in range(-3, 4):
                        for dy in range(-3, 4):
                            x = cx + dx
                            y = cy + dy
                            if 0 <= x < self.width and 0 <= y < self.height and arr[y, x] == 1:
                                arr[y, x] = 2

                base_size = max(4.5, min(11.0, max(self.width, self.height) * 0.6))
                fig, ax = plt.subplots(figsize=(base_size, base_size), dpi=120)
                cmap = plt.cm.colors.ListedColormap([
                    "#e5e7eb",
                    "#2e7d32",
                    "#ef4444",
                ])
                ax.imshow(arr, cmap=cmap, vmin=0, vmax=2)
                ax.set_axis_off()
                ax.set_title("Forest Fire Simulation")
                return fig

        self.model = ForestFireModel(
            self.width,
            self.height,
            self.density,
            self.wind_direction,
        )

    def reset(self, seed=None):
        if seed is not None:
            self.seed = seed
        self.history.clear()
        self.model = None
        self._create_model()

    def _save_snapshot(self):
        grid = [
            [self.model.grid[x][y] for y in range(self.height)]
            for x in range(self.width)
        ]
        self.history.append({
            "grid": grid,
            "random_state": self.model.rng.getstate(),
            "cleared_cells": self.cleared_cells.copy(),
            "density": self.density,
            "steps": self.steps,
            "wind_direction": self.wind_direction,
        })

    def rewind(self, steps):
        steps = max(0, int(steps))
        if steps == 0 or steps > len(self.history):
            return False

        snapshot = self.history[-steps]
        for x in range(self.width):
            for y in range(self.height):
                self.model.grid[x][y] = snapshot["grid"][x][y]
        self.model.rng.setstate(snapshot["random_state"])
        self.cleared_cells = snapshot["cleared_cells"].copy()
        self.density = snapshot["density"]
        self.steps = snapshot["steps"]
        self.wind_direction = snapshot["wind_direction"]
        del self.history[-steps:]
        return True

    def apply_config(self, width, height, density, steps, wind_direction=None):
        dimensions_changed = width != self.width or height != self.height
        density_changed = density != self.density

        if dimensions_changed:
            self.width = width
            self.height = height
            self.density = density
            self.steps = steps
            if wind_direction is not None:
                self.wind_direction = wind_direction
            self.cleared_cells.clear()
            self.reset()
            return

        if density_changed:
            self._apply_density(density)

        self.density = density
        self.steps = steps
        if wind_direction is not None:
            self.wind_direction = wind_direction
            self.model.wind_direction = wind_direction

    def clear_area(self, location):
        if location != "bottom_right":
            return False

        start_x = self.width * 2 // 3
        start_y = self.height * 2 // 3
        for x in range(start_x, self.width):
            for y in range(start_y, self.height):
                self.cleared_cells.add((x, y))
                self.model.grid[x][y] = 0
        return True

    def _apply_density(self, density):
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) in self.cleared_cells:
                    self.model.grid[x][y] = 0
                    continue
                if self.model.grid[x][y] == 2:
                    continue

                value = ((x * 73856093) ^ (y * 19349663) ^ self.seed) % 1000 / 1000
                self.model.grid[x][y] = 1 if value < density else 0

    def run(self):
        if self.model is None:
            self._create_model()

        for _ in range(self.steps):
            self._save_snapshot()
            self.model.step()

        return self.model.render()

    def render_png(self, advance=True):
        fig = self.run() if advance else self.model.render()
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=120, bbox_inches="tight", pad_inches=0.08)
        plt.close(fig)
        return buffer.getvalue()
