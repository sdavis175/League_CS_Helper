import math
from configparser import ConfigParser
from ctypes import windll

import pygame
from pytesseract import pytesseract
from win32api import RGB
from win32con import HWND_TOPMOST, GWL_EXSTYLE, SWP_NOMOVE, SWP_NOSIZE, WS_EX_TRANSPARENT, LWA_COLORKEY, WS_EX_LAYERED
from win32gui import SetWindowLong, SetLayeredWindowAttributes, GetWindowLong

CONFIG_LOC = "config.ini"
transparent_color = '#000000'
pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
global rescale_w
global rescale_h


def read_numbers(screenshot, bbox):
    """
    Crops the screen and returns the integer from it.
    :param screenshot: PIL Image of the screen
    :param bbox: [x0, y0, x1, y1] of where to crop
    :return: Integer from captured area
    """
    crop = screenshot.crop(bbox)
    num_string = pytesseract.image_to_string(crop.convert("L"), lang='eng', config='digits')
    num_val = -1
    try:
        num_val = int(num_string)
    except ValueError:
        pass

    return num_val


def load_config():
    """
    Loads config.ini and returns all the constructed objects from it
    :return: All config values in their respective data structures
    """
    config = ConfigParser()
    config.read(CONFIG_LOC)
    settings = config["settings"]
    regions = config["regions"]
    hp_bar = config["hp_bar"]
    screen_width = int(settings["screen_width"])
    screen_height = int(settings["screen_height"])
    fps_cap = int(settings["fps_cap"])
    ad_x0 = float(regions["ad_x0"])
    ad_y0 = float(regions["ad_y0"])
    ad_w = float(regions["ad_w"])
    ad_h = float(regions["ad_h"])
    ui_0 = [int(regions["ui0_x0"]), int(regions["ui0_y0"]), int(regions["ui0_x1"]), int(regions["ui0_y1"])]
    ui_1 = [int(regions["ui1_x0"]), int(regions["ui1_y0"]), int(regions["ui1_x1"]), int(regions["ui1_y1"])]
    ui_list = [ui_0, ui_1]
    ad_bbox = [int(ad_x0 * screen_width), int(ad_y0 * screen_height),
               int(screen_width * (ad_w + ad_x0)), int(screen_height * (ad_h + ad_y0))]
    ad_rect = [int(ad_x0 * screen_width), int(ad_y0 * screen_height),
               int(ad_w * screen_width), int(ad_h * screen_height)]
    hp_lower = [int(hp_bar["hp_lower_r"]), int(hp_bar["hp_lower_g"]), int(hp_bar["hp_lower_b"])]
    hp_upper = [int(hp_bar["hp_upper_r"]), int(hp_bar["hp_upper_g"]), int(hp_bar["hp_upper_b"])]
    hp_bar_length = int(hp_bar["hp_bar_length"])
    minion_thresholds = [int(hp_bar["melee_threshold"]), int(hp_bar["caster_threshold"]),
                         int(hp_bar["cannon_threshold"])]
    hp_search_padding = int(hp_bar["hp_search_padding"])
    return screen_width, screen_height, fps_cap, ui_list, ad_bbox, ad_rect, hp_lower, hp_upper, hp_bar_length, \
           minion_thresholds, hp_search_padding


