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
MAX_POPULATION = 10000  # Increased population cap
METEOR_REVERT_TIME = 20  # Time (in years) for meteor strike to revert
FIGHT_DISTANCE = 20  # Distance threshold for civilizations to fight
FIGHT_DAMAGE = 0.1  # Population reduction factor when civilizations fight
CITIZENS_PER_DOT = 10  # Each dot represents 100 citizens

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
                initial_population = 1000  # Start with 1000 citizens (10 dots)
                civilizations.append({
                    "center": (x, y), 
                    "population": initial_population,  # Start with floating-point population
                    "tech": 1.0, 
                    "territory": territory,
                    "dots": [(x, y) for _ in range(initial_population // CITIZENS_PER_DOT)],  # Initial dots
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

# Check Proximity and Fight
def check_proximity_and_fight(civilizations):
    for i, civ1 in enumerate(civilizations):
        for j, civ2 in enumerate(civilizations):
            if i >= j:
                continue
            # Calculate distance between centers
            x1, y1 = civ1["center"]
            x2, y2 = civ2["center"]
            distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
            if distance < FIGHT_DISTANCE:
                # Reduce population of both civilizations
                civ1["population"] *= (1 - FIGHT_DAMAGE)
                civ2["population"] *= (1 - FIGHT_DAMAGE)
                # Remove dots proportionally to population reduction
                civ1["dots"] = civ1["dots"][:int(civ1["population"] / CITIZENS_PER_DOT)]
                civ2["dots"] = civ2["dots"][:int(civ2["population"] / CITIZENS_PER_DOT)]
                print(f"Civilizations at {civ1['center']} and {civ2['center']} are fighting! Population reduced.")

# Apply Meteor Strike Effect
def create_meteor_strike(biome_map, civilizations, year):
    if year % 20 == 0 and random.random() < 0.3:  # Less frequent meteor strikes
        cx, cy, radius = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1), random.randint(5, 15)
        affected_area = []  # Store affected area for reversion
        for y in range(max(0, cy - radius), min(HEIGHT, cy + radius)):
            for x in range(max(0, cx - radius), min(WIDTH, cx + radius)):
                if (x - cx)**2 + (y - cy)**2 <= radius**2:
                    affected_area.append((x, y, biome_map[y, x].copy()))  # Save original biome
                    biome_map[y, x] = (1.0, 0.0, 0)  # Set to red color
                    # Check if any civilization's dots are hit
                    for civ in civilizations:
                        if (x, y) in civ["dots"]:
                            civ["population"] *= 0.5  # Reduce population by 50%
                            civ["dots"] = civ["dots"][:int(civ["population"] / CITIZENS_PER_DOT)]  # Remove hit dots
        print(f"Meteor strike at ({cx}, {cy}) in year {year}")  # Debug print
        return {"year": year, "center": (cx, cy), "radius": radius, "affected_area": affected_area}
    return None

# Revert Meteor Strike Area
def revert_meteor_strike(biome_map, meteor_strike, year):
    if meteor_strike and year - meteor_strike["year"] >= METEOR_REVERT_TIME:
        for x, y, original_biome in meteor_strike["affected_area"]:
            biome_map[y, x] = original_biome  # Revert to original biome
        print(f"Meteor strike at {meteor_strike['center']} reverted in year {year}")  # Debug print
        return None  # Clear the meteor strike
    return meteor_strike

# Update Simulation
def update_civilizations(civilizations, biome_map, year, meteor_strike):
    for civ in civilizations:
        # Determine growth rate based on population size
        growth_rate = SLOW_GROWTH_RATE if civ["population"] > SLOW_GROWTH_THRESHOLD else civ["growth_rate"]
        # Apply growth rate to population
        civ["population"] *= (1 + growth_rate)
        # Cap population at MAX_POPULATION
        civ["population"] = min(civ["population"], MAX_POPULATION)
        # Add new dots based on population growth
        target_dots = int(civ["population"] / CITIZENS_PER_DOT)
        while len(civ["dots"]) < target_dots:
            x, y = random.choice(civ["territory"])  # Add new dots within the territory
            civ["dots"].append((x, y))
        # Remove excess dots if population decreases
        civ["dots"] = civ["dots"][:target_dots]
        # Debug print to verify population growth
        print(f"Civilization at {civ['center']}: Population = {civ['population']:.2f}, Growth Rate = {growth_rate:.4f}")
    # Check for meteor strikes and resolve border conflicts
    meteor_strike = create_meteor_strike(biome_map, civilizations, year) or meteor_strike
    meteor_strike = revert_meteor_strike(biome_map, meteor_strike, year)
    check_borders(civilizations)
    check_proximity_and_fight(civilizations)  # Check for proximity and fight
    return meteor_strike

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
    plt.pause(0.01)  # Shorter pause to keep the simulation responsive

# Run Simulation
def run_simulation():
    heightmap = generate_heightmap()
    biome_map = generate_biome_map(heightmap)
    civilizations = initialize_civilizations(heightmap)
    year = 0
    meteor_strike = None  # Track active meteor strike
    try:
        while year < 1000:
            meteor_strike = update_civilizations(civilizations, biome_map, year, meteor_strike)
            draw_simulation(biome_map, civilizations, year)
            year += 1
    except KeyboardInterrupt:
        print("Simulation stopped by user.")

run_simulation()