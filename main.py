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
TECH_GROWTH_RATE = 0.01  # Tech growth per year
MIN_DISTANCE_BETWEEN_CIVS = 20  # Minimum distance between civilizations
MAX_CIVILIZATIONS = 100  # Maximum number of civilizations

# Orbital Mechanics
YEAR_LENGTH = 10  
AXIAL_TILT = 23.5  
ORBIT_SPEED = 2 * np.pi / YEAR_LENGTH  
ORBIT_ANGLE = 0  

# Biome favorability (higher values mean faster growth)
BIOME_FAVORABILITY = {
    (0, 0, 0.5): 0.5,  # Water (less favorable)
    (0.9, 0.8, 0.5): 0.8,  # Sand (moderately favorable)
    (0.9, 0.7, 0.3): 0.7,  # Desert (less favorable)
    (0.1, 0.6, 0.2): 1.2,  # Grassland (highly favorable)
    (0.0, 0.4, 0.1): 1.0,  # Forest (favorable)
    (1, 1, 1): 0.6  # Snow (less favorable)
}

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

# Check if a new civilization is too close to existing ones
def is_too_close(new_x, new_y, civilizations, min_distance):
    for civ in civilizations:
        dist = math.sqrt((civ["x"] - new_x)**2 + (civ["y"] - new_y)**2)
        if dist < min_distance:
            return True
    return False

# Initialize civilizations
def initialize_civilizations(heightmap):
    civilizations = []
    colors = plt.cm.get_cmap('tab10', NUM_CIVILIZATIONS)  # Assign unique colors
    for i in range(NUM_CIVILIZATIONS):
        while True:
            x, y = random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)
            if heightmap[y, x] > 0.35 and not is_too_close(x, y, civilizations, MIN_DISTANCE_BETWEEN_CIVS):  
                civilizations.append({
                    "x": x, 
                    "y": y, 
                    "population": 100, 
                    "tech": 1.0, 
                    "color": colors(i)  # Assign a unique color
                })
                break
    return civilizations

# Calculate growth factor based on surrounding biome colors
def calculate_growth_factor(civ, biome_map):
    x, y = int(civ["x"]), int(civ["y"])
    growth_factor = 0.0
    count = 0
    
    # Check a 5x5 grid around the civilization
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            nx, ny = x + dx, y + dy
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                biome_color = tuple(biome_map[ny, nx])
                growth_factor += BIOME_FAVORABILITY.get(biome_color, 0.5)  # Default to 0.5 if biome not found
                count += 1
    
    return growth_factor / count if count > 0 else 0.5

# Civilization AI: Expansion, Growth
def update_civilizations(civilizations, heightmap, biome_map):
    for civ in civilizations:
        # Calculate growth factor based on surrounding biome colors
        growth_factor = calculate_growth_factor(civ, biome_map)
        
        # Ensure population only grows
        civ["population"] *= (1 + CIV_GROWTH_RATE * growth_factor)  
        civ["tech"] *= (1 + TECH_GROWTH_RATE)  

        if random.random() < CIV_SPREAD_CHANCE and len(civilizations) < MAX_CIVILIZATIONS:
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
                if not is_too_close(new_x, new_y, civilizations, MIN_DISTANCE_BETWEEN_CIVS):
                    # Create a new civilization without reducing the original population
                    civilizations.append({
                        "x": new_x, 
                        "y": new_y, 
                        "population": 100,  # Start with a fixed population for new settlements
                        "tech": civ["tech"], 
                        "color": civ["color"]  # Inherit the same color
                    })

# Draw simulation
def draw_simulation(biome_map, civilizations, step, scatter=None, cursor=None):
    if scatter is None:
        # First frame: create the plot
        plt.clf()
        plt.imshow(biome_map)
        
        # Prepare scatter plot data
        x_coords = [civ["x"] for civ in civilizations]
        y_coords = [civ["y"] for civ in civilizations]
        colors = [civ["color"] for civ in civilizations]
        sizes = [civ["population"] / 10 for civ in civilizations]  # Scale size by population
        
        # Create the scatter plot
        scatter = plt.scatter(
            x_coords, y_coords,
            color=colors,
            s=sizes,  # Size of each dot
            alpha=0.7  # Semi-transparent dots
        )
        
        plt.title(f"Procedural Civilization Simulation - Year {step}")
        
        # Add hover effect using mplcursors
        cursor = mplcursors.cursor(scatter, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(
            f"Population: {civilizations[sel.index]['population']:.0f}"  # Display population of the hovered civilization
        ))
    else:
        # Update the scatter plot data
        x_coords = [civ["x"] for civ in civilizations]
        y_coords = [civ["y"] for civ in civilizations]
        sizes = [civ["population"] / 10 for civ in civilizations]
        
        # Update the scatter plot
        scatter.set_offsets(np.column_stack((x_coords, y_coords)))
        scatter.set_sizes(sizes)
        
        plt.title(f"Procedural Civilization Simulation - Year {step}")
    
    plt.pause(0.1)
    return scatter, cursor

# Main Simulation Loop
def run_simulation():
    global ORBIT_ANGLE
    heightmap = generate_heightmap()
    civilizations = initialize_civilizations(heightmap)

    step = 0
    scatter = None
    cursor = None
    while True:
        ORBIT_ANGLE = (ORBIT_ANGLE + ORBIT_SPEED) % (2 * np.pi)
        temperature_map = generate_temperature_map(heightmap, ORBIT_ANGLE)
        biome_map = generate_biome_map(heightmap, temperature_map)
        update_civilizations(civilizations, heightmap, biome_map)
        
        # Update the plot every year
        scatter, cursor = draw_simulation(biome_map, civilizations, step, scatter, cursor)
        
        step += 1

# Run the simulation
run_simulation()