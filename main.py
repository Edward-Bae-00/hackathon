import numpy as np
import matplotlib.pyplot as plt
import random
from noise import pnoise2
import mplcursors

# Constants
WIDTH, HEIGHT = 256, 128
SCALE = 50.0
OCTAVES = 6
PERSISTENCE = 0.5
LACUNARITY = 2.0

NUM_CIVILIZATIONS = 8
CIV_GROWTH_RATE_MIN = 0.03  # Minimum growth rate
CIV_GROWTH_RATE_MAX = 0.07  # Maximum growth rate
CIV_SPREAD_CHANCE = 0.2
TECH_GROWTH_RATE = 0.001
MAX_CIVILIZATIONS = 100
SLOW_GROWTH_THRESHOLD = 500  # Population threshold for slower growth
SLOW_GROWTH_RATE = 0.02  # Slower growth rate for large populations
MAX_POPULATION = 5000  # Maximum population cap

# Generate Terrain
def generate_heightmap():
    heightmap = np.array([[pnoise2(x / SCALE, y / SCALE, octaves=OCTAVES, 
                                    persistence=PERSISTENCE, lacunarity=LACUNARITY, 
                                    repeatx=WIDTH, repeaty=HEIGHT, base=42) 
                           for x in range(WIDTH)] for y in range(HEIGHT)])
    return (heightmap - np.min(heightmap)) / (np.max(heightmap) - np.min(heightmap))

# Generate Biome Map
def generate_biome_map(heightmap):
    biome_map = np.zeros((HEIGHT, WIDTH, 3))
    colors = [(0, 0, 0.5), (0.9, 0.8, 0.5), (0.9, 0.7, 0.3), (0.1, 0.6, 0.2), (0.0, 0.4, 0.1)]
    thresholds = [0.3, 0.35, 0.7, 0.5]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            h = heightmap[y, x]
            for i, t in enumerate(thresholds):
                if h < t:
                    biome_map[y, x] = colors[i]
                    break
            else:
                biome_map[y, x] = colors[-1]
    return biome_map

# Initialize Civilizations
def generate_irregular_shape(center_x, center_y, size=10):
    return [(center_x + random.randint(-size, size), center_y + random.randint(-size, size)) for _ in range(size * 2)]

def initialize_civilizations(heightmap):
    civilizations = []
    colors = plt.get_cmap('tab10')
    for i in range(NUM_CIVILIZATIONS):
        while True:
            x, y = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1)
            if heightmap[y, x] >= 0.3:
                territory = generate_irregular_shape(x, y)
                growth_rate = random.uniform(CIV_GROWTH_RATE_MIN, CIV_GROWTH_RATE_MAX)  # Unique growth rate
                civilizations.append({
                    "center": (x, y), 
                    "population": 10.0,  # Start with floating-point population
                    "tech": 1.0, 
                    "territory": territory,
                    "dots": [(x, y) for _ in range(10)],  # Initial dots
                    "color": colors(i)[:3],
                    "border_color": None,
                    "growth_rate": growth_rate  # Unique growth rate for each civilization
                })
                break
    return civilizations

# Check Borders and Resolve Conflicts
def check_borders(civilizations):
    to_remove = []
    for i, civ1 in enumerate(civilizations):
        for j, civ2 in enumerate(civilizations):
            if i >= j:
                continue
            if any(abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1 
                   for x1, y1 in civ1["territory"] for x2, y2 in civ2["territory"]):
                civ1["border_color"] = civ2["border_color"] = "red"
                if random.random() < 0.05:
                    winner, loser = (civ1, civ2) if random.random() < 0.5 else (civ2, civ1)
                    winner["territory"].extend(loser["territory"])
                    winner["dots"].extend(loser["dots"])  # Transfer dots from loser to winner
                    to_remove.append(loser)
    for civ in to_remove:
        civilizations.remove(civ)

# Apply Meteor Strike Effect
def create_meteor_strike(biome_map, year):
    if year % 10 == 0 and random.random() < 0.5:  # More frequent meteor strikes
        cx, cy, radius = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1), random.randint(5, 15)
        for y in range(max(0, cy - radius), min(HEIGHT, cy + radius)):
            for x in range(max(0, cx - radius), min(WIDTH, cx + radius)):
                if (x - cx)**2 + (y - cy)**2 <= radius**2:
                    biome_map[y, x] = (1.0, 0.0, 0)  # Set to red color
        print(f"Meteor strike at ({cx}, {cy}) in year {year}")  # Debug print
        return cx, cy, radius
    return None

# Update Simulation
def update_civilizations(civilizations, biome_map, year):
    for civ in civilizations:
        # Determine growth rate based on population size
        growth_rate = SLOW_GROWTH_RATE if civ["population"] > SLOW_GROWTH_THRESHOLD else civ["growth_rate"]
        # Apply growth rate to population
        civ["population"] *= (1 + growth_rate)
        # Cap population at MAX_POPULATION
        civ["population"] = min(civ["population"], MAX_POPULATION)
        # Add new dots based on population growth
        new_dots = int(civ["population"] - len(civ["dots"]))  # Number of new dots to add
        for _ in range(new_dots):
            x, y = random.choice(civ["territory"])  # Add new dots within the territory
            civ["dots"].append((x, y))
        # Debug print to verify population growth
        print(f"Civilization at {civ['center']}: Population = {civ['population']:.2f}, Growth Rate = {growth_rate:.4f}")
    # Check for meteor strikes and resolve border conflicts
    create_meteor_strike(biome_map, year)
    check_borders(civilizations)

# Draw Simulation
def draw_simulation(biome_map, civilizations, year):
    plt.clf()
    plt.imshow(biome_map)
    scatter_objects = []  # Store scatter objects for hover functionality
    for civ in civilizations:
        # Draw all dots for the civilization
        x_coords, y_coords = zip(*civ["dots"])
        scatter = plt.scatter(x_coords, y_coords, color=civ["color"], s=5, alpha=0.7)  # Smaller dots
        scatter_objects.append((scatter, civ))  # Store scatter object and civilization data
    # Add hover functionality to display population
    for scatter, civ in scatter_objects:
        cursor = mplcursors.cursor(scatter, hover=True)
        cursor.connect("add", lambda sel, civ=civ: sel.annotation.set_text(f"Pop: {civ['population']:.0f}"))
    plt.title(f"Procedural Civilization Simulation - Year {year}")
    plt.pause(0.1)

# Run Simulation
def run_simulation():
    heightmap = generate_heightmap()
    biome_map = generate_biome_map(heightmap)
    civilizations = initialize_civilizations(heightmap)
    year = 0
    try:
        while year < 1000:
            update_civilizations(civilizations, biome_map, year)
            draw_simulation(biome_map, civilizations, year)
            year += 1
    except KeyboardInterrupt:
        print("Simulation stopped by user.")

run_simulation()