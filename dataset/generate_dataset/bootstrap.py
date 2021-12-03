# Copyright 2019 Oliver Struckmeier
# Licensed under the GNU General Public License, version 3.0. See LICENSE for details

import random
from os import listdir

import numpy as np
from PIL import Image
from PIL import ImageFilter

####### Object Classes ####
# 2: Red Canon
# 1: Red Caster
# 0: Red Melee

####### Params ############
# Print out the status messages and where stuff is placed
verbose = False
# Important the leaf directories have to be called masked_champions, masked_minions, masked_towers or you have to change add_object to write the object classes properly
# Directory in which the masked minion images are located
masked_minions = "../src_data/masked_minions"
# Directory in which the map backgrounds are located
map_images_dir = "../src_data/map_screenshots"
# Directory in which the dataset will be stored (creates jpegs and labels subdirectory there)
# Attention if you use darknet to train: the structure has to be exactly as follows:
# - Dataset
# -- images
# --- XYZ0.jpg
# --- XYZ1.jpg
# -- labels
# --- XYZ0.txt
# --- XYZ1.txt
# -- train.txt
# -- test.txt
output_dir = "output"
# Prints a box around the placed object in red (for debug purposes)
print_box = True
# Size of the datasets the program should generate
dataset_size = 4500
# Beginning index for naming output files
start_index = 5548
# How many minons should be added minimum/maximum to each sample
minions_min = 1
minions_max = 10
assert (minions_min <= minions_max), "Error, minions_max needs to be larger than minions_min!"
# The scale factor of how much a champion image needs to be scaled to have a realistic size
scale_minions = 0.9
random_scale_minions = 0.25
# Random rotation maximum offset in counter-/clockwise direction
rotate = 10
# Output image size
output_size = (2560, 1440)
# Factor how close the objects should be clustered around the bias point larger->less clustered but also more out of the image bounds, value around 100 -> very clustered
bias_strength = 220  # 220 is good, dont select too large or the objects will be too often out of bounds
# Resampling method of the object scaling
# sampling_method = Image.BICUBIC
sampling_method = Image.BILINEAR  # IMO the best but use both to have more different methods
# Add random noise to pixels
noise = (0, 0, 0)
# Blur the image
blur = False
blur_strength = 1.4  # 0.6 is a good value
# Sometimes randomly add a cursor
cursors_min = 0
cursors_max = 0
assert (cursors_min <= cursors_max), "Error, cursors_max needs to be larger than cursors_min!"
cursor_scale = 0.40  # 0.45 seems good
cursor_random = 0.2
cursor_path = "../src_data/cursor"
# Padding for the bias point (to keep the clustering of the minions from spawning minions outside of the image
padding = 300  # 400 is good
########### Helper functions ###################
"""
This funciton applies random noise to the rgb values of a pixel (R,G,B)
"""


def apply_noise(pixel):
    R = max(0, min(255, pixel[0] + random.randint(-noise[0], noise[0])))
    G = max(0, min(255, pixel[1] + random.randint(-noise[1], noise[1])))
    B = max(0, min(255, pixel[2] + random.randint(-noise[2], noise[2])))
    A = pixel[3]
    return (R, G, B, A)


"""
This function places a masked image with a given path onto a map fragment
Passing -1 to the object class allows you to set objects like the UI that are not affected by rotations bias etc.
"""


