#!/usr/bin/env python3

#####################################################################################
# Simple map plotting of --print-matrix output from geoloc                          #
#                                                                                   #
# Usage: reads geoloc matrix from stdin and produces a plot on map                  #
#                                                                                   #
# Plot matrix on Europe map:                                                        #
# geoloc --classify --print-matrix mymsg.txt | ./geoplot.py --europe                #
#                                                                                   #
# Plot on world map, projection is mercator:                                        #
# geoloc --classify --print-matrix mymsg.txt | ./geoplot.py --world --proj=merc     #
#                                                                                   #
# Plot on U.S. map, use contours instead of grid:                                   #
# geoloc --classify --print-matrix mymsg.txt | ./geoplot.py --us --contour          #
#                                                                                   #
# As previous, but output PDF:                                                      #
# geoloc --classify --print-matrix mymsg.txt | ./geoplot.py --us --contour --pdf    #
#                                                                                   #
# MH20140406                                                                        #
#####################################################################################

import argparse
import cartopy.crs as ccrs
import cartopy.feature as cf
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import sys
import os


PROJECTIONS = {
    'plate_carree': ccrs.PlateCarree,
    'albers_equal_area': ccrs.AlbersEqualArea,
    'azimuthal_equidistant': ccrs.AzimuthalEquidistant,
    'equidistant_conic': ccrs.EquidistantConic,
    'lambert_conformal': ccrs.LambertConformal,
    'lambert_cylindrical': ccrs.LambertCylindrical,
    'mercator': ccrs.Mercator,
    'miller': ccrs.Miller,
    'mollweide': ccrs.Mollweide,
    'orthographic': ccrs.Orthographic,
    'robinson': ccrs.Robinson,
    'sinusoidal': ccrs.Sinusoidal,
    'stereographic': ccrs.Stereographic,
    'transverse_mercator': ccrs.TransverseMercator,
    'utm': ccrs.UTM,
    'interrupted_goode_homolosine': ccrs.InterruptedGoodeHomolosine,
    'rotated_pole': ccrs.RotatedPole,
    'osgb': ccrs.OSGB,
    'euro_pp': ccrs.EuroPP,
    'geostationary': ccrs.Geostationary,
    'nearside_perspective': ccrs.NearsidePerspective,
    'eckert_i': ccrs.EckertI,
    'eckert_ii': ccrs.EckertII,
    'eckert_iii': ccrs.EckertIII,
    'eckert_iv': ccrs.EckertIV,
    'eckert_v': ccrs.EckertV,
    'eckert_vi': ccrs.EckertVI,
    'equal_earth': ccrs.EqualEarth,
    'gnomonic': ccrs.Gnomonic,
    'lambert_azimuthal_equal_area': ccrs.LambertAzimuthalEqualArea,
    'north_polar_stereo': ccrs.NorthPolarStereo,
    'osni': ccrs.OSNI,
    'south_polar_stereo': ccrs.SouthPolarStereo
}

def make_colormap(seq):
    """Return a LinearSegmentedColormap
    seq: a sequence of floats and RGB-tuples. The floats should be increasing
    and in the interval (0,1).
    """
    seq = [(None,) * 3, 0.0] + list(seq) + [1.0, (None,) * 3]
    cdict = {'red': [], 'green': [], 'blue': []}
    for i, item in enumerate(seq):
        if isinstance(item, float):
            r1, g1, b1 = seq[i - 1]
            r2, g2, b2 = seq[i + 1]
            cdict['red'].append([item, r1, r2])
            cdict['green'].append([item, g1, g2])
            cdict['blue'].append([item, b1, b2])
    return mcolors.LinearSegmentedColormap('CustomMap', cdict)

def make_rvb_colormap():
    c = mcolors.ColorConverter().to_rgb
    return make_colormap([c('white'), c('white'), 0.1, c('white'), c('yellow'), 0.33, c('yellow'), c('LightGreen'), 0.66,
                          c('LightGreen'), c('orange'), 0.8, c('orange'), c('red'), 0.95, c('red')])

def open_file(path: str):
    if sys.platform.startswith('darwin'):
        os.system('open {path}'.format(path=path))
    elif sys.platform.startswith('linux'):
        os.system('xdg-open {path}'.format(path=path))
    elif sys.platform.startswith('win32'):
        os.startfile(path)

parser = argparse.ArgumentParser(description='Simple map plotting of --print-matrix output from geoloc')
parser.add_argument('-u', '--us', action='store_true', help='Plot US map')
parser.add_argument('-e', '--europe', action='store_true', help='Plot Europe map')
parser.add_argument('-w', '--world', action='store_true', help='Plot world map')
parser.add_argument('-p', '--proj', choices=PROJECTIONS.keys(), default='plate_carree', help='Projection name')
parser.add_argument('-g', '--grid', action='store_true', help='Show grid')
parser.add_argument('-s', '--states', action='store_true', help='Plot state boundaries')
parser.add_argument('-c', '--contour', action='store_true', help='Plot contours instead of grid')
parser.add_argument('-o', '--output', help='Output file; extension specifies format')
parser.add_argument('-a', '--open_after', action='store_true', help='Open created file')
args = parser.parse_args()

if args.us:
    extent = [-130, -55, 25, 50]
elif args.world:
    extent = [-180, 180, -70, 70]
elif args.europe:
    extent = [-25, 30, 35, 70]
else:
    parser.exit(message='Please specify the map type (us or world or europe)')

rvb = make_rvb_colormap()
data = np.loadtxt(sys.stdin, delimiter='\t')
longranularity = data.shape[1]
latgranularity = int(longranularity/2)
lcenterskip = (180/longranularity)

ax = plt.axes(projection=PROJECTIONS[args.proj]())
ax.set_extent(extent, crs=PROJECTIONS[args.proj]())
ax.add_feature(cf.COASTLINE)
ax.add_feature(cf.BORDERS)

if args.states:
    ax.add_feature(cf.STATES, edgecolor='lightgrey')

if args.grid:
    ax.gridlines(xlocs=np.arange(-180, 180, 360 / latgranularity),
             ylocs=np.arange(-90, 90, 180 / latgranularity),
             draw_labels=True, dms=True, color='gray')

if args.contour:
    x = np.linspace(-180 + lcenterskip, 180 - lcenterskip, longranularity)
    y = np.linspace(-90 + lcenterskip, 90 - lcenterskip, latgranularity)
    x, y = np.meshgrid(x, y)
    p = ax.contourf(x, y, data, cmap=rvb, zorder=1, alpha=0.8)
else:
    x = np.linspace(-180 , 180, longranularity, endpoint=False)
    y = np.linspace(-90 , 90, latgranularity, endpoint=False)
    x, y = np.meshgrid(x, y)
    p = ax.pcolormesh(x, y, data, transform=PROJECTIONS[args.proj](), cmap=rvb, zorder=1, alpha=0.8)

plt.colorbar(p, orientation='horizontal')

if args.output is None:
    plt.show()
elif args.output.lower().endswith('.png'):
    plt.savefig(args.output, format='png')
    if args.open_after:
        open_file(args.output)
elif args.output.lower().endswith('.pdf'):
    plt.savefig(args.output, format='pdf')
    if args.open_after:
        open_file(args.output)
