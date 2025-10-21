# Optool extension to use DDA on GRF particles

Program uses ADDA and Optool to calculate opacities for Gaussian random field (GRF) particles.
A manual will be written later, this is basic usage for now.

to use, run `python3 my_program.py` with arguments.

command line options can be shown with -h or --help.

some small notes:
lnk files can be used for wavelength grid and 'material' the same as in optool.

for testing, spheres can be used instead of GRF particles. to do this, use the --sphere option. Because this still uses a DDA grid there are only 4 options for mantle fraction available, the most suitable one will be picked automatically.

A generated spectrum can be plotted interactively from results.dat using plot_spectrum.py, giving the path to results.dat as the argument.

A particle can be visualised with plot_shape.py, giving the path to the particle as the argument.