def add_object(path, cur_image_path, object_class, bias_point, last):
    # Set up the map data
    map_image = Image.open(cur_image_path)
    map_image = map_image.convert("RGBA")
    # Cut the image to the desired output image size
    map_data = map_image.getdata()
    w, h = map_image.size
    if verbose:
        print("Adding object: ", path)
    # Read the image file of the current object to add
    obj = Image.open(path)
    if object_class >= 0:
        # Randomly rotate the image, but make the normal orientation most likely using a normal distribution
        obj = obj.rotate(np.random.normal(loc=0.0, scale=rotate), expand=True)
    obj = obj.convert("RGBA")
    obj_w, obj_h = obj.size
    # Rescale the image based on the scale factor
    if object_class == 0 or object_class == 1 or object_class == 2:  # red canon minion
        scale_factor = random.uniform(scale_minions - random_scale_minions, scale_minions + random_scale_minions)
        size = int(obj_w * scale_factor), int(obj_h * scale_factor)
    elif object_class == -1:  # Cursor
        scale_factor = random.uniform(cursor_scale - cursor_random, cursor_scale + cursor_random)
        size = int(obj_w * scale_factor), int(obj_h * scale_factor)
    else:
        size = int(obj_w), int(obj_h)

    # Compute the position of minions based on the bias point. Normally distribute the mininons around 
    # a central point to create clusters of objects for more realistic screenshot fakes
    # Champions and structures are uniformly distributed
    if object_class == -1:  # Champion or structure or cursor
        obj_pos_center = (random.randint(0, w - 1), random.randint(0, h - 1))
    else:
        x_coord = np.random.normal(loc=bias_point[0], scale=bias_strength)
        y_coord = np.random.normal(loc=bias_point[1], scale=bias_strength)
        obj_pos_center = (int(x_coord), int(y_coord))

    # Resize the image based on the scaling above
    obj = obj.resize(size, resample=sampling_method)
    obj_w, obj_h = obj.size

    if verbose:
        print("Placing at : {}|{}".format(obj_pos_center[0], obj_pos_center[1]))
    # Extract the image data
    obj_data = obj.getdata()
    out_data = np.array(map_image)
    last_pixel = 0
    # Compute the object corners
    min_x = int(min(w, max(0, obj_pos_center[0] - obj_w / 2 - 2)))
    max_x = int(min(w, max(0, obj_pos_center[0] + obj_w / 2 + 2)))
    min_y = int(min(h, max(0, obj_pos_center[1] - obj_h / 2 - 2)))
    max_y = int(min(h, max(0, obj_pos_center[1] + obj_h / 2 + 2)))
    # Place the images
    for y in range(min_y, max_y):
        for x in range(min_x, max_x):
            pixel = (0, 0, 0, 0)
            # Compute the pixel index in the map fragment
            map_index = x + w * y
            # print("x: ", x, " y: ", y)
            # If we want to print the box around the object, set the pixel to red
            if print_box is True and y == obj_pos_center[1] - int(obj_h / 2) and \
                    obj_pos_center[0] - int(obj_w / 2) < x < obj_pos_center[0] + int(obj_w / 2):
                pixel = (255, 0, 0, 255)
            elif print_box is True and y == obj_pos_center[1] + int(obj_h / 2) and \
                    obj_pos_center[0] - int(obj_w / 2) < x < obj_pos_center[0] + int(obj_w / 2):
                pixel = (255, 0, 0, 255)
            elif print_box is True and x == obj_pos_center[0] - int(obj_w / 2) and \
                    obj_pos_center[1] - int(obj_h / 2) < y < obj_pos_center[1] + int(obj_h / 2):
                pixel = (255, 0, 0, 255)
            elif print_box is True and x == obj_pos_center[0] + int(obj_w / 2) and \
                    obj_pos_center[1] - int(obj_h / 2) < y < obj_pos_center[1] + int(obj_h / 2):
                pixel = (255, 0, 0, 255)
            else:
                # Replace the old input image pixels with the object to add pixels
                if obj_pos_center[0] - int(obj_w / 2) <= x <= obj_pos_center[0] + int(obj_w / 2) \
                        and obj_pos_center[1] - int(obj_h / 2) <= y <= obj_pos_center[1] + int(obj_h / 2):
                    obj_x = x - obj_pos_center[0] - int(obj_w / 2) - 1
                    obj_y = y - obj_pos_center[1] - int(obj_h / 2) - 1
                    object_index = (obj_x + obj_w * obj_y)
                    # Check the alpha channel of the object to add
                    # If it is smaller 150, the pixel is invisible, 255: fully visible, 150: seethrough (brush simulation)
                    # Then use the original images pixel value
                    # Else use the object to adds pixel value
                    if obj_data[object_index][3] == 255:
                        pixel = (obj_data[object_index][0], obj_data[object_index][1], obj_data[object_index][2], 255)
                        last_pixel += 1
                    elif obj_data[object_index][3] == 0:
                        pixel = (map_data[map_index][0], map_data[map_index][1], map_data[map_index][2], 255)
                else:
                    pixel = (
                        map_data[map_index][0], map_data[map_index][1], map_data[map_index][2], map_data[map_index][3])
            out_data[y, x] = pixel
    if last and (noise[0] > 0 or noise[1] > 0 or noise[2] > 0):
        for y in range(0, h):
            for x in range(0, w):
                # Compute the pixel index in the map fragment
                map_index = x + w * y
                out_data[y, x] = apply_noise(out_data[y, x])
    # Save the image
    map_image = Image.fromarray(np.array(out_data))
    if blur and last:
        map_image = map_image.filter(ImageFilter.GaussianBlur(radius=blur_strength))
    map_image = map_image.convert("RGB")
    map_image.save(output_dir + "/images/" + filename + ".jpg", "JPEG")
    # Append the bounding box data to the labels file if the object class is not -1
    if object_class >= 0:
        with open(output_dir + "/labels/" + filename + ".txt", "a") as f:
            # Write the position of the object and its bounding box data to the labels file
            # All values are relative to the whole image size
            # Format: class, x_pos, y_pos, width, height
            f.write("" + str(object_class) + " " + str(float(obj_pos_center[0] / w)) + " " + str(
                float(obj_pos_center[1] / h)) + " " + str(float(obj_w / w)) + " " + str(float(obj_h / h)) + "\n")


