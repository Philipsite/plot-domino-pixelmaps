"""
A python script to plot pixelmaps generated by domnio

12.12.2022 Advanced Phase Equilibrium Course HS22
written by: Philip Hartmeier
"""
import matplotlib.cm
import matplotlib.colors

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

# define a global endmember dict, linking database, minerals and all endmembers
em_dict_global = {}
em_dict_global["jun92d"] = {}
em_dict_global["jun92d"]["biotite"] = "Ann", "Phl"
em_dict_global["jun92d"]["white mica"] = "Ms", "Pg", "MgC", "FeC"
em_dict_global["jun92d"]["margarite"] = "Mrg"
em_dict_global["jun92d"]["garnet"] = "Gr", "Py", "Alm", "spf"
em_dict_global["jun92d"]["chlorite"] = "Ame", "Pen", "FeAm", "FeP"


class MakeMapper:
    def __init__(self, parent_dir, database, em_dict_global=em_dict_global):
        self.parent_dir = Path(parent_dir)
        # create instance endmember dict
        self.endmeber_dict = em_dict_global[database]

    def idx_grid(limits, noSteps):
        """
        Function to be used in read_pixinfo() method
        calculate an array of P or T for specified upper and lower limit
        and number of steps (PT-points).
        Must be tranposed for P to match makemapper format

        Args:
            limits (float): array with lower and upper limit
            noSteps (int): number of point along P or T axis

        Returns:
            np.array: Array with values for T or P, idx of flattened array corresponds to pixelmap idx
        """
        diff = limits[1] - limits[0]
        step = diff / noSteps

        start = limits[0] + (step * 0.5)
        end = limits[1] - (step * 0.5)

        grid = np.linspace(start, end, noSteps)
        grid = np.array([grid])
        grid = np.repeat(grid, noSteps, axis=0)

        return grid

    def read_pixinfo(self):
        """Reading in the pixinfo txt from pixelmap output

        Saves T_grid, P_grid, bulk, pixmap_names to attributes
        """
        file_path = Path(self.parent_dir, "pixinfo")

        pixinfo = open(file_path)
        pixinfo = pixinfo.readlines()
        # strip "\n" and trailing/leading spaces
        pixinfo = [line.strip() for line in pixinfo]

        # extract T min max and P min max
        PT_limits = np.float32(pixinfo[2].split())
        T_limits = PT_limits[0:2]
        P_limits = PT_limits[2:4]

        # read n.o. steps in X and Y
        T_noSteps, P_noSteps = np.int16(pixinfo[4].split())[0:2]

        # read lines to skip
        temp_idx = np.int16(pixinfo[5])

        # read bulk composition
        temp_idx = 7 + temp_idx
        bulk = pixinfo[temp_idx]

        # read composition lines to skip
        comp_lines = np.int16(pixinfo[temp_idx - 1])
        temp_idx = comp_lines + temp_idx

        # read all calculated pixelmaps
        pixmap_names = pixinfo[temp_idx:]

        # calculate array with PT for indices
        T_grid = MakeMapper.idx_grid(T_limits, T_noSteps).flatten()
        # transpose P grid, to match pixelmap format from domino
        P_grid = np.transpose(MakeMapper.idx_grid(P_limits, P_noSteps)).flatten()

        # save to attributs
        self.T_grid = T_grid
        self.P_grid = P_grid
        self.bulk = bulk
        self.pixmap_names = pixmap_names

    def read_pixelmap(parent_dir, file_name):
        """func to be used in read_mineral_variable() method.
        read a pixelmap .txt file and adjust indexing to python convention.

        Args:
            parent_dir (Path): Should be taken from MakeMapper.parentdir
            file_name (Path): Filename of pixelmap for a variable-endmember pair

        Returns:
            pd.DataFrame: df of pixelmap
        """
        file_path = Path(parent_dir, file_name)
        pixelmap = pd.read_csv(file_path, sep="    ",
                               header=None,
                               names=["px_idx", "value"],
                               engine="python")

        # adjust idx for python convention
        pixelmap["px_idx"] = pixelmap["px_idx"] - 1

        return pixelmap

    def PT_to_pixelmap(pixelmap, T_grid, P_grid):
        """func to be used in read_mineral_variable() method.

        Args:
            pixelmap (pd.Dataframe): pixelmap dataframe
            T_grid (np.array): Should be taken from MakeMapper.T_grid
            P_grid (np.array): Should be taken from MakeMapper.P_grid

        Returns:
            pd:DataFrame: update pixelmap df, with P-T added
        """
        pixelmap["T"] = T_grid[pixelmap["px_idx"]]
        pixelmap["P"] = P_grid[pixelmap["px_idx"]]

        return pixelmap

    def read_mineral_variable(self, mineral, compositional_var="Mg#"):
        """Read pixelmap for a specified variable of interest.
        Maps for all endmembers of mineral (specified in database) are read
        and concatenated.

        Args:
            mineral (str): mineral name, endmember of solid solutions are taken from MakeMapper.endmember_dict.
            compositional_var (str, optional): A variable of interest for the given mineral. Defaults to "Mg#".
                possible variables: "Al_pfu", "Mg#", "n", "n_H2O", "rho", "Si_pfu", "vol", "wt_H2O"

        Saves concatenated maps of all endmembers with added P-T-conditions to pixelmap attribute
        """
        # get endmembers
        end_members = self.endmeber_dict[mineral]

        filenames_list = []
        for end_member in end_members:
            file_name = compositional_var+"_"+"["+end_member+"]"

            if file_name in self.pixmap_names:
                filenames_list.append(file_name)
            else:
                print("ERROR: endmember [{em}] variable [{var}] combination does not exist.".format(em=end_member, var=compositional_var))

        pixel_map_allEndMemebers = pd.DataFrame()
        for file_name in filenames_list:
            px_map = MakeMapper.read_pixelmap(parent_dir=self.parent_dir, file_name=file_name)
            px_map["endmember_var"] = file_name
            pixel_map_allEndMemebers = pd.concat((pixel_map_allEndMemebers, px_map), axis=0)

        pixel_map_def = MakeMapper.PT_to_pixelmap(pixelmap=pixel_map_allEndMemebers,
                                                  T_grid=self.T_grid,
                                                  P_grid=self.P_grid)

        self.pixelmap = pixel_map_def

    def get_variable_names(self):
        """Returning the list of all read pixelmaps

        Returns:
            list: pixel map names
        """
        return self.pixmap_names

    def plot_pixelmap(self, cmap="magma"):
        fig, ax = plt.subplots(figsize=(6, 6))

        cmap = plt.cm.get_cmap(cmap)
        # create normalization instance
        norm = matplotlib.colors.Normalize(vmin=self.pixelmap["value"].min(), vmax=self.pixelmap["value"].max())
        # create a scalarmappable from the colormap
        sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])

        ax.scatter(x=self.pixelmap["T"],
                   y=self.pixelmap["P"],
                   c=cmap(norm(self.pixelmap["value"])))

        ax.set_xlabel("Temperature /C")
        ax.set_ylabel("Pressure /bar")

        fig.colorbar(sm, ax=ax, fraction=0.03)

        plt.show()

    def calc_volume_fraction(self, mineral):
        # get endmembers
        end_members = self.endmeber_dict[mineral]

        filenames_list = []
        for end_member in end_members:
            file_name = "vol_"+"["+end_member+"]"

            if file_name in self.pixmap_names:
                filenames_list.append(file_name)
            else:
                print("ERROR: endmember [{em}] variable [vol] combination does not exist.".format(em=end_member))

        pixel_map_allEndMemebers = pd.DataFrame()
        for file_name in filenames_list:
            px_map = MakeMapper.read_pixelmap(parent_dir=self.parent_dir, file_name=file_name)
            px_map["endmember_var"] = file_name
            pixel_map_allEndMemebers = pd.concat((pixel_map_allEndMemebers, px_map), axis=0)

        tot_vol_map = MakeMapper.read_pixelmap(parent_dir=self.parent_dir, file_name="V_solids")
        tot_vol_map.rename(columns={"value": "tot_vol"}, inplace=True)

        pixel_map_def = MakeMapper.PT_to_pixelmap(pixelmap=pixel_map_allEndMemebers,
                                                  T_grid=self.T_grid,
                                                  P_grid=self.P_grid)

        pixel_map_def = pixel_map_def.join(tot_vol_map.set_index("px_idx"), on="px_idx")
        pixel_map_def["vol_frac"] = pixel_map_def["value"]/pixel_map_def["tot_vol"]

        self.pixelmap = pixel_map_def

    def plot_vol_fraction(self, cmap="magma"):
        fig, ax = plt.subplots(figsize=(6, 6))

        cmap = plt.cm.get_cmap(cmap)
        # create normalization instance
        norm = matplotlib.colors.Normalize(vmin=self.pixelmap["vol_frac"].min(), vmax=self.pixelmap["vol_frac"].max())
        # create a scalarmappable from the colormap
        sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])

        ax.scatter(x=self.pixelmap["T"],
                   y=self.pixelmap["P"],
                   c=cmap(norm(self.pixelmap["vol_frac"])))

        ax.set_xlabel("Temperature /C")
        ax.set_ylabel("Pressure /bar")

        fig.colorbar(sm, ax=ax, fraction=0.03)

        plt.show()
