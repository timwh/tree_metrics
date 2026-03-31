"""
norm2chm.py: Covert normalised point cloud into canopy height model (CHM)
Author: Tim Whiteside
Requires: laspy,numpy, gdal, rasterio, matplotlib
"""

import os
from os.path import splitext
from pathlib import Path
import laspy
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colormaps as cm
from osgeo import gdal
import rasterio
from rasterio.transform import from_origin
from rasterio.mask import mask
from scipy.interpolate import griddata
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import ConvexHull
from scipy.spatial import Delaunay
from shapely.geometry import Polygon
import geopandas as gpd



def norm2chm(input_las,grid_res=0.2):
    """
    Convert a normalised point cloud into a gridded canopy height model
    :param input_las:
    :param grid_res:
    :return: filled_chm:
    """

    las = laspy.read(input_las)

    # Get 2D footprint
    points_2d = np.column_stack((las.x, las.y))
    hull = ConvexHull(points_2d)
    hull_polygon = Polygon(points_2d[hull.vertices])

    # convert footprint to gdf
    gdf = gpd.GeoDataFrame(geometry=[hull_polygon], crs=epsg_no)

    # Filter out ground points (classification == 2)
    veg_mask = las.classification != 10
    x = las.x[veg_mask]
    y = las.y[veg_mask]
    z = las.z[veg_mask] - min(las.z[veg_mask])

    # Define grid resolution
    res = grid_res  # meters
    xmin, ymin = np.min(x), np.min(y)
    xmax, ymax = np.max(x), np.max(y)

    ncols = int((xmax - xmin) / res) + 1
    nrows = int((ymax - ymin) / res) + 1

    # Create empty grid
    chm = np.full((nrows, ncols), np.nan)

    # Assign max Z to each grid cell
    ix = ((x - xmin) / res).astype(int)
    iy = ((ymax - y) / res).astype(int)  # flip Y for raster orientation

    for i, j, height in zip(iy, ix, z):
        if np.isnan(chm[i, j]) or height > chm[i, j]:
            chm[i, j] = height

    # Replace NaNs with 0 or interpolate if needed
    chm = np.nan_to_num(chm, nan=0)
    rows, cols = np.indices(chm.shape)
    valid_mask = ~np.isnan(chm)
    points = np.column_stack((rows[valid_mask], cols[valid_mask]))
    values = chm[valid_mask]

    # Interpolate over missing cells
    filled_chm = griddata(points, values, (rows, cols), method="nearest")
    return filled_chm, xmin, xmax, ymin, ymax, gdf

if __name__ == "__main__":
    epsg_no = "EPSG:7853"
    plot = '1'
    date = '20251225' #YYYYMMDD

    folder = Path(f'c:/lidar/{date}/{plot}')
    extension = '.laz'
    print(folder)
    for file in folder.glob(f'*_plot_iso{extension}'):
        input_las = file
        filename = os.path.splitext(input_las)[0]
        print(filename)
        def_return = norm2chm(input_las, grid_res=0.2)

        filled_chm = def_return[0]
        xmin = def_return[1]
        ymax = def_return[4]
        res = 0.2
        gdf = def_return[5]
        # Assuming your CHM is a NumPy array and has NaNs for no-data
        # Create a colormap with NaNs fully transparent
        cmap = cm.get_cmap('Spectral_r').copy()  # '_r' gives you the reversed (inverted) version
        cmap.set_bad(color='none')  # makes NaNs fully transparent

        # Plot
        plt.figure(figsize=(10, 8))
        im = plt.imshow(filled_chm, cmap=cmap, origin='upper')
        cbar = plt.colorbar(im)
        cbar.set_label('Canopy Height (m)', fontsize=14)
        cbar.ax.tick_params(labelsize=12)

        plt.title(f"Canopy Height Model - {filename}")
        plt.axis('off')  # optional cleanup
        plt.savefig(f"{filename}_CHM_pub.png", dpi=300)
        plt.show()

        # Save as GeoTIFF
        transform = from_origin(xmin, ymax, res, res)
        #filename,ext = splitext(input_las)
        res_cm = res*100
        with rasterio.open(
            f"{filename}_{int(res_cm)}cm.tif",
            "w",
            driver="GTiff",
            height=filled_chm.shape[0],
            width=filled_chm.shape[1],
            count=1,
            dtype=filled_chm.dtype,
            crs=epsg_no,  # Update to match your data
            transform=transform,
        ) as dst:
            dst.write(filled_chm, 1)


        with rasterio.open(f"{filename}_{int(res_cm)}cm.tif") as src:
            shapes = gdf.geometry
            output_chm, out_transform = mask(src, shapes, crop=True)
            # Copy and update metadata
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": output_chm.shape[1],
                "width": output_chm.shape[2],
                "transform": out_transform
            })

        # Save to new file
        with rasterio.open(f"{filename}_{int(res_cm)}cm_mask.tif", "w", **out_meta) as dest:
            dest.write(output_chm)