def init_overlay(screen_width, screen_height):
    """
    Initializes the pygame overlay to be transparent, always on top, and click-through-able
    :param screen_width: Screen width from config
    :param screen_height: Screen height from config
    :returns: pygame Screen and hwnd
    """
    global rescale_h, rescale_w
    # Mostly taken from https://github.com/LtqxWYEG/PoopStuckToYourMouse to make the overlay work as intended

    pygame.init()
    info = pygame.display.Info()  # get screen information like size, to set in pygame.display.set_mode
    rescale_w = info.current_w / screen_width
    rescale_h = info.current_h / screen_height
    setWindowPos = windll.user32.SetWindowPos  # see setWindowAttributes()
    flags = pygame.FULLSCREEN  # | pygame.DOUBLEBUF | pygame.HWSURFACE  # flags to set in pygame.display.set_mode
    transparentColorTuple = tuple(int(transparent_color.lstrip('#')[i:i + 2], 16) for i in (
        0, 2, 4))  # convert transparentColor to tuple for win32api.RGB(), to reduce hard-coded values. Thanks John1024
    screen = pygame.display.set_mode((info.current_w, info.current_h), flags,
                                     vsync=0,
                                     display=0)  # vsync only works with OPENGL flag, so far. Might change in the future
    screen.fill(transparent_color)  # fill with transparent color set in win32gui.SetLayeredWindowAttributes
    hwnd = pygame.display.get_wm_info()[
        'window']  # get window manager information about this pygame window, in order to address it in setWindowAttributes()
    setWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
    SetWindowLong(hwnd, GWL_EXSTYLE, GetWindowLong(hwnd, GWL_EXSTYLE) | WS_EX_TRANSPARENT | WS_EX_LAYERED)
    SetLayeredWindowAttributes(hwnd, RGB(*transparentColorTuple), 0, LWA_COLORKEY)
    windll.user32.SetFocus(hwnd)  # sets focus on pygame window
    # HWND_TOPMOST: Places the window above all non-topmost windows. The window maintains its topmost position even when it is deactivated. (Well, it SHOULD. But doesn't.)
    # It's not necessary to set the SWP_SHOWWINDOW flag.
    # SWP_NOMOVE: Retains the current position (ignores X and Y parameters).
    # SWP_NOSIZE: Retains the current size (ignores the cx and cy parameters).
    # GWL_EXSTYLE: Retrieve the extended window styles of the window.
    # WS_EX_TRANSPARENT: The window should not be painted until siblings beneath the window have been painted, making it transparent.
    # WS_EX_LAYERED: The window is a layered window, so that we can set attributes like color with SetLayeredWindowAttributes ...
    # LWA_COLORKEY: ... and make that color the transparent color of the window.
    return screen, hwnd


def draw_rects(screen, rects, rect_color, thickness, rescale=True):
    """
    Draws a list of rectangles to the screen
    :param screen: pygame Screen
    :param rects: List of rectangles defined as [x0, y0, width, height]
    :param rect_color: Color of the rectangles
    :param thickness: Thickness to draw the rectangles
    :param rescale: Rescale to fix Window's screen adjustment
    """
    # Clear pygame screen
    screen.fill(transparent_color)

    # Draw the rectangles
    for rect in rects:
        if rescale:
            pygame.draw.rect(screen, rect_color, pygame.Rect(rect[0] * rescale_w, rect[1] * rescale_h,
                                                             rect[2] * rescale_w, rect[3] * rescale_h), thickness)
        else:
            pygame.draw.rect(screen, rect_color, pygame.Rect(rect[0], rect[1], rect[2], rect[3]), thickness)

    pygame.display.update()


def is_hp(pixel, hp_lower, hp_upper):
    """
    Checks if a given pixel is within the color bounds of being an HP pixel
    :param pixel: [R, G, B] of the pixel
    :param hp_lower: From the config, [R, G, B] of the lower bounds for the HP pixel to check
    :param hp_upper: From the config, [R, G, B] of the upper bounds for the HP pixel to check
    :return: If the pixel is an HP pixel
    """
    return hp_lower[0] <= pixel[0] <= hp_upper[0] and \
           hp_lower[1] <= pixel[1] <= hp_upper[1] and \
           hp_lower[2] <= pixel[2] <= hp_upper[2]


