import numpy as np
import matplotlib.pyplot as plt
from noise import pnoise2

# Planet settings
WIDTH, HEIGHT = 512, 256  # Map resolution
SCALE = 100.0  # Controls terrain roughness
OCTAVES = 6  # Number of noise layers
PERSISTENCE = 0.5  # Controls detail level
LACUNARITY = 2.0  # Controls how frequency increases per octave

# Generate Perlin Noise-based heightmap
def generate_heightmap():
    heightmap = np.zeros((HEIGHT, WIDTH))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            heightmap[y, x] = pnoise2(
                x / SCALE, y / SCALE,
                octaves=OCTAVES,
                persistence=PERSISTENCE,
                lacunarity=LACUNARITY,
                repeatx=WIDTH, repeaty=HEIGHT,
                base=42  # Random seed
            )
    return (heightmap - np.min(heightmap)) / (np.max(heightmap) - np.min(heightmap))  # Normalize

# Generate climate zones (temperature based on latitude)
def generate_temperature_map(heightmap):
    temperature_map = np.zeros((HEIGHT, WIDTH))
    for y in range(HEIGHT):
        latitude_factor = 1 - abs((y / HEIGHT) - 0.5) * 2  # Hotter at equator, colder at poles
        temperature_map[y, :] = latitude_factor - (heightmap[y, :] * 0.3)  # Higher = colder
    return (temperature_map - np.min(temperature_map)) / (np.max(temperature_map) - np.min(temperature_map))  # Normalize

# Assign biome colors based on height and temperature
def generate_biome_map(heightmap, temperature_map):
    biome_map = np.zeros((HEIGHT, WIDTH, 3))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            h = heightmap[y, x]
            t = temperature_map[y, x]

            if h < 0.3:  # Water
                biome_map[y, x] = [0, 0, 0.5]  # Deep Blue
            elif h < 0.35:  # Beach
                biome_map[y, x] = [0.9, 0.8, 0.5]  # Sand color
            elif t > 0.7:  # Desert
                biome_map[y, x] = [0.9, 0.7, 0.3]  # Sandy color
            elif t > 0.5:  # Grasslands
                biome_map[y, x] = [0.1, 0.6, 0.2]  # Green
            elif t > 0.3:  # Forest
                biome_map[y, x] = [0.0, 0.4, 0.1]  # Dark Green
            else:  # Snowy
                biome_map[y, x] = [1, 1, 1]  # White
    return biome_map

# Generate maps
heightmap = generate_heightmap()
temperature_map = generate_temperature_map(heightmap)
biome_map = generate_biome_map(heightmap, temperature_map)

# Display the generated planet map
plt.figure(figsize=(10, 5))
plt.imshow(biome_map)
plt.axis('off')
plt.title("Procedural Planet Generation")
plt.show()
