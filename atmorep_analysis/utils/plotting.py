"""
Methods for creating plots.
"""

__authors__ = "Ilaria Luise"
__email__ = "ilaria.luise@cern.ch"
__date__ = "2023-12-20"
__update__ = "2023-12-22"

# for processing data
import os
import logging
import numpy as np
import xarray as xr
import pandas as pd
from itertools import product

# for plotting
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.rcParams['axes.linewidth'] = 0.1
import matplotlib.colors as mcolors

from mpl_toolkits.axes_grid1 import make_axes_locatable

#for maps
import cartopy
import cartopy.crs as ccrs  #https://scitools.org.uk/cartopy/docs/latest/installing.html
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import cartopy.feature as cfeature
from atmorep_analysis.utils.utils import get_units
# auxiliary variable for logger
module_name = os.path.basename(__file__).rstrip(".py")

########################################

def CustomPalette():
  colors = [ (0.278, 0.380, 0.620), (0.867, 0.647, 0.365), (0.991, 0.949, 0.765)]
  cmap = mcolors.LinearSegmentedColormap.from_list('YlBu', colors, N=100)
  return cmap

def MathematicaPalette():
  colors = [ 
          (0.368417,	0.506779,	0.709798),
          (0.880722,	0.611041,	0.142051),
          (0.560181,	0.691569,	0.194885),
          (0.922526,	0.385626,	0.209179),
          (0.528488,	0.470624,	0.701351),
          (0.772079,	0.431554,	0.102387),
          (0.363898,	0.618501,	0.782349),
          (1.000000,	0.750000,	0),
          (0.647624,	0.378160,	0.614037),
          (0.571589,	0.586483,	0.),
          (0.915000,	0.332500,	0.2125),
          (0.400822,	0.522007,	0.85),
          (0.972829,	0.621644,	0.073362),
          (0.736783,	0.358000,	0.503027),
          (0.280264,	0.715000,	0.429209)
          ]
  cmap = mcolors.LinearSegmentedColormap.from_list('MathCol', colors, N=len(colors))
  return cmap


########################################
   
def create_canvas(figsize = (8, 8), ncols = 1, nrows = 1):  
  fig, ax_temp = plt.subplots(figsize=(6, 6))
  gs = fig.add_gridspec(ncols, nrows)
  ax_temp.remove()
  ax = [fig.add_subplot(gs[c,r]) for c,r in product(range(ncols), range(nrows))]
  return fig, ax

########################################

def imshow(data, ax, title = '', vmin=None, vmax=None, colorbar = False, remove_ticks = False):
  im = ax.imshow(data, cmap=CustomPalette(), vmin=vmin, vmax=vmax)
  ax.set_title(title, color='dimgray')
  if remove_ticks:
    ax.set_xticks([]), ax.set_yticks([])
  return im

########################################

def plot(hlist, ax, linewidth = 1):
  for h in hlist:
    ax.plot(h[0], label = h[1], color = h[2], linewidth = 1.5)
  ax.legend(frameon=False)
  return ax

########################################

def plot_on_map(data, field, cmap = "RdBu", norm = None, zrange = [0.,0.1]):
    """
    plot on a world map
    """
    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree(central_longitude=180))
    ax.set_global()
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.set_xticks([0, 60, 120, 180, 240, 300, 360], crs=ccrs.PlateCarree())
    ax.set_yticks([-90, -60, -30, 0, 30, 60, 90], crs=ccrs.PlateCarree())
    lon_formatter = LongitudeFormatter(zero_direction_label=True)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)
    #see: https://matplotlib.org/stable/tutorials/colors/colormapnorms.html
    pos1 = ax.get_position() # get the original position 
    pos2 = [pos1.x0 - 0.04, pos1.y0,  pos1.width, pos1.height] 
    ax.set_position(pos2) # set a new position

    if(norm != None):
      im = plt.imshow(data, cmap=cmap, extent=[-180,180,-90,90], norm=norm) #or use plt.pcolor
    else:
      im = plt.imshow(data, cmap=cmap, extent=[-180,180,-90,90], vmin=zrange[0],  vmax=zrange[1]) #or use plt.pcolor
    cbar = plt.colorbar(im, shrink=0.7, cax=fig.add_axes([0.9, 0.23, 0.022, 0.5])) #, format='%.0e')
    cbar.set_label(get_units(field), y=-0.04, ha='right', rotation=0)
   # plt.savefig(name)
    return fig

