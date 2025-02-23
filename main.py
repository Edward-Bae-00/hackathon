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
NUM_CIVILIZATIONS = 8
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
                    "color": colors(i),  # Assign a unique color
                    "border_color": None
                })
                break
    return civilizations

def check_borders(civilizations):
    for i, civ1 in enumerate(civilizations):
        for j, civ2 in enumerate(civilizations):
            if i >= j:  # Avoid double-checking the same pair
                continue
            
            # Check if their territories are touching (simple border detection)
            for x1, y1 in civ1["territory"]:
                for x2, y2 in civ2["territory"]:
                    if abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1:  # Borders are close
                        # Mark the border red
                        civ1["border_color"] = "red"
                        civ2["border_color"] = "red"
                        
                        # Eventually, one civilization will win and merge with the other
                        if random.random() < 0.05: 
                            # Randomly choose a winner
                            winner = random.choice([civ1, civ2])
                            loser = civ2 if winner == civ1 else civ1
                            
                            # Merge territories and colors
                            winner["territory"].extend(loser["territory"])
                            loser["color"] = winner["color"]  # Winner takes the loser's land
                            #civilizations.remove(loser)  # Loser civilization is eliminated
                            break
                        
def create_meteor_strike(biome_map, year):
    # Every 30 years, there is a chance for a meteor strike
    if year % 30 == 0 and random.random() < 0.2:  # 20% chance
        # Random position and size for the meteor
        center_x = random.randint(0, WIDTH-1)
        center_y = random.randint(0, HEIGHT-1)
        radius = random.randint(5, 15)
        
        # Apply meteor effect: a large orange circular area
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if (x - center_x)**2 + (y - center_y)**2 <= radius**2:
                    biome_map[y, x] = (1.0, 0.5, 0)  # orange color

        # Fade meteor effect over time
        return center_x, center_y, radius  # Keep track of meteor position and size
    return None



# Simulation update
def update_civilizations(civilizations, biome_map, year):
    for civ in civilizations:
        # Adjust growth rate based on population
        if civ["population"] > SLOW_GROWTH_THRESHOLD:
            growth_rate = SLOW_GROWTH_RATE
        else:
            growth_rate = CIV_GROWTH_RATE
        
        civ["population"] += civ["population"] * growth_rate
        if civ["population"] > MAX_POPULATION:
            civ["population"] = MAX_POPULATION
    
    # Meteor strike effect every 30 years
    meteor = create_meteor_strike(biome_map, year)
    
    # Border conflict between civilizations
    check_borders(civilizations)

# Draw the simulation with meteor strike and border conflict
def draw_simulation(biome_map, civilizations, year):
    plt.clf()  # Clear previous frame
    plt.imshow(biome_map)
    
    # Draw civilization territories with red borders if there's a conflict
    for civ in civilizations:
        x_coords = [x for x, y in civ["territory"]]
        y_coords = [y for x, y in civ["territory"]]
        color = civ["color"] if civ["border_color"] != "red" else "red"
        plt.scatter(x_coords, y_coords, color=color, s=1, alpha=0.7)

    # Prepare scatter plot data for civilization centers
    x_coords = [civ["center"][0] for civ in civilizations]
    y_coords = [civ["center"][1] for civ in civilizations]
    colors = [civ["color"] for civ in civilizations]
    sizes = [civ["population"] / 2 for civ in civilizations]
    
    # Create scatter plot
    scatter = plt.scatter(x_coords, y_coords, color=colors, s=sizes, alpha=0.7)
    
    # Add hover effect to display population
    cursor = mplcursors.cursor(scatter, hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(f"Population: {civilizations[sel.index]['population']:.0f}"))
    
    # Display the current year
    plt.title(f"Procedural Civilization Simulation - Year {year}")
    
    plt.pause(0.1)

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