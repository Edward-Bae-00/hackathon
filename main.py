import numpy as np
import matplotlib.pyplot as plt
import random
import math
from noise import pnoise2
import mplcursors

# Planet Settings
WIDTH, HEIGHT = 256, 128  
SCALE = 50.0  
OCTAVES = 6
PERSISTENCE = 0.5
LACUNARITY = 2.0

# Civilization AI Settings
NUM_CIVILIZATIONS = 5
CIV_GROWTH_RATE = 0.02  
CIV_SPREAD_CHANCE = 0.2  
WAR_THRESHOLD = 0.3  # If two civs are too close, they may fight
TECH_GROWTH_RATE = 0.01  # Tech growth per year

# Orbital Mechanics
YEAR_LENGTH = 10  
AXIAL_TILT = 23.5  
ORBIT_SPEED = 2 * np.pi / YEAR_LENGTH  
ORBIT_ANGLE = 0  

# Generate terrain
def generate_heightmap():
    heightmap = np.zeros((HEIGHT, WIDTH))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            heightmap[y, x] = pnoise2(
                x / SCALE, y / SCALE,
                octaves=OCTAVES, persistence=PERSISTENCE,
                lacunarity=LACUNARITY, repeatx=WIDTH, repeaty=HEIGHT,
                base=42
            )
    return (heightmap - np.min(heightmap)) / (np.max(heightmap) - np.min(heightmap))

# Temperature map affected by orbit
def generate_temperature_map(heightmap, orbit_angle):
    temperature_map = np.zeros((HEIGHT, WIDTH))
    for y in range(HEIGHT):
        latitude_factor = 1 - abs((y / HEIGHT) - 0.5) * 2  
        seasonal_effect = math.cos(orbit_angle) * (AXIAL_TILT / 90)  
        temperature_map[y, :] = latitude_factor + seasonal_effect - (heightmap[y, :] * 0.3)
    return (temperature_map - np.min(temperature_map)) / (np.max(temperature_map) - np.min(temperature_map))

# Assign biomes based on height and temperature
def generate_biome_map(heightmap, temperature_map):
    biome_map = np.zeros((HEIGHT, WIDTH, 3))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            h, t = heightmap[y, x], temperature_map[y, x]
            if h < 0.3:  biome_map[y, x] = [0, 0, 0.5]  
            elif h < 0.35: biome_map[y, x] = [0.9, 0.8, 0.5]  
            elif t > 0.7:  biome_map[y, x] = [0.9, 0.7, 0.3]  
            elif t > 0.5:  biome_map[y, x] = [0.1, 0.6, 0.2]  
            elif t > 0.3:  biome_map[y, x] = [0.0, 0.4, 0.1]  
            else: biome_map[y, x] = [1, 1, 1]  
    return biome_map

# Initialize civilizations
def initialize_civilizations(heightmap):
    civilizations = []
    colors = plt.cm.get_cmap('tab10', NUM_CIVILIZATIONS)  # Assign unique colors
    for i in range(NUM_CIVILIZATIONS):
        while True:
            x, y = random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)
            if heightmap[y, x] > 0.35:  
                civilizations.append({
                    "x": x, 
                    "y": y, 
                    "population": 100, 
                    "tech": 1.0, 
                    "color": colors(i)  # Assign a unique color
                })
                break
    return civilizations

# Civilization AI: Expansion, Growth, War
def update_civilizations(civilizations, heightmap):
    for civ in civilizations:
        civ["population"] *= (1 + CIV_GROWTH_RATE)  
        civ["tech"] *= (1 + TECH_GROWTH_RATE)  

        if random.random() < CIV_SPREAD_CHANCE:
            best_tile = None
            best_score = -1
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                new_x, new_y = civ["x"] + dx, civ["y"] + dy
                if 0 <= new_x < WIDTH and 0 <= new_y < HEIGHT and heightmap[new_y, new_x] > 0.35:
                    score = heightmap[new_y, new_x] + random.uniform(0, 0.1)  
                    if score > best_score:
                        best_tile = (new_x, new_y)
                        best_score = score
            
            if best_tile:
                new_x, new_y = best_tile
                civilizations.append({
                    "x": new_x, 
                    "y": new_y, 
                    "population": civ["population"] * 0.5, 
                    "tech": civ["tech"], 
                    "color": civ["color"]  # Inherit the same color
                })
                civ["population"] *= 0.5  

    # Check for war
    for i, civ1 in enumerate(civilizations):
        for j, civ2 in enumerate(civilizations):
            if i != j:
                dist = math.sqrt((civ1["x"] - civ2["x"])**2 + (civ1["y"] - civ2["y"])**2)
                if dist < WAR_THRESHOLD:
                    if civ1["population"] * civ1["tech"] > civ2["population"] * civ2["tech"]:
                        civ1["population"] += civ2["population"] * 0.2  
                        civilizations.pop(j)  

# Draw simulation
def draw_simulation(biome_map, civilizations, step):
    plt.clf()
    plt.imshow(biome_map)
    
    # Prepare scatter plot data
    x_coords = []
    y_coords = []
    colors = []
    populations = []
    
    for civ in civilizations:
        # Add a dot for each citizen
        num_citizens = int(civ["population"] / 10)  # Scale down for visualization
        x_coords.extend([civ["x"] + random.uniform(-0.5, 0.5) for _ in range(num_citizens)])
        y_coords.extend([civ["y"] + random.uniform(-0.5, 0.5) for _ in range(num_citizens)])
        colors.extend([civ["color"]] * num_citizens)
        populations.extend([civ["population"]] * num_citizens)
    
    # Create the scatter plot
    scatter = plt.scatter(
        x_coords, y_coords,
        color=colors,
        s=5  # Size of each dot
    )
    
    plt.title(f"Procedural Civilization Simulation - Year {step}")
    
    # Add hover effect using mplcursors
    cursor = mplcursors.cursor(scatter, hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(
        f"Population: {populations[sel.index]:.0f}"  # Display population of the hovered civilization
    ))
    
    plt.pause(0.1)

# Main Simulation Loop
def run_simulation():
    global ORBIT_ANGLE
    heightmap = generate_heightmap()
    civilizations = initialize_civilizations(heightmap)

    step = 0
    while True:
        ORBIT_ANGLE = (ORBIT_ANGLE + ORBIT_SPEED) % (2 * np.pi)
        temperature_map = generate_temperature_map(heightmap, ORBIT_ANGLE)
        biome_map = generate_biome_map(heightmap, temperature_map)
        update_civilizations(civilizations, heightmap)
        draw_simulation(biome_map, civilizations, step)
        step += 1

# Run the simulation
run_simulation()