########################################

def plot_on_map_custom_edges(data, edges, cmap = "RdBu", norm = None, zrange = [0.,0.1]):
    """
    plot on a world map
    """
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree(central_longitude=180))
    ax.set_global()
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    # ax.set_xticks([0, 60, 120, 180, 240, 300, 360], crs=ccrs.PlateCarree())
    # ax.set_yticks([-90, -60, -30, 0, 30, 60, 90], crs=ccrs.PlateCarree())
    lon_formatter = LongitudeFormatter(zero_direction_label=True)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)
    im = plt.imshow(data, cmap=cmap, vmin=zrange[0],  vmax=zrange[1]) #or use plt.pcolor
    ax.set_ylim(min(edges[:2]), max(edges[:2]))
    ax.set_xlim(min(edges[2:]), max(edges[2:])) 
    plt.colorbar(im, orientation="horizontal", shrink=0.7)
   # plt.savefig(name)
    return fig

def plot_1D_wDiff(field, data1, data2, label1, label2):
  
    fig1, ax_temp = plt.subplots(figsize=(6, 6)) 
    gs = fig1.add_gridspec(ncols = 1, nrows = 2, height_ratios = [3,1])
    ax_temp.remove()
    axs = []
    axs.append(fig1.add_subplot(gs[0,0]))
    axs.append(fig1.add_subplot(gs[1,0]))
    # axs.append(fig1.add_subplot(gs[2,0]))
    data1_f = data1.flatten()
    data2_f = data2.flatten()
    xmin = min(np.minimum(data1_f, data2_f))
    xmax = max(np.maximum(data1_f, data2_f))
    
    plt1 = axs[0].hist( data1_f, bins=50, fill=False, label = label1, range = [xmin, xmax], color='royalblue', histtype = 'step')
    plt2 = axs[0].hist( data2_f, bins=50, fill=False, label = label2,  range= [xmin, xmax], color='red', histtype = 'step')

    axs[0].set_xlim([xmin, xmax])
    axs[0].legend(frameon=False)
    
    #ratio and diff plots 
    width = (plt1[1][0] - plt1[1][-1])/len(plt1[1])
    diff = (plt1[0]-plt2[0])-width
    xvalues = plt1[1][:-1]-width
    axs[1].axhline(y=0., color='darkgray', linestyle='-', linewidth=0.5)
    axs[1].bar(xvalues, height=diff,
             width = width, align = 'edge')
    axs[1].ticklabel_format(axis='y', style='sci', scilimits=(2,2))
    axs[1].set_ylabel(label1+"-"+label2)
    axs[1].set_xlim([xmin, xmax])

    # ratio = np.divide(plt1[0], plt2[0])-width
    # axs[2].axhline(y=1., color='darkgray', linestyle='-', linewidth=0.5)
    # axs[2].bar(plt1[1][:-1], height=ratio, color = 'grey',alpha = 0.5, 
    #          width= width , align = 'edge')
    # axs[2].set_xlabel(field)
    # axs[2].set_ylabel(label1+"/"+label2)
    # axs[2].set_ylim([0, 2])
    # axs[2].set_xlim([xmin, xmax])
    plt.tight_layout()
    fig1.align_ylabels()
    return fig1

########################################

# auxiliary function for colormap
def get_colormap_temp(levels=None):
    """
    Get a nice colormap for plotting topographic height
    :param levels: level boundaries
    :return cmap: colormap-object
    :return norm: normalization object corresponding to colormap and levels
    """
    bounds = np.asarray(levels)

    nbounds = len(bounds)
    col_obj = mpl.cm.seismic_r(np.linspace(0.5, 1., nbounds))

    # create colormap and corresponding norm
    cmap = mpl.colors.ListedColormap(col_obj, name="temp" + "_map")
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    return cmap, norm, bounds


