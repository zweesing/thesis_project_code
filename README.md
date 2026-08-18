# POTATOS (Particle Opacity Tool: ADDA Treats Odd Shapes)
## Optool extension to use DDA on GRF particles for calculating dust opacities

This program uses ADDA (https://github.com/adda-team/adda) and Optool (https://github.com/cdominik/optool) to calculate opacities for Gaussian random field (GRF) particles.

it is easiest to run the program from this directory, as it uses avg_params.dat and the particle directories. The relative path to the particle directories can also be changed at the top of my_program.py, if you do want to move things. avg_params.dat needs to be in the same directory as the script.

to use, run `python3 my_program.py` with arguments.

command line options can be shown with -h or --help.

some small notes:
lnk files can be used for wavelength grid and 'material' the same as in optool.

For testing, spheres can be used instead of GRF particles. to do this, use the --sphere option. Because this still uses a DDA grid there are only 4 options for mantle fraction available, the most suitable one will be picked automatically.

A generated spectrum can be plotted interactively from results.dat using plot_spectrum.py, giving the path to results.dat as the argument.

A particle can be visualised with plot_shape.py, giving the path to the particle as the argument.
