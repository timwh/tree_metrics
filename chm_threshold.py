import os
import numpy as np
from osgeo import gdal
import rasterio as rio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
import matplotlib.pyplot as plt

# Load CHM
def chm_threshold(plot_no, wkg_dir, input_raster, threshold = 2):
    """
    Function for thresholding a surface model
    :param plot_no: str
    :param wkg_dir: str or Path
    :param input_raster: str or Path
    :param threshold: num in meters
    """
    os.chdir(wkg_dir)
    with rio.open(input_raster) as src:
        chm = src.read(1)
        transform = src.transform
        crs = src.crs
        # Set and apply threshold
        binary_chm = np.where(chm >= threshold, 1, 0)
        masked_binary = np.ma.masked_where(np.isnan(chm), binary_chm)

    with rio.open(
        'binary.tif',
        "w",
        driver = "GTiff",
        height = masked_binary.shape[0],
        width = masked_binary.shape[1],
        count=1,
        dtype='int32',
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(masked_binary,1)
        print(dst.dtypes)


    plt.figure(figsize=(10, 8))
    plt.imshow(masked_binary, cmap='gray', origin='upper')
    plt.title(f"{plot_no} Binary Canopy Mask (≥ {threshold} m)")
    plt.axis('off')
    plt.show()


    with rio.open('binary.tif') as src:
        canopy = src.read(1) == 1
        # Extract shapes (polygons) for value 1
        results = (
            {"properties": {"value": v}, "geometry": s}
            for s, v in shapes(src.read(1), mask=canopy, transform=transform)
            if v == 1
        )

    # Convert to GeoDataFrame
    geoms = [shape(r["geometry"]) for r in results]
    gdf = gpd.GeoDataFrame(geometry=geoms, crs=src.crs)

    # Save to shapefile
    gdf.to_file(f"{plot_no}_canopy_mask.shp")


if __name__ == "__main__":
    plot = '1'
    date ='20251225' #YYYYMMDD
    wkg_dir = f'c:/lidar/{date}/{plot}'
    input_file = f'{date}_{plot}_20cm.tif'

    chm_threshold(plot, wkg_dir, input_file, threshold)




