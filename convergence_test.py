import os

dir_run = "convergence_tests/coated_sphere_4-5_runs"
# dir_run = "convergence_tests/uncoated_sphere_runs"


dirs = os.listdir(dir_run)
dirs.sort()

# this number means the folder whetre you want to start,
# should half the thing already have been run and you want to continue
# so '3' means start at 003
dirs = dirs[9:]

for dir in dirs:
    os.system(f"python3 my_program.py -r {dir_run}/{dir}")
