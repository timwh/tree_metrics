import os
import laspy
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point


def clip_las_by_polygon(las_file, shp_file, plot_num, output_file, crs_epsg=32633,min_fraction=0.5):
    """
    Function to clip las/laz file with tree ids to a plot, includes all trees that intersect with
    plot boundary by at least the minimum fraction
    :param las_file: las/laz file to clip
    :param shp_file: shapefile of plot polygons
    :param plot_num: plot number in the shapefile
    :param output_file: clipped las/laz file
    :param crs_epsg: CRS for files
    :param min_fraction: minimum fraction of tree that intersects with plot boundary
    :return:
    """
    # --- Read LAS ---
    las = laspy.read(las_file)

    # Ensure treeID field exists
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

    # Build dataframe of points
    df = pd.DataFrame({
        "x": np.array(las.x),
        "y": np.array(las.y),
        "z": np.array(las.z),
        "tree_id": np.array(las[tree_ids])
    })

    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.x, df.y), crs=f"EPSG:{crs_epsg}")

    # --- Read polygon ---
    bb_clip = gpd.read_file(shp_file).to_crs(gdf.crs)
    bb_clip = bb_clip[bb_clip['Plot'] == plot_num]

    # Find trees whose points intersect the polygon (touch or inside)
    merged = bb_clip.union_all() if hasattr(bb_clip, "union_all") else bb_clip.unary_union

    # Check which points are inside
    gdf["inside"] = gdf.within(merged)

    # Compute fraction of inside points per tree
    fractions = gdf.groupby("tree_id")["inside"].mean()

    # Select trees with majority of points inside
    keep_tree_ids = fractions[fractions > min_fraction].index.values
    # Filter LAS by those treeIDs
    mask = np.isin(las[tree_ids], keep_tree_ids)
    clipped_las = laspy.create(point_format=las.header.point_format, file_version=las.header.version)

    # Copy coordinates
    clipped_las.x = las.x[mask]
    clipped_las.y = las.y[mask]
    clipped_las.z = las.z[mask]

    # Copy other attributes
    for dim in las.point_format.dimension_names:
        if dim not in {"x", "y", "z"}:
            clipped_las[dim] = las[dim][mask]

    # Write to new LAS file
    clipped_las.write(output_file)
    print(f"✅ Saved clipped LAS with intersecting trees to {output_file}")


# Run function
plot_no = "Plot1"
wkg_dir = f"C:/lidar/folder/{plot_no}/trees"  # Working directory
input_las = os.path.join(wkg_dir, f'{plot_no}_treeids.laz')  # las/laz file with tree IDs
shpfile = "C:/lidar/shp2/Plot_polys.shp"  # shapefile of plot boundaries
outfile = os.path.join(wkg_dir, f"{plot_no}_clipped_plot.laz")  # output clipped las file
clip_las_by_polygon(
    las_file=input_las,
    shp_file=shpfile,
    plot_num=plot_no,
    output_file=outfile,
    crs_epsg=62332,
    min_fraction=0.5
)
