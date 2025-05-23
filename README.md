# tree_metrics
## Derive metrics from segmented point cloud with unique tree IDs.
### Requires a segmented point cloud with a tree ID attribute.

Extract tree crowns as polygons using 2D alpha shapes.

Assign metrics to these polygons:
  - Crown area (m^2) - Crown area derived from 2D alpha shape polygons (adaptive alpha value based on crown bounding box).
  - Maximum diameter of crown (m) - Maximum planar distance between points of crown.
  - Average diameter of crown (m) - The mean of max and min diameters of crown.
  - Tree height (m) - Measured from ground to the tip of crown.
  - Crown depth (m) - Measured from base of crown to the tip.
  - Crown volume (m^3) - Two metrics are provided: (i) the volume of crown assuming a conical crown (1/3* area * crown height), (ii) volume derived from the 3D alpha shape of the crown (a more realistic representation of volume).
