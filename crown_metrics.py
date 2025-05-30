"""
crown_metrics.py
Author: Tim Whiteside
Requires: laspy, pandas, geopandas, numpy, alphashape, shapely, scipy, pyvista
"""

import laspy
import pandas as pd
import geopandas as gpd
import numpy as np
import alphashape
from shapely.geometry import MultiPoint
from scipy.spatial import distance
import pyvista as pv


def adaptive_alpha(coords_2d):
    """Compute alpha based on tree extent."""
    if len(points_2d) < 4:
        return 1.0
    mp = MultiPoint(coords_2d)
    width = mp.bounds[2] - mp.bounds[0]
    height = mp.bounds[3] - mp.bounds[1]
    return 0.075 * max(width, height)

def crown_volume_3d(coords_3d, alpha=2.0):
    """Use 3D alpha shape to calculate volume"""
    try:
        shape = alphashape.alphashape(coords_3d, alpha)
        mesh = pv.wrap(shape)
        return mesh.volume
    except Exception:
        return 0.0

def process_las_to_crowns(las_file, output_shp, crs_epsg=32633):
    # Read LAS file
    las = laspy.read(las_file)

    # Extract XYZ and Tree IDs
    try:
        #tree_ids = np.array(las['tree_id']) # Custom extra dimension with unique tree IDs
        tree_ids = las['final_segs']  # Custom extra dimension with unique tree IDs
    except KeyError:
        raise ValueError("LAS file must contain a tree_id attribute per point.")

    df = pd.DataFrame({
        'x': np.array(las.x),
        'y': np.array(las.y),
        'z': np.array(las.z),
        'tree_id': np.array(tree_ids)
    })

    crowns = []

    for tree_id, group in df.groupby('tree_id'):
        coords_2d = group[['x', 'y']].values
        coords_3d = group[['x', 'y', 'z']].values
        zs = group['z'].values
        if len(coords) < 3:
            continue
            
        alpha = adaptive_alpha(coords_2d)
        try:
            polygon = alphashape.alphashape(coords_2d, alpha)
        except:
            continue
        if not polygon or polygon.is_empty:
            continue

        # Remove/smooth sharp mouths etc using negative and positive buffers.
        #polygon = polygon.buffer(-0.5).buffer(0.5)
        polygon = polygon.simplify(0.2).buffer(0.1)

        # Calculate metrics
        # Crown area
        area = polygon.area
        # Max diameter = max distance between crown points
        max_diameter = np.max(distance.pdist(coords_2d)) if len(coords_2d) >= 2 else 0
        # Avg diameter from polygon
        bounds = polygon.bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        avg_diameter = (width + height) / 2
        # Tree height (absolute)
        tree_height = zs.max() - zs.min()
        # Crown depth: exclude base 5% of Z to avoid noise
        z_min = np.percentile(zs, 5)
        crown_depth = zs.max() - z_min
        # Crown volume 2d (simplified cone)
        crown_volume = (1/3) * area * crown_height
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
            'volume_2d_m3': round(crown_volume, 4),
            'volume_3d_m3': round(vol_3d, 4)
        })

    # Save list as Shapefile
    gdf = gpd.GeoDataFrame(crowns, crs=f"EPSG:{crs_epsg}")
    gdf.to_file(output_shp)
    print(f"✅ Crown polygons saved to {output_shp}")


# Run on .las/.laz file with defined CRS
process_las_to_crowns("input/with/treed_id.laz", "output/shapefile/with/metrics.shp", crs_epsg=32663)
