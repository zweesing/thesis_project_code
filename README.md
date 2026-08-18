# POTATOS (Particle Opacity Tool: ADDA Treats Odd Shapes)
## Optool extension to use DDA on GRF particles for calculating dust opacities

This program uses ADDA (https://github.com/adda-team/adda) and Optool (https://github.com/cdominik/optool) to calculate opacities for Gaussian random field (GRF) particles. No input files are required, it can function fully from the command line.

## Requirements
To run POTATOS, both Optool and ADDA need to be on your path. 
The other requirements are Numpy and matplotlib, which can be installed with `pip install -r requirements.txt`

it is easiest to clone this directory and run the program from here, as it uses avg_params.dat and the particle directories. The relative path to the particle directories can also be changed at the top of my_program.py, if you do want to move things around. avg_params.dat needs to be in the same directory as the script.

to use, run `python3 potatos.py` with arguments.

### example usage:
show all options

`python3 potatos.py -h`

A 0.1 micron grain made of pyroxene and carbon in a mass ratio of 0.7/0.3, averaging over 2 particles. The wavelength range is 1 to 25 micron (100 points).

`python3 potatos.py -a 0.1 -l 1 25 100 -c pyr 0.7 c 0.3 -n 2`

for a list of possible materials and their abbreviations, see the optool UserGuide https://github.com/cdominik/optool/blob/master/UserGuide.org. 


### other functionality:
lnk files can be used for wavelength grid and material the same as in optool.

For testing, spheres can be used instead of GRF particles. to do this, use the --sphere option. Because this still uses a DDA grid there are only 4 options for mantle fraction available, the most suitable one will be picked automatically.

A generated spectrum can be plotted interactively from results.dat using plot_spectrum.py, giving the path to results.dat as the argument.

A particle can be visualised with plot_shape.py, giving the path to the particle as the argument.

