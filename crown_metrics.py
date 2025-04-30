import laspy
import pandas as pd
import geopandas as gpd
import numpy as np
import alphashape
from shapely.geometry import MultiPoint
from shapely.ops import unary_union
from scipy.spatial import distance


def adaptive_alpha(points_2d):
    """Compute alpha based on tree extent."""
    if len(points_2d) < 4:
        return 1.0
    mp = MultiPoint(points_2d)
    width = mp.bounds[2] - mp.bounds[0]
    height = mp.bounds[3] - mp.bounds[1]
    return 0.075 * max(width, height)


def extract_tree_crowns_from_las(las_file, output_shp, crs_epsg=32633):
    # Read LAS file
    las = laspy.read(las_file)

    # Extract XYZ and Tree IDs
    try:
        tree_ids = las['final_segs']  # Custom extra dimension
    except KeyError:
        tree_ids = las.classification  # Use classification if tree_id not found

    df = pd.DataFrame({
        'x': np.array(las.x),
        'y': np.array(las.y),
        'z': np.array(las.z),
        'tree_id': np.array(tree_ids)
    })

    crowns = []

    for tree_id, group in df.groupby('tree_id'):
        coords = group[['x', 'y']].values
        zs = group['z'].values
        if len(coords) >= 3:
            alpha = adaptive_alpha(coords)
            polygon = alphashape.alphashape(coords, alpha)
            if polygon and not polygon.is_empty:
                # Remove/smooth sharp mouths etc using negative and positive buffers.
                polygon = polygon.buffer(-0.5).buffer(0.5)
                # Crown area
                area = polygon.area
                # Max diameter = max distance between crown points
                max_diameter = 0
                if len(coords) >= 2:
                    max_diameter = np.max(distance.pdist(coords))
                # Avg diameter from polygon
                bounds = polygon.bounds
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                avg_diameter = (width + height) / 2
                # Tree height (absolute)
                tree_height = zs.max() - zs.min()
                # Crown height: exclude base 5% of Z to avoid noise
                z_min = np.percentile(zs, 5)
                z_max = zs.max()
                crown_height = z_max - z_min
                # Crown volume (simplified cone)
                crown_volume = (1 / 3) * area * crown_height

                # Append to list
                crowns.append({'tree_id': int(tree_id),
                               'geometry': polygon,
                               'area_m2': area,
                               'max_diam_m': max_diameter,
                               'avg_diam_m': avg_diameter,
                               'tree_ht_m': tree_height,
                               'crown_ht_m': crown_height,
                               'crown_vol_m3': crown_volume
                })

    # Save list as Shapefile
    gdf = gpd.GeoDataFrame(crowns, crs=f"EPSG:{crs_epsg}")
    gdf.to_file(output_shp)
    print(f"✅ Crown polygons saved to {output_shp}")


# Run this on your .las/.laz file with your CRS
extract_tree_crowns_from_las("input/with/treed_id.laz", "output/shapefile/with/metrics.shp", crs_epsg=32663)
