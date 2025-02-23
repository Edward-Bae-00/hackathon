import numpy as np
import matplotlib.pyplot as plt
import random
from noise import pnoise2
import mplcursors
from scipy.spatial import ConvexHull

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
MAX_POPULATION = 10000000  # Increased population cap
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
    return [
        (max(0, min(WIDTH - 1, center_x + random.randint(-size, size))),
         max(0, min(HEIGHT - 1, center_y + random.randint(-size, size))))
        for _ in range(size * 2)
    ]

def initialize_civilizations(heightmap):
    civilizations = []
    colors = plt.get_cmap('tab10')
    valid_color_indices = [0, 1, 2, 4, 5, 6, 7, 8, 9]  # Skipping index 3 (Red)

    for i in range(NUM_CIVILIZATIONS):
        while True:
            x, y = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1)
            if heightmap[y, x] >= 0.3:
                territory = generate_irregular_shape(x, y)
                growth_rate = random.uniform(CIV_GROWTH_RATE_MIN, CIV_GROWTH_RATE_MAX)
                initial_population = 1000
                civ_color = colors(valid_color_indices[i % len(valid_color_indices)])[:3]  # Safe color selection
                # Use ConvexHull to represent the territory as a continuous shape
                hull = ConvexHull(territory)
                border_points = [territory[i] for i in hull.vertices]
                civilizations.append({
                    "center": (x, y), 
                    "population": initial_population,
                    "tech": 1.0, 
                    "territory": territory,
                    "border": border_points,  # Store border points for conflict detection
                    "color": civ_color,
                    "border_color": None,
                    "growth_rate": growth_rate
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
            # Check if any border points of civ1 are close to civ2's border
            if any(abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1 
                   for x1, y1 in civ1["border"] for x2, y2 in civ2["border"]):
                civ1["border_color"] = civ2["border_color"] = "red"
                if random.random() < 0.05:
                    winner, loser = (civ1, civ2) if random.random() < 0.5 else (civ2, civ1)
                    winner["territory"].extend(loser["territory"])
                    # Recompute the convex hull for the winner
                    winner_hull = ConvexHull(winner["territory"])
                    winner["border"] = [winner["territory"][i] for i in winner_hull.vertices]
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
                    # Check if any civilization's territory is hit
                    for civ in civilizations:
                        if any(abs(x - tx) <= 1 and abs(y - ty) <= 1 for tx, ty in civ["border"]):
                            civ["population"] *= 0.5  # Reduce population by 50%
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
def update_civilizations(civilizations, biome_map, heightmap, year, meteor_strike):
    for civ in civilizations:
        # Determine growth rate based on population size
        growth_rate = SLOW_GROWTH_RATE if civ["population"] > SLOW_GROWTH_THRESHOLD else civ["growth_rate"]
        # Apply growth rate to population
        civ["population"] *= (1 + growth_rate)
        # Cap population at MAX_POPULATION
        civ["population"] = min(civ["population"], MAX_POPULATION)

        # Expand territory based on population growth
        if civ["population"] > len(civ["territory"]) * CITIZENS_PER_DOT:
            # Add new points to the territory
            new_points = []
            for _ in range(int(civ["population"] // CITIZENS_PER_DOT - len(civ["territory"]))):
                x, y = random.choice(civ["territory"])
                dx, dy = random.randint(-1, 1), random.randint(-1, 1)
                new_x, new_y = max(0, min(WIDTH - 1, x + dx)), max(0, min(HEIGHT - 1, y + dy))
                if heightmap[new_y, new_x] >= 0.3:  # Ensure it's land
                    new_points.append((new_x, new_y))
            civ["territory"].extend(new_points)

            # Recompute the convex hull for the expanded territory
            if len(civ["territory"]) >= 3:  # ConvexHull requires at least 3 points
                hull = ConvexHull(civ["territory"])
                civ["border"] = [civ["territory"][i] for i in hull.vertices]

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
    for civ in civilizations:
        if len(civ["border"]) >= 3:  # Ensure there are enough points to draw a border
            # Draw the border of the civilization
            border_x, border_y = zip(*civ["border"])
            plt.plot(border_x + (border_x[0],), border_y + (border_y[0],), color=civ["color"], linewidth=2)
        # Display population as text at the center
        plt.text(civ["center"][0], civ["center"][1], f"Pop: {civ['population']:.0f}", 
                 color="white", fontsize=8, ha="center")
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
            meteor_strike = update_civilizations(civilizations, biome_map, heightmap, year, meteor_strike)
            draw_simulation(biome_map, civilizations, year)
            year += 1
    except KeyboardInterrupt:
        print("Simulation stopped by user.")

run_simulation()