# %%
from makemap import MakeMapper

# %%
pxMap = MakeMapper("pixelmaps", "jun92d")
pxMap.read_pixinfo()
pxMap.read_mineral_variable("garnet", "x_spf")
pxMap.plot_pixelmap()
# %%
pxMap = MakeMapper("pixelmaps", database="jun92d")
pxMap.read_pixinfo()
pxMap.read_mineral_variable("white mica")
pxMap.plot_pixelmap(cmap="viridis")
# %%
pxMap = MakeMapper("pixelmaps", database="jun92d")
pxMap.read_pixinfo()
pxMap.read_mineral_variable("white mica", "Al_pfu")
pxMap.plot_pixelmap(cmap="viridis")

# %%
pxMap = MakeMapper("pixelmaps", database="jun92d")
pxMap.read_pixinfo()
pxMap.calc_volume_fraction("biotite")
pxMap.plot_vol_fraction(cmap="viridis")

# %%
pxMap = MakeMapper("pixelmaps", database="jun92d")
pxMap.read_pixinfo()
print(pxMap.get_variable_names())
# %%
pxMap.read_mineral_variable("garnet", "x_Alm")
pxMap.plot_pixelmap(cmap="magma")
# %%