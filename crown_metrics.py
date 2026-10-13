"""
crown_metrics.py
Derive a number of crown metrics from a point cloud with unique tree IDs
Author: Tim Whiteside
Requires: laspy, pandas, geopandas, numpy, alphashape, shapely, scipy, pyvista
"""
import os
from pathlib import Path
import re
import laspy
import pandas as pd
import geopandas as gpd
import numpy as np
import alphashape
from shapely.geometry import MultiPoint
from scipy.spatial import ConvexHull
from scipy.spatial import distance
import pyvista as pv
import logging

# Suppress internal alphashape warning when simplices are coplanar/collinear
class SingularMatrixFilter(logging.Filter):
    def filter(self, record):
        return "Singular matrix" not in record.getMessage()

logging.getLogger().addFilter(SingularMatrixFilter())


def adaptive_alpha(coords_2d):
    """Compute alpha based on tree extent."""
    if len(coords_2d) < 4:
        return 1.0
    mp = MultiPoint(coords_2d)
    width = mp.bounds[2] - mp.bounds[0]
    height = mp.bounds[3] - mp.bounds[1]
    return 0.075 * max(width, height)

def maximum_diameter(coords_2d):
    """ Calc max diameter using Convex Hull"""
    if len(coords_2d) >= 3:
        try:
            hull = ConvexHull(coords_2d)
            hull_points = coords_2d[hull.vertices]
            max_diameter = np.max(distance.cdist(hull_points, hull_points))
            return (max_diameter)
        except Exception as e:
            print(f"[WARN] Failed to compute max diameter ({e})")
            return(0.0)
    else:
        return(0.0)


def crown_volume_3d(coords_3d, alpha=2.0):
    """Use 3D alpha shape to calculate volume"""
    if len(coords_3d) < 4:
        return 0.0
    unique_3d = np.unique(coords_3d, axis=0)
    if len(unique_3d) < 4 or np.linalg.matrix_rank(unique_3d - unique_3d.mean(axis=0)) < 3:
        return 0.0
    try:
        shape = alphashape.alphashape(coords_3d, alpha)
        mesh = pv.wrap(shape)
        return mesh.volume
    except Exception:
        return 0.0


def process_las_to_crowns(plot_no,las_file,output_shp):
    #os.chdir(f'C:/lidar/Pine_creek/{plot_no}/align/treeiso')

    las_file = las_file
    #output_shp = f'metrics/{plot_no}_plot_metrics.shp'

    print(f'Processing Plot {plot_no}...')
    # Read LAS file
    las = laspy.read(las_file)

    # Extract XYZ and Tree IDs (either final_segs (treeiso) or treeID (lidR)
    try:
        if 'final_segs' in list(las.point_format.dimension_names):
            tree_ids = 'final_segs'  # Custom extra dimension with unique tree IDs
            print(f'TreeID ({tree_ids}) field exists!')
        elif 'treeID' in list(las.point_format.dimension_names):
            tree_ids = 'treeID'
            print(f'TreeID ({tree_ids}) field exists!')
        else:
            print('There is no treeID field in this point cloud. Please conduct an ITC detection.')
            exit()

    except KeyError:
        raise ValueError("LAS file must contain a tree_id attribute per point.")

    df = pd.DataFrame({
        'x': np.array(las.x),
        'y': np.array(las.y),
        'z': np.array(las.z),
        'tree_id': np.array(las[tree_ids])
    })

    # Filter out unassigned/background points (sentinel NA 1.79e308, NaN, <= 0)
    df = df[df['tree_id'].notna() & np.isfinite(df['tree_id']) & (df['tree_id'] > 0) & (df['tree_id'] < 1e9)]
    df['tree_id'] = df['tree_id'].astype(int)

    crowns = []

    for tree_id, group in df.groupby('tree_id'):
        coords_2d = group[['x', 'y']].values
        coords_3d = group[['x', 'y', 'z']].values
        zs = group['z'].values

        # Skip very small trees
        if len(coords_2d) < 3:
            print(f"[WARN] Skipping tree {tree_id}: not enough points ({len(coords_2d)})")
            continue

        # Check for unique and non-collinear points
        unique_2d = np.unique(coords_2d, axis=0)
        if len(unique_2d) < 3 or np.linalg.matrix_rank(unique_2d - unique_2d.mean(axis=0)) < 2:
            print(f"[WARN] Skipping tree {tree_id}: points are collinear or duplicate")
            continue

        alpha = adaptive_alpha(coords_2d)
        try:
            polygon = alphashape.alphashape(coords_2d, alpha)
        except Exception as e:
            print(f"[WARN] Skipping tree {tree_id}: alphashape failed ({e})")
            continue
        if not polygon or polygon.is_empty:
            print(f"[WARN] Skipping tree {tree_id}: empty polygon from alphashape")
            continue

        # Remove/smooth sharp mouths etc using negative and positive buffers.
        # polygon = polygon.buffer(-0.5).buffer(0.5)
        polygon = polygon.simplify(0.2).buffer(0.1)

        # Calculate metrics
        # Crown area
        area = polygon.area
        # Max diameter = max distance between crown points
        #max_diameter = np.max(distance.pdist(coords_2d)) if len(coords_2d) >= 2 else 0
        max_diameter = maximum_diameter(coords_2d)
        if max_diameter == 0:
            print(f"[WARN] Tree {tree_id}: failed to compute max diameter")

        # Avg diameter from polygon
        bounds = polygon.bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        avg_diameter = (width + height) / 2
        # Tree height (absolute)
        tree_height = zs.max() - zs.min()
        #tree_height = zs.max()
        #tree_ids = df["tree_id"].to_numpy()
        #z_vals = df["z"].to_numpy()
        #max_z = np.full(tree_ids.max() + 1, -np.inf)
        #np.maximum.at(max_z, tree_ids, z_vals)
        #tree_height = max_z[tree_ids]

        # Crown depth: exclude base 5% of Z to avoid noise
        z_min = np.percentile(zs, 5)
        crown_depth = zs.max() - z_min

        # Crown volume 2d (simplified cone)
        crown_volume = (1 / 3) * area * crown_depth
        # Optional 3D alpha shape volume
        vol_3d = crown_volume_3d(coords_3d, alpha=alpha)

        # Append to list
        crowns.append({
            'tree_id': int(tree_id),
            'geometry': polygon,
            'area_m2': round(area, 4),
            'max_diam_m': round(max_diameter, 4),
            'avg_diam_m': round(avg_diameter, 4),
            'tree_ht_m': round(tree_height, 4),
            'crown_ht_m': round(crown_depth, 4),
            'vol_2d_m3': round(crown_volume, 4),
            'vol_3d_m3': round(vol_3d, 4),
            'n_points': len(coords_2d)
        })

    if not crowns:
        print(f"[WARN] Plot {plot_no}: No valid tree crowns detected.")
        return

    # Save list as Shapefile
    crs_epsg = '7853'
    gdf = gpd.GeoDataFrame(crowns, crs=f"EPSG:{crs_epsg}")
    gdf.to_file(output_shp)
    print(f"[OK] Plot {plot_no} Crown polygons saved to {output_shp}")

if __name__ == "__main__":
    folder = Path(f'C:/lidar/treeID')
    extension = '.laz'
    metric_folder = folder / "metrics"
    metric_folder.mkdir(parents=True, exist_ok=True)

    for file in folder.glob(f'*{extension}'):
        filename = file.stem
        input_las = file
        output_shp = f"{filename}_metrics.shp"
        output_metric = metric_folder / output_shp
        process_las_to_crowns(grid_number, input_las, output_metric)

