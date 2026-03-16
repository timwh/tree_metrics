"""
Show trees by height in 3D point cloud plot using open3D
Author: Tim Whiteside
Requires: laspy, numpy, pandas, os, open3d, matplotlib
"""

import laspy as lp
import numpy as np
import pandas as pd
import os
import open3d as o3d
from matplotlib.colors import to_rgb


def class_tree_height(lasfile, classtype):
    """
    Function to classify and 3D plot an ITC point cloud based on tree height
    @param: lasfile: point cloud with tree IDs
    @param: classtype: class grouping (Werner or arbitrary (2m spacings)
    """
    # Read in las
    las = lp.read(lasfile)

    # Ensure treeID field exists
    if 'final_segs' in list(las.point_format.dimension_names):
        id_field = 'final_segs'  # Custom extra dimension with unique tree IDs
        print(f'TreeID ({id_field}) field exists!')
    elif 'treeID' in list(las.point_format.dimension_names):
        id_field = 'treeID'
        print(f'TreeID ({id_field}) field exists!')
    else:
        raise ValueError("LAS file must contain a tree id field.")

    # Create xyz df with tree ID
    df = pd.DataFrame({
        'x': np.array(las.x),
        'y': np.array(las.y),
        'z': np.array(las.z),
        'tree_id': np.array(las[id_field])
    })
    # Extract arrays from las
    x = las.x
    y = las.y
    z = las.z
    tree_ids = np.array(las[id_field]).astype(int)

    points = np.vstack((x, y, z)).T

    # Assign the tree height (max_z) to each point based on tree ID
    #tree_ids = df["tree_id"].to_numpy()
    #z_vals = df["z"].to_numpy()
    #max_z = np.full(tree_ids.max() + 1, -np.inf)
    #np.maximum.at(max_z, tree_ids, z_vals)
    #df["max_z"] = max_z[tree_ids]

    print("Getting tree heights...")

    unique_ids, inverse = np.unique(tree_ids, return_inverse=True)

    max_z = np.full(unique_ids.size, -np.inf)
    np.maximum.at(max_z, inverse, z)

    point_max_z = max_z[inverse]

    # Classify into height classes
    htype = classtype

    # Assign bins by selected height class type
    if htype == "Arbitrary":  # bins 2 metres apart
        bins = [2, 4, 6, 8, 10, 12, 14, 16, np.inf]
        bin_names = ["2-4m", "4-6m", "6-8m", "8-10m", "10-12m", "12-14m", "14-16m", "16m+"]
        bin_colours = {
            "2-4m": "#0000FF",  # hex colours
            "4-6m": "#0077F6",
            "6-8m": "#00EEEE",
            "8-10m": "#7FF676",
            "10-12m": "#FFFF00",
            "12-14m": "#FF7F00",
            "14-16m": "#FF0000",
            "16m+": "AA0000"
        }
    elif htype == "Werner":
        bins = [0.5, 1.5, 5, 10, np.inf]
        bin_names = ["0.5-1.5m", "1.5-5m", "5-10m", "10+m"]
        bin_colours = {
            "0.5-1.5m": "#0000FF",  # hex colours
            "1.5-5m": "#00EEEE",
            "5-10m": "#FFFF00",
            "10+m": "#FF0000"
        }
    else:
        print("Class type not known")
    print(bin_names)

    # Bin heights into classes
    print("Classifying trees...")

    class_indices = np.digitize(point_max_z, bins) - 1
    valid = (class_indices >= 0) & (class_indices < len(bin_names))

    points = points[valid]
    class_indices = class_indices[valid]

    # Get unique height classes and initialise colour array
    colors = np.zeros((len(points), 3))
    color_map = {k: to_rgb(v) for k, v in bin_colours.items()}

    for i, label in enumerate(bin_names):
        mask = class_indices == i
        colors[mask] = color_map[label]

    # create Open3D point cloud to plot
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)

    # display plot
    o3d.visualization.draw_geometries([pcd])


if __name__ == "__main__":
    # Set working directory
    date = '20250819'
    plot_no = '1A'
    os.chdir(f'c:/lidar/tlf/{date}/CSF/norm/treeiso/{plot_no}')

    # LAS file with tree IDs to plot
    lasfile = f'{date}_TLF_{plot_no}_clipped_plot_iso.laz'

    # Select height classification type
    classtype = 'Werner'  # alternative is 'Arbitrary'

    # Run function
    class_tree_height(lasfile, classtype)