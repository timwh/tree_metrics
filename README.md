# tree_metrics
<img src = "https://github.com/timwh/tree_metrics/blob/main/img/ChatGPT_Image_Sep_19_2025_01_51_06_PM.png" width = '250'> <img src="https://github.com/timwh/tree_metrics/blob/main/img/Screenshot_2025-05-23_145317.png" width="300" height="300" />
## Derive metrics from segmented point cloud with unique tree IDs.
### Requires a segmented point cloud with a tree ID attribute.

crown_metrics.py

Extract tree crowns as polygons using 2D alpha shapes.

Assign metrics to these polygons:
  - Crown area (m^2) - Crown area derived from 2D alpha shape polygons (adaptive alpha value based on crown bounding box).
  - Maximum diameter of crown (m) - Maximum planar distance between points of crown.
  - Average diameter of crown (m) - The mean of max and min diameters of crown.
  - Tree height (m) - Measured from ground to the tip of crown.
  - Crown depth (m) - Measured from base of crown to the tip.
  - Crown volume (m^3) - Two metrics are provided: (i) the volume of crown assuming a conical crown (1/3* area * crown height), (ii) volume derived from the 3D alpha shape of the crown (a more realistic representation of volume).




Plot tree height class distribution

<img src="https://github.com/timwh/tree_metrics/blob/main/img/Figure_1.png" width="500" height="300" />


