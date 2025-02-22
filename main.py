import numpy as np
import matplotlib.pyplot as plt
import random
from noise import pnoise2
import mplcursors

# Planet Settings
WIDTH, HEIGHT = 256, 128  
SCALE = 50.0  
OCTAVES = 6
PERSISTENCE = 0.5
LACUNARITY = 2.0

# Civilization Settings
NUM_CIVILIZATIONS = 5
CIV_GROWTH_RATE = 0.05  # Base growth rate
CIV_SPREAD_CHANCE = 0.2
TECH_GROWTH_RATE = 0.001
MAX_CIVILIZATIONS = 100
SLOW_GROWTH_THRESHOLD = 500  # Population threshold for slower growth
SLOW_GROWTH_RATE = 0.01  # Reduced growth rate after 500 citizens
MAX_POPULATION = 1000  # Maximum population cap

# Generate terrain
def generate_heightmap():
    heightmap = np.array([[pnoise2(x / SCALE, y / SCALE, octaves=OCTAVES, 
                                    persistence=PERSISTENCE, lacunarity=LACUNARITY, 
                                    repeatx=WIDTH, repeaty=HEIGHT, base=42) 
                           for x in range(WIDTH)] for y in range(HEIGHT)])
    return (heightmap - np.min(heightmap)) / (np.max(heightmap) - np.min(heightmap))

# Assign biomes
def generate_biome_map(heightmap):
    biome_map = np.zeros((HEIGHT, WIDTH, 3))
    colors = [(0, 0, 0.5), (0.9, 0.8, 0.5), (0.9, 0.7, 0.3), (0.1, 0.6, 0.2), (0.0, 0.4, 0.1)]
    thresholds = [0.3, 0.35, 0.7, 0.5]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            h = heightmap[y, x]
            # Find the appropriate biome color based on height thresholds
            biome_color = None
            for i, t in enumerate(thresholds):
                if h < t:
                    biome_color = colors[i]
                    break
            # If no condition is met, assign the last color (forest)
            if biome_color is None:
                biome_color = colors[-1]
            biome_map[y, x] = biome_color
    return biome_map

# Civilization generation
def generate_irregular_shape(center_x, center_y, size=10):
    return [(center_x + random.randint(-size, size), center_y + random.randint(-size, size)) for _ in range(size * 2)]

def initialize_civilizations(heightmap):
    civilizations = []
    colors = plt.get_cmap('tab10', NUM_CIVILIZATIONS)  # Assign unique colors
    for i in range(NUM_CIVILIZATIONS):
        while True:
            x, y = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1)
            # Ensure the civilization does not start in water (height < 0.3)
            if heightmap[y, x] >= 0.3:
                civilizations.append({
                    "center": (x, y), 
                    "population": 10, 
                    "tech": 1.0, 
                    "territory": generate_irregular_shape(x, y),
                    "color": colors(i)  # Assign a unique color
                })
                break
    return civilizations

# Simulation update
def update_civilizations(civilizations):
    for civ in civilizations:
        # Adjust growth rate based on population
        if civ["population"] > SLOW_GROWTH_THRESHOLD:
            growth_rate = SLOW_GROWTH_RATE  # Slower growth after 500 citizens
        else:
            growth_rate = CIV_GROWTH_RATE  # Normal growth rate
        
        # Additive growth to slow down population increase
        civ["population"] += civ["population"] * growth_rate
        
        # Cap population to prevent runaway growth
        if civ["population"] > MAX_POPULATION:
            civ["population"] = MAX_POPULATION

def draw_simulation(biome_map, civilizations, step):
    plt.clf()  # Clear the previous frame
    plt.imshow(biome_map)
    
    # Prepare scatter plot data
    x_coords = [civ["center"][0] for civ in civilizations]
    y_coords = [civ["center"][1] for civ in civilizations]
    colors = [civ["color"] for civ in civilizations]
    sizes = [civ["population"] / 2 for civ in civilizations]
    
    # Create the scatter plot
    scatter = plt.scatter(
        x_coords, y_coords,
        color=colors,
        s=sizes,
        alpha=0.7
    )
    
    # Add hover effect to display population
    cursor = mplcursors.cursor(scatter, hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(
        f"Population: {civilizations[sel.index]['population']:.0f}"
    ))
    
    # Display the current iteration (year)
    plt.title(f"Procedural Civilization Simulation - Year {step}")
    
    plt.pause(0.1)

def run_simulation():
    heightmap = generate_heightmap()
    biome_map = generate_biome_map(heightmap)
    civilizations = initialize_civilizations(heightmap)
    step = 0
    try:
        while step < 1000:  # Run for 1000 steps (years)
            update_civilizations(civilizations)
            draw_simulation(biome_map, civilizations, step)
            step += 1
    except KeyboardInterrupt:
        print("Simulation stopped by user.")

run_simulation()