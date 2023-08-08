Simple plotting utility written in python for geoloc. Requires numpy and matplotlib and CartoPy.

It reads geoloc's `--print-matrix` output from stdin, and plots the results
on a map.

Usage examples (assume mymsg.txt contains comma-separated features as input for geoloc):

Plot matrix on Europe map:

```
geoloc --classify --print-matrix mymsg.txt | ./geoplot.py --europe
```

Plot on world map, projection is mercator:

```
geoloc --classify --print-matrix mymsg.txt | ./geoplot.py --world --proj mercator
```

Plot on U.S. map, use contours instead of grid:

```
geoloc --classify --print-matrix mymsg.txt | ./geoplot.py --us --contour
```

As previous, but output PDF:

```
geoloc --classify --print-matrix mymsg.txt | ./geoplot.py --us --contour --output map.pdf
```

- MH20140406
- WB20230808
