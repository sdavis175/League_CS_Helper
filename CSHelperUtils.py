from configparser import ConfigParser
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
    :return: Screen width, Screen height, bbox [x0, x1, y0, y1], rect [x0, y0, width, height]
    """
    config = ConfigParser()
    config.read(CONFIG_LOC)
    vals = config["vals"]
    screen_width = int(vals["screen_width"])
    screen_height = int(vals["screen_height"])
    fps_cap = int(vals["fps_cap"])
    ad_x0 = float(vals["ad_x0"])
    ad_y0 = float(vals["ad_y0"])
    ad_w = float(vals["ad_w"])
    ad_h = float(vals["ad_h"])
    bbox = [int(ad_x0 * screen_width), int(ad_y0 * screen_height),
            int(screen_width * (ad_w + ad_x0)), int(screen_height * (ad_h + ad_y0))]
    rect = [int(ad_x0 * screen_width), int(ad_y0 * screen_height),
            int(ad_w * screen_width), int(ad_h * screen_height)]
    return screen_width, screen_height, fps_cap, bbox, rect


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
    transparentColorTuple = tuple(int(transparent_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))  # convert transparentColor to tuple for win32api.RGB(), to reduce hard-coded values. Thanks John1024
    screen = pygame.display.set_mode((info.current_w, info.current_h), flags,
                                     vsync=0, display=0)  # vsync only works with OPENGL flag, so far. Might change in the future
    screen.fill(transparent_color)  # fill with transparent color set in win32gui.SetLayeredWindowAttributes
    hwnd = pygame.display.get_wm_info()['window']  # get window manager information about this pygame window, in order to address it in setWindowAttributes()
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
