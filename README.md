# tree_metrics
## Derive metrics from segmented point cloud with unique tree IDs. Requires a segmented point cloud with a tree ID attribute.

Extract tree crowns as polygons using 2D alpha shapes.

Assign metrics to these polygons:
  - Crown area (m^2) - Crown area derived from 2D alpha shape polygons (adaptive alpha value based on crown bounding box)
  - Maximum diameter of crown (m) - max planar distance between points of crown
  - Average diameter of crown (m) - mean of max and min diameters of crown
  - Tree height (m) - Ground to tip of crown
  - Crown height (m) - Base of crown to tip
  - Crown volume (m^3) - Two metrics: (i) the volume of crown assuming a conical crown (1/3* area * crown height), (ii) volume from 3D alpha shape of crown (more realistic representation)