# for making plot nice
def decorate_plot(ax_plot, plot_xlabel=True, plot_ylabel=True):
    fs = 16
    # if "login" in host:
    # add nice coast- and borderlines
    ax_plot.coastlines(linewidth=0.75)
    ax_plot.coastlines(linewidth=0.75)
    ax_plot.add_feature(cartopy.feature.BORDERS)

    # adjust extent and ticks as well as axis-label
    ax_plot.set_xticks(np.arange(0., 360. + 0.1, 2.))  # ,crs=projection_crs)
    ax_plot.set_yticks(np.arange(-90., 90. + 0.1, 2.))  # ,crs=projection_crs)

    ax_plot.set_extent([4., 17, 46., 56.])    # , crs=prj_crs)
    ax_plot.minorticks_on()
    ax_plot.tick_params(axis="both", which="both", direction="out", labelsize=fs)

    # some labels
    if plot_xlabel:
        ax_plot.set_xlabel("Longitude [°E]", fontsize=fs)
    if plot_ylabel:
        ax_plot.set_ylabel("Latitude[°N]", fontsize=fs)

    return ax_plot


# for creating plot
def create_mapplot(data1, data2, plt_fname, opt_plot={}):
    # get coordinate data
    try:
        time, lat, lon = data1["time"].values, data1["lat"].values, data1["lon"].values
        time_stamp = (pd.to_datetime(time)).strftime("%Y-%m-%d %H:00 UTC")
    except Exception as err:
        print("Failed to retrieve coordinates from data1")
        raise err
    # construct array for edges of grid points
    dy, dx = np.round((lat[1] - lat[0]), 2), np.round((lon[1] - lon[0]), 2)
    lat_e, lon_e = np.arange(lat[0]-dy/2, lat[-1]+dy, dy), np.arange(lon[0]-dx/2, lon[-1]+dx, dx)

    title1, title2 = opt_plot.get("title1", "input T2m"), opt_plot.get("title2", "target T2m")
    title1, title2 = "{0}, {1}".format(title1, time_stamp), "{0}, {1}".format(title2, time_stamp)
    levels = opt_plot.get("levels", np.arange(-5., 25., 1.))

    # get colormap
    cmap_temp, norm_temp, lvl = get_colormap_temp(levels)
    # create plot objects
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8), sharex=True, sharey=True,
                                   subplot_kw={"projection": ccrs.PlateCarree()})

    # perform plotting
    _ = ax1.pcolormesh(lon_e, lat_e, np.squeeze(data1.values), cmap=cmap_temp, norm=norm_temp)
    temp2 = ax2.pcolormesh(lon_e, lat_e, np.squeeze(data2.values), cmap=cmap_temp, norm=norm_temp)

    ax1, ax2 = decorate_plot(ax1), decorate_plot(ax2, plot_ylabel=False)

    ax1.set_title(title1, size=14)
    ax2.set_title(title2, size=14)

    # add colorbar
    cax = fig.add_axes([0.92, 0.3, 0.02, 0.4])
    cbar = fig.colorbar(temp2, cax=cax, orientation="vertical", ticks=lvl[1::2])
    cbar.ax.tick_params(labelsize=12)

    # save plot and close figure
    plt_fname = plt_fname + ".png" if not plt_fname.endswith(".png") else plt_fname
    print(f"Save plot in file '{plt_fname}'")
    fig.savefig(plt_fname, bbox_inches="tight")
    plt.close(fig)


def save_ims( dir_out, field, data, name, min_val = 1., max_val = -1.) :
  
  if not os.path.exists(dir_out ):
    os.makedirs( dir_out)

  cmap = mpl.colormaps.get_cmap('PuBuGn')

  if 1. == min_val : 
    min_val = data.min()
  if -1. == max_val : 
    max_val = data.max()
  print( 'min / max : {} / {}'.format( min_val, max_val) )
  print(data.min(), data.max())
  bname = dir_out + '/fig_{}_{}.{}'
  fname = bname.format( field, name, 'png' )
  plt.imsave( fname, data, vmin=min_val, vmax=max_val, cmap = cmap )
  fname = bname.format( field, name, 'pdf' )
  plt.imsave( fname, data, vmin=min_val, vmax=max_val, cmap = cmap )
  plt.close()
    # print( 'Finished saving figures for step={}, tidx = {}.'.format( epoch, tidx) )
