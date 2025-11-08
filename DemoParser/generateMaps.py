import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv

def extract_coordinates(df):
    return df[
        (df['is_alive'] == True)
        & (df['is_airborne'] == False)
        & (df['X'].notna()) & (df['Y'].notna()) & (df['Z'].notna())
    ][['steamid', 'X', 'Y', 'Z']]

def draw_coordinates(positions):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(positions['X'], positions['Y'], positions['Z'], s=1, alpha=0.1)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    # --- Equal aspect ratio across all axes ---
    x_limits = [positions['X'].min(), positions['X'].max()]
    y_limits = [positions['Y'].min(), positions['Y'].max()]
    z_limits = [positions['Z'].min(), positions['Z'].max()]

    max_range = np.array([
        x_limits[1] - x_limits[0],
        y_limits[1] - y_limits[0],
        z_limits[1] - z_limits[0]
    ]).max() / 2.0

    mid_x = np.mean(x_limits)
    mid_y = np.mean(y_limits)
    mid_z = np.mean(z_limits)

    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    plt.show()

def generate_map_surface(positions, downsample=5, alpha_value=50, floor_height=150):
    # Downsample positions
    positions = positions.iloc[::downsample, :].copy()

    # Identify "floors" based on Z levels
    z_min, z_max = positions['Z'].min(), positions['Z'].max()
    z_levels = np.arange(z_min, z_max, floor_height)

    surfaces = []
    for i, level in enumerate(z_levels):
        floor_slice = positions[
            (positions['Z'] > level) & (positions['Z'] <= level + floor_height)
        ]
        if len(floor_slice) < 100:
            continue  # skip empty slices

        points = floor_slice[['X', 'Y', 'Z']].to_numpy(dtype=np.float32)
        cloud = pv.PolyData(points)
        try:
            surface = cloud.delaunay_2d(alpha=alpha_value)
            surfaces.append(surface)
        except:
            pass  # skip if surface fails (e.g., too few points)
    
    return surfaces

def draw_map_surface(surfaces):
    plotter = pv.Plotter()
    colours = ["darkgray", "lightblue", "lightgreen", "lightcoral", "khaki"]

    for i, surface in enumerate(surfaces):
        try:
            colour = colours[i % len(colours)]
            plotter.add_mesh(surface, color=colour, opacity=0.8)
        except:
            pass  # skip if surface fails
        
    plotter.show_grid()
    plotter.set_background("lightgray")
    plotter.show(title="Map Floors View")


def save_map_mesh(surfaces):
    combined_surface = surfaces[0]
    for s in surfaces[1:]:
        combined_surface = combined_surface.merge(s)
        combined_surface.save(surfaceMeshPath := "map_surface.vtk")