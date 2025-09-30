import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

### Bin and plot out height class distribution
### Read tree metric shapefile
df = gpd.read_file('output/shapefile/with/metrics.shp')

# Select height class type - arbitrary or Werner
htype = "Werner"

# Assign bins by selected height class type
if htype == "Arbitrary":
    bins = [2, 4, 6, 8, 10, 12, 14, 16]
    bin_names = ["2-4m", "4-6m", "6-8m", "8-10m", "10-12m", "12-14m", "14-16m"]
    bin_colours = {
        "2-4m": "#0000FF",
        "4-6m": "#0077F6",
        "6-8m": "#00EEEE",
        "8-10m": "#7FF676",
        "10-12m": "#FFFF00",
        "12-14m": "#FF7F00",
        "14-16m": "#FF0000"
    }
    ht_min = 2

elif htype == "Werner":
    bins = [0.5, 1.5, 5, 10, 30]
    bin_names = ["0.5-1.5m", "1.5-5m", "5-10m", "10+m"]
    bin_colours = {
        "0.5-1.5m": "#0000FF",
        "1.5-5m": "#00EEEE",
        "5-10m": "#FFFF00",
        "10+m": "#FF0000"
    }
    ht_min = 0.5

else:
    print("Not known")

print(bin_names)

# Bin heights into classes
df["htclass"] = pd.cut(df["Z"], bins=bins, labels=bin_names, right=False)

# Remove NA trees
df = df[df["htclass"].notna()]

# Show data summary
print(df.describe(include="all"))

# Plot height class distribution
plt.figure(figsize=(10, 6))
sns.set_theme(style="whitegrid")

# Create barplot
ax = sns.countplot(data=df, x="htclass", palette=bin_colours)

# Customize plot
ax.set_xlabel("Height Class")
ax.set_ylabel("Count")
plt.xticks(rotation=45)
plt.tight_layout()

# Save plot
plt.savefig("output/height_class_distribution.png", dpi=300)
plt.show()