def below_threshold(minion_pos, frame_arr, hp_search_padding, hp_lower, hp_upper, hp_bar_length, minion_thresholds):
    """
    Finds the minion's HP bar and checks if it is below it's threshold
    :param minion_pos: [x0, y0, w, h, label]
    :param frame_arr: Numpy array from the frame
    :param hp_search_padding: From the config, how large to make the search window from the minion's position
    :param hp_lower: From the config, [R, G, B] of the lower bounds for the HP pixel to check
    :param hp_upper: From the config, [R, G, B] of the upper bounds for the HP pixel to check
    :param hp_bar_length: From the config, pixel length of the HP bar
    :param minion_thresholds: From the config, [melee, caster, cannon] pixel values of when the player should attack it
    :return: If the minion's health is below the threshold (meaning the player should attack it)
    """
    try:
        # Create the padded search box to look for HP bars
        search_box = []
        if int(minion_pos[0]) > hp_search_padding:
            search_box.append(int(minion_pos[0]) - hp_search_padding)
        else:
            search_box.append(int(minion_pos[0]))
        if int(minion_pos[1]) > hp_search_padding:
            search_box.append(int(minion_pos[1]) - hp_search_padding)
        else:
            search_box.append(int(minion_pos[1]))
        if int(minion_pos[0] + minion_pos[2]) + hp_search_padding < frame_arr.shape[1] - 1:
            search_box.append(int(minion_pos[0] + minion_pos[2]) + hp_search_padding)
        else:
            search_box.append(int(minion_pos[0] + minion_pos[2]))
        search_box.append(int(minion_pos[1] + minion_pos[2] / 2))

        # Search for unique starting coordinates of HP bars (this will find the left-most pixel in it)
        found_hp_y_list = []
        found_hp_x_list = []
        half_hp_bar_length = int(hp_bar_length / 2)
        for y in range(search_box[1], search_box[3]):
            for x in range(search_box[0], search_box[2]):
                pixel = frame_arr[y][x]
                if is_hp(pixel, hp_lower, hp_upper) and y not in found_hp_y_list and x + half_hp_bar_length <= \
                        search_box[2]:
                    if x - 1 >= 0:
                        if not is_hp(frame_arr[y][x - 1], hp_lower, hp_upper):
                            found_hp_y_list.append(y)
                            found_hp_x_list.append(x)
                    else:
                        found_hp_y_list.append(y)
                        found_hp_x_list.append(x)

        if len(found_hp_y_list) == 0:
            raise Exception("Could not find HP!")

        # Determine starting pixel position in case their are multiple HP bars found
        if len(found_hp_y_list) > 1:
            # Find the closest HP bar to the center of the minion
            closest_to_center_index = -1
            closest_to_center_val = 10000
            minion_center_x = int(minion_pos[0] + minion_pos[2] / 2)
            for found_hp_index, found_hp_x in enumerate(found_hp_x_list):
                center = found_hp_x + half_hp_bar_length
                dx = abs(center - minion_center_x)
                dy = abs(found_hp_y_list[found_hp_index] - minion_pos[1])
                dist_to_minion = math.sqrt(dx ** 2 + dy ** 2)
                if dist_to_minion < closest_to_center_val:
                    closest_to_center_val = dist_to_minion
                    closest_to_center_index = found_hp_index
            starting_pixel = [found_hp_x_list[closest_to_center_index], found_hp_y_list[closest_to_center_index]]
        else:
            starting_pixel = [found_hp_x_list[0], found_hp_y_list[0]]

        # Count number of HP pixels from left to right
        hp_pixel_count = 0
        for _ in range(80):
            pixel = frame_arr[starting_pixel[1], starting_pixel[0]]
            if is_hp(pixel, hp_lower, hp_upper):
                hp_pixel_count += 1
                starting_pixel[0] += 1
            else:
                break

        # Check if the HP pixels are at or below threshold (means the player should attack minion)
        return hp_pixel_count <= minion_thresholds[minion_pos[4]]
    except Exception as e:
        print(e)
        return False


def in_ui(minion_pos, ui_list):
    """
    Checks if the minion's position is inside one of the UI positions
    :param minion_pos: [x0, y0, w, h] of minion
    :param ui_list: From the config, list of [x0, y0, x1, y1] positions of the UI elements on the screen
    :return: If the minion overlaps the UI or not
    """
    minion_x1 = minion_pos[0] + minion_pos[2]
    minion_y1 = minion_pos[1] + minion_pos[3]
    for ui_pos in ui_list:
        # https://stackoverflow.com/questions/40795709/checking-whether-two-rectangles-overlap-in-python-using-two-bottom-left-corners
        x_match = (ui_pos[0] < minion_pos[0] < ui_pos[2]) or (ui_pos[0] < minion_x1 < ui_pos[2])
        y_match = (ui_pos[1] < minion_pos[1] < ui_pos[3]) or (ui_pos[1] < minion_y1 < ui_pos[3])
        if x_match and y_match:
            return True
    return False
