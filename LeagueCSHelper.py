from CSHelperUtils import *
import pygame
from ctypes import windll
from PIL import Image, ImageGrab
import numpy as np
from time import time
import torch
from argparse import ArgumentParser

if __name__ == '__main__':
    # Setup argument parser
    parser = ArgumentParser(description="League CS Helper")
    parser.add_argument("--print_times",
                        default=False,
                        action="store_true",
                        help="Prints how long each phase took in a frame")
    parser.add_argument("--debug_display",
                        default=False,
                        action="store_true",
                        help="Shows all minions regardless of HP")
    args = parser.parse_args()

    # Load data and overlay
    screen_width, screen_height, fps_cap, ad_bbox, ad_rect, \
        hp_lower, hp_upper, hp_bar_length, minion_thresholds, hp_search_padding = load_config()
    screen, hwnd = init_overlay(screen_width, screen_height)
    fps_clock = pygame.time.Clock()
    model = torch.hub.load('ultralytics/yolov5', 'custom', path="custom-weights/10kv2.pt")
    model.eval()

    ad = 50
    ad_check = 20
    i = 0

    while True:
        t = time()
        for event in pygame.event.get():
            windll.user32.SetFocus(hwnd)  # Brings window back to focus if any key or mouse button is pressed.

        # Take screenshot
        s = time()
        frame = ImageGrab.grab()
        frame_arr = np.array(frame)
        if args.print_times:
            print(f"Screenshot took: {time() - s}")

        # Run model on screenshot
        s = time()
        results = model(frame_arr)
        # results.print()
        all_detected_objs = results.xyxy[0].cpu().numpy()
        minion_pos_list = []
        for detected_obj in all_detected_objs:
            if detected_obj[4] > .6:
                w = detected_obj[2] - detected_obj[0]
                h = detected_obj[3] - detected_obj[1]
                minion_pos_list.append([detected_obj[0], detected_obj[1], w, h, int(detected_obj[5])])
        # print(found)
        if args.print_times:
            print(f"Model took: {time() - s}")

        # Determine if the found minions are below the threshold
        display_minions = []
        if args.debug_display:
            display_minions = minion_pos_list
        else:
            s = time()
            for minion_pos in minion_pos_list:
                if below_threshold(minion_pos, frame_arr, hp_search_padding,
                                   hp_lower, hp_upper, hp_bar_length, minion_thresholds):
                    display_minions.append(minion_pos)
            if args.print_times:
                print(f"Determining thresholds took: {time() - s}")

        # Check for AD
        """
        s = time()
        if i == ad_check:
            ad = read_numbers(frame, ad_bbox)
            i = 0
            if print_times:
                print(f"AD took: {time() - s}")
        else:
            i += 1
        if ad != -1:
            # print(ad)
            pass
        """

        # Draw the rectangles
        s = time()
        draw_rects(screen, display_minions, (0, 255, 0), 1)
        if args.print_times:
            print(f"Drawing took: {time() - s}")

        if args.print_times:
            print(f"Total time: {time() - t}")
            print("-"*30)
        fps_clock.tick(fps_cap)