########### Main function ######################
maps = sorted(listdir(map_images_dir))

for dataset in range(0, dataset_size):
    filename = str(dataset + start_index)
    print("Dataset: ", dataset, " / ", dataset_size, " : ", filename)
    # Randomly select a map background
    mp_fnam = map_images_dir + "/" + random.choice(maps)
    if verbose:
        print("Using map fragment: ", mp_fnam)

    # Randomly add 0-12 minions to the image
    # TODO change classification for blue and superminions
    minions = []
    for i in range(0, random.randint(minions_min, minions_max)):
        # Select a random subdirectory because the minions are sorted in subdirectories
        minions_dir = random.choice(sorted(listdir(masked_minions)))
        if minions_dir == "red_cannon":
            minions.append([masked_minions + "/" + minions_dir + "/" + random.choice(
                sorted(listdir(masked_minions + "/" + minions_dir))), 2])
        elif minions_dir == "red_caster":
            minions.append([masked_minions + "/" + minions_dir + "/" + random.choice(
                sorted(listdir(masked_minions + "/" + minions_dir))), 1])
        elif minions_dir == "red_melee":
            minions.append([masked_minions + "/" + minions_dir + "/" + random.choice(
                sorted(listdir(masked_minions + "/" + minions_dir))), 0])
        else:
            print("Error: This folder: ", minions_dir,
                  " was not specified to contain masked images. Skipping. Atention! Dataset might be broken!")
    if verbose:
        print("Adding {} minions!".format(len(minions)))

    # Now figure out the order in which we want to add the objects (So that sometimes objects will overlap)
    objects_to_add = minions
    random.shuffle(objects_to_add)
    # Read in the current map background as image
    map_image = Image.open(mp_fnam)
    w, h = map_image.size
    # Make sure the image is 1920x1080 (otherwise the overlay might not fit properly)
    assert (w == 2560 and h == 1440), "Error image has to be 2560x1440"

    map_image.save(output_dir + "/images/" + filename + ".jpg", "JPEG")
    cur_image_path = output_dir + "/images/" + filename + ".jpg"
    # Iterate through all objects in the order we want them to be added and add them to the backgroundl
    # Note this function also saves the image already
    # Point around which the objects will be clustered
    bias_point = (random.randint(padding, w - 1 - padding), random.randint(padding, h - 1 - padding))
    for i in range(0, len(objects_to_add)):
        o = objects_to_add.pop()
        if len(objects_to_add) == 0:
            add_object(o[0], cur_image_path, o[1], bias_point, True)  # Set last to true to apply the possible noise
        else:
            add_object(o[0], cur_image_path, o[1], bias_point, False)
    # Lastly add a cursor
    for i in range(cursors_min, random.randint(cursors_min, cursors_max)):
        cursor = cursor_path + "/" + random.choice(sorted(listdir(cursor_path)))
        add_object(cursor, cur_image_path, -1, bias_point, False)
        # If no objects were added we still have to create an empty txt file
    with open(output_dir + "/labels/" + filename + ".txt", "a") as f:
        f.write("")
    if verbose:
        print("=======================================")
