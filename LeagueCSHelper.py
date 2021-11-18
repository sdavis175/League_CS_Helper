from utils import *
import pygame
from ctypes import windll
from PIL import Image, ImageGrab
import time

if __name__ == '__main__':
    screen_width, screen_height, fps_cap, ad_bbox, ad_rect = load_config()
    screen, hwnd = init_overlay(screen_width, screen_height)
    fps_clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            windll.user32.SetFocus(hwnd)  # Brings window back to focus if any key or mouse button is pressed.

        frame = ImageGrab.grab()
        ad = read_numbers(frame, ad_bbox)
        if ad != -1:
            print(ad)
        draw_rects(screen, [ad_rect], (255, 0, 0), 1)
        # draw_rects(screen, [[2560 / 2, 1440 / 2, 1, 30], [2560 / 2, 1440 / 2, 30, 1], [2560 / 2, 1440 / 2, -30, -1], [2560 / 2, 1440 / 2, -1, -30]], (255, 0, 0), 2)
        fps_clock.tick(fps_cap)
