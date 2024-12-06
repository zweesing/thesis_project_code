""" 
file to read and plot cross section as a function of wavelength for both optool and adda, with conversions.
runs optool first, generates
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import argparse

# defining units. I work in CGS throughout. multiply a number in a different unit with the variable of that unit to convert.
micron = 1e-4

# can also make this an arg
a_micron = 0.5  # micron (radius)

# adda doesnt deal well with big particles. dont worry about this, for the purpose of this we dont need smaller than this
lam_thresh = 1  # micron. all lambdas below this will be skipped by adda because it takes too long

# ------------------------------------------------------------------------------------- #
# get the material and the file
# lnk_data has a file with all abreviations

# NEW
# # try to do this by generating the optool lnk file and then reading in that?
# ------------------------------------------------------------------------------------- #

parser = argparse.ArgumentParser()
# parser.add_argument("material", help="specify the material")
parser.add_argument("folder", help="specify the folder for saving files")
args = parser.parse_args()

material = "pyr"
# material = args.material
folder = args.folder
os.system(f"mkdir {folder}")


def find_material_file():
    """old function. find the correct lnk opacities file"""
    files_folder = "/home/ziggy/thesis/optool/lnk_data"
    material_files_list = os.listdir(files_folder)
    material_files_list = [
        filename for filename in material_files_list if filename.endswith(".lnk")
    ]

    # if multiple files match, it will not recognize rn
    material_file = None
    for filename in material_files_list:
        if material in filename:
            material_file = filename


# ------------------------------------------------------------------------------------- #
# generate material file with optool and read it in
# read in material file
# ------------------------------------------------------------------------------------- #
# print(f'Reading refractive indices from {files_folder}/{material_file} ...')
# # read in file from optool for refractive indices.
# rfile = open(files_folder + '/' + material_file, "r")
# make the optool files
os.system(f"cd {folder} && optool -c {material} -a {a_micron} -mie -w ")
# read in file from optool for refractive indices.
rfile = open(folder + "/optool_mix.lnk", "r")

dum = rfile.readline()
header = ""

while dum.strip()[0] == "#":
    header = header + dum
    dum = rfile.readline()

# number of lambdas and rho
while len(dum.strip()) < 1:
    dum = rfile.readline()  # skip any empty lines
nlam = int(dum.split()[0])
rho = float(dum.split()[1])

lamarr = np.zeros(nlam)
narr = np.zeros(nlam)
karr = np.zeros(nlam)

# Read the refractive indices
dum = rfile.readline()
while len(dum.strip()) < 1:
    dum = rfile.readline()  # skip any empty lines
for ilam in range(nlam):
    dum = dum.split()
    lamarr[ilam] = float(dum[0]) * micron
    narr[ilam] = float(dum[1])  # refractive indices
    karr[ilam] = float(dum[2])

    dum = rfile.readline()

rfile.close()
# ------------------------------------------------------------------------------------- #
# call optool with the specified material
# ------------------------------------------------------------------------------------- #


# material must be a material recognised by optool
print(f"Running 'optool -c {material} -a {a_micron}' ...")
os.system(f"cd {folder} && optool -c {material} -a {a_micron} -mie")
# ------------------------------------------------------------------------------------- #
# read in optool data file
# this has a bunch of commented code, becasue if you replace it with that the script works without the venv
# ------------------------------------------------------------------------------------- #
rfile = open(f"{folder}/dustkappa.dat", "r")

dum = rfile.readline()
header = ""

while dum.strip()[0] == "#":
    header = header + dum
    dum = rfile.readline()

# Read the file format
while len(dum.strip()) < 1:
    dum = rfile.readline()  # skip any empty lines
iformat = int(dum)

# Read the number of wavelengths in the file and prepare arrays
nlam = int(rfile.readline())
lam_optool = np.zeros(nlam)
kabs = np.zeros(nlam)
ksca = np.zeros(nlam)
phase_g = np.zeros(nlam)

# Read the opacities
dum = rfile.readline()
while len(dum.strip()) < 1:
    dum = rfile.readline()  # skip any empty lines
for ilam in range(nlam):
    dum = dum.split()
    lam_optool[ilam] = float(dum[0]) * micron  # micron -> cm
    kabs[ilam] = float(dum[1])  # cm2/g
    ksca[ilam] = float(dum[2])
    phase_g[ilam] = float(dum[3])
    dum = rfile.readline()

rfile.close()


# this is shorter butr requires venv optool installed
# ------------------------------------
# import optool
# file1 = 'dustkappa.dat'
# header,lam_optool,kabs,ksca,g = optool.readoutputfile(file1,scat=False)
# nlam = lam_optool.shape[0]
# lam_optool = lam_optool *micron
# ------------------------------------


# converting to cross section. we use exptinction, so sum of opacities.
# then we divide by the volume x density to get the cross section. I think
kext = kabs + ksca

# convert to match with ADDA. opacity to cross section needs density. Doing manually for now, but should be read from file
# rho = 3.01 # g/cm3vr 08 nov

# extinction is in cm's
# what size to use? I'm getting confused about the -a and -d options and what optool gives, for now use one size. hardcoded for now
a = a_micron * micron

# cross section kappa x rho x volume?
Cext_optool = kext * rho * (4 / 3 * np.pi * a**3)  # cm2
Cabs_optool = kabs * rho * (4 / 3 * np.pi * a**3)

# Q is basically effective cross section divided by surface. so
Q_optool = Cext_optool / (np.pi * a**2)  # unitless


# ------------------------------------------------------------------------------------- #
# generate adda data
# ------------------------------------------------------------------------------------- #

# # make a directory
# dir_counter = 0
# no_dir = True
# while no_dir:
#     # check if dir is empty
#     if os.path.isdir(f'adda_runs{dir_counter}'):
#         dir_counter += 1
#     else:
#         os.system(f'mkdir adda_runs{dir_counter}')
#         no_dir = False
os.system(f"mkdir runs/{folder}/adda_runs")

# run adda
for i, lam in enumerate(lamarr):
    lam_micron = lam / micron
    if lam_micron < lam_thresh:  # these take so long
        pass

    else:

        n = narr[i]
        k = karr[i]

        # adda takes a and lambda in micron
        geom = False
        if not geom:
            os.system(
                f"cd {folder}/adda_runs && adda -eq_rad {a_micron} -lambda {lam_micron} -m {n} {k} -save_geom"
            )
            geom = True
        else:
            os.system(
                f"cd {folder}/adda_runs && adda -eq_rad {a_micron} -lambda {lam_micron} -m {n} {k}"
            )
        # rename files not trivial because i dont have the folder names? or do it in a second loop
        # os.system(f'cd {folder}/adda_runs/ &&')
for run_folder in os.listdir(f"{folder}/adda_runs"):
    os.system(f"cd {folder}/adda_runs/{run_folder} && mv log log.txt")
# ------------------------------------------------------------------------------------- #
# read in adda data
# ------------------------------------------------------------------------------------- #

adda_folders = os.listdir(f"{folder}/adda_runs")
adda_folders.sort()
adda_folders.pop(0)  # remove the exp count file
nlam = len(adda_folders)

# prepare arrays
Cexts = np.zeros(nlam)
Qext = np.zeros(nlam)
Cabs = np.zeros(nlam)
Qabs = np.zeros(nlam)

# not sure if this works
for i, a_folder in enumerate(adda_folders):
    try:
        f = open(f"{folder}/adda_runs/{a_folder}/CrossSec-Y", "r")

        lines = f.readlines()
        Cexts[i] = float(lines[0].split()[-1]) * micron**2
        Qext[i] = float(lines[1].split()[-1]) * micron**2
        Cabs[i] = float(lines[2].split()[-1]) * micron**2
        Qabs[i] = float(lines[3].split()[-1]) * micron**2

        f.close()
    except FileNotFoundError:
        Cexts[i] = Qext[i] = Cabs[i] = Qabs[i] = np.nan

# ------------------------------------------------------------------------------------- #
# plot both sets
# ------------------------------------------------------------------------------------- #

fig = plt.figure(figsize=(10, 7))
plt.title(f"a={a} cm, material = {material}")
plt.xlabel("lambda (cm)")
plt.ylabel("crosssection (cm2)")
plt.plot(lamarr[-nlam:], Cexts, label="ADDA Cext")
plt.plot(lamarr[-nlam:], Cabs, label="ADDA Cabs")
plt.plot(lam_optool, Cext_optool, label="optool Cext")
plt.plot(lam_optool, Cabs_optool, label="optool Cabs")
plt.xscale("log")
plt.legend()

plt.show()
