import numpy as np

# so this sucks a little bit but. it  can make a shape with two domains.
# it first makes two coordinate lists, and then writes those
shape_name = "my_small_coated_sphere"
# we need to write a shape file that has a bunch of x y z coordinates inside a sphere
# amount of points is determined by the box size
rad = [10, 8]
Ndom = 2
box_size = 32


def write_shape_file(filename, coordinates, Ndom=1, comments="some comment"):
    # idk why im doing this so complicatedly
    nofile = True
    counter = 0
    newfilename = filename

    while nofile:
        try:
            file = open(f"{newfilename}.geom", "x")
            nofile = False
        except FileExistsError:
            counter += 1
            newfilename = filename + str(counter)

    file.write("# some comments about the shape i made\n")
    file.write(f"# Volume1 = {len(coordinates[0])}\n# Volume2 = {len(coordinates[1])}")
    if Ndom == 1:
        for coordinate in coordinates:
            file.write(coordinate + "\n")
    else:
        # if Ndom is more than one, coordinates should be one dimension higher
        file.write(f"\nNmat={Ndom}\n")
        for domain in range(Ndom):
            for coordinate in coordinates[domain]:
                file.write(coordinate + " " + str(domain + 1) + "\n")

    file.close()
    return newfilename


def generate_coordinates(rad=8):
    # I still need to test this with different radii

    # box size
    size = size_x = size_y = size_z = box_size
    halfsize = int(size / 2)

    # can only take 2 domains max rn, mostly testing
    if type(rad) == list:
        r1 = rad[0]
        r2 = rad[1]
        coordinates = [[], []]
    else:
        r1 = rad
        coordinates = []

    offset = (
        -r1 + 0.5
    )  # this +0.5 puts the center on a halfpoint and makes the generation match addas method

    # this isnt entirely correct because negative edge points and positive edge points are treated differently.
    # rounding problems

    # how do we deal with rounding? adda does something called volume correction
    # this has become a bit of a monster
    for x in range(size):
        for y in range(size):
            for z in range(size):
                # if multiple domains
                if type(rad) == list:
                    # first (smaller) domain
                    if (
                        np.sqrt(
                            (x + offset) ** 2 + (y + offset) ** 2 + (z + offset) ** 2
                        )
                        <= r2
                    ):
                        coordinate = f"{x} {y} {z}"
                        coordinates[0].append(coordinate)
                    # second (outer) domain
                    elif (
                        np.sqrt(
                            (x + offset) ** 2 + (y + offset) ** 2 + (z + offset) ** 2
                        )
                        <= r1
                    ):
                        coordinate = f"{x} {y} {z}"
                        coordinates[1].append(coordinate)
                # if one domain
                else:
                    if (
                        np.sqrt(
                            (x + offset) ** 2 + (y + offset) ** 2 + (z + offset) ** 2
                        )
                        <= r1
                    ):
                        coordinate = f"{x} {y} {z}"
                        coordinates.append(coordinate)

    return coordinates


coordinates = generate_coordinates(rad)
filename = write_shape_file(shape_name, coordinates, Ndom)
print("made shape file " + filename + ".geom")
