from CSHelperUtils import *
import pygame
from ctypes import windll
from PIL import Image, ImageGrab
import numpy as np
import time
import torch


if __name__ == '__main__':
    screen_width, screen_height, fps_cap, ad_bbox, ad_rect = load_config()
    screen, hwnd = init_overlay(screen_width, screen_height)
    fps_clock = pygame.time.Clock()

    model = torch.hub.load('ultralytics/yolov5', 'custom', path="custom-weights/10k.pt")

    while True:
        for event in pygame.event.get():
            windll.user32.SetFocus(hwnd)  # Brings window back to focus if any key or mouse button is pressed.

        frame = ImageGrab.grab()
        results = model(frame)
        results.print()
        pos = results.xywh[0].cpu().numpy()
        found = []
        for detected_obj in pos:
            if detected_obj[4] > .6:
                found.append(list(detected_obj[0:4]))
        print(found)
        ad = read_numbers(frame, ad_bbox)
        if ad != -1:
            # print(ad)
            pass
        # draw_rects(screen, [ad_rect], (0, 0, 255), 1)
        # draw_rects(screen, [[2560 / 2, 1440 / 2, 1, 30], [2560 / 2, 1440 / 2, 30, 1], [2560 / 2, 1440 / 2, -30, -1], [2560 / 2, 1440 / 2, -1, -30]], (255, 0, 0), 2)
        # draw_rects(screen, [[700, 400, 1150, 650]], (255, 0, 0), 1)
        draw_rects(screen, found, (0, 255, 0), 1)
        fps_clock.tick(fps_cap)


