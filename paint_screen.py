"""
    This is a simple application for drawing on a canvas by
    tracking movement of a red ball using the web-cam
"""

import PySimpleGUI as sg
import numpy as np
import cv2
from tkinter import filedialog
from tkinter import Tk
import os


def info_box():
    """Funcion that opens an info window at the start"""
    layout = [[sg.Text('Use a red ball (other red objects may suffice too) to draw', text_color="BLACK",
                       background_color="WHITE")],
              [sg.Text('To change color or clear the canvas just move the object to the appropriate field',
                       text_color="BLACK", background_color="WHITE")],
              [sg.Text('Reqired: Enabled web-cam', text_color="RED", background_color="WHITE")],
              [sg.Button('Got it!', button_color=("white", "black"))]]
    window = sg.Window('Usage info', layout, disable_minimize=True, background_color="WHITE",
                       return_keyboard_events=True)
    event, values = window.read()
    # TODO x
    if event == 'Got it!':
        window.close()


def no_cam():
    """Funcion that opens the camera"""
    layout = [[sg.Text('ERROR: no camera found', text_color="RED", background_color="WHITE")],
              [sg.Button('OK', button_color=("white", "black"))]]
    window = sg.Window('Usage info', layout, disable_minimize=True, background_color="WHITE",
                       return_keyboard_events=True)
    event, values = window.read()
    if event == 'Got it!':
        window.close()
        exit(1)


def save_query(img):
    """Funcion that queries user if they want to save before exiting application"""
    layout = [[sg.Text('Save the drawing?', background_color="WHITE", text_color="BLACK")],
              [sg.Button('Save', button_color=("white", "black")), sg.Cancel(button_color=("white", "black"))]]
    query = sg.Window('Save', layout, location=(800, 400), disable_minimize=True, background_color="WHITE")
    event, values = query.read()
    if event == 'Save':
        query.close()
        file_save(img)


def file_save(img):
    """Function that saves the drawing to a specified location"""
    Tk().withdraw()
    f = filedialog.asksaveasfile(defaultextension=".jpg")
    # asksaveasfile return `None` if dialog closed with "cancel".
    if f is None:
        return
    cv2.imwrite(f.name, img)


if __name__ == '__main__':

    # Upper and lower limits for red
    redlower = np.array([0, 0, 153])
    redupper = np.array([120, 120, 255])

    # kernel for erosion and dilation
    kernel = np.ones((5, 5), np.uint8)

    # points of drawn lines
    points = [[] for i in range(11)]

    # the colors chart
    chart = cv2.imread(os.path.dirname(__file__) + "//pics//CHART_smol.png")

    # colors
    colors = (
        (0, 0, 255), (39, 127, 255), (0, 255, 255), (0, 255, 0), (76, 177, 34), (255, 194, 87), (255, 0, 0),
        (164, 73, 163),
        (201, 174, 255), (255, 255, 255), (0, 0, 0))

    # initial drawing color
    color_index = 0

    # blank painting initialisation
    paintWindow = np.zeros((480, 640, 3), np.uint8)

    # Display usage info
    info_box()

    # Create the window
    window = sg.Window('Air Canvas', [[sg.Image(filename='', key='real'), sg.Image(filename='', key='paintwindow')]],
                       location=(200, 200), background_color="BLACK")

    # Setup the web-cam as a capture device
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if cap is None or not cap.isOpened():
        no_cam()

    # Create background subtract-or
    fgbg = cv2.createBackgroundSubtractorMOG2()

    while True:

        # get events for the window with 20ms max wait
        # TODO:sho e ova
        event, values = window.Read(timeout=20, timeout_key='timeout')

        # read image from web-cam
        ret, real = cap.read()
        real = cv2.resize(real, (640, 480))

        # mirror the camera input
        real = cv2.flip(real, 1)

        # Isolate the moving parts
        fgmask = fgbg.apply(real)
        frame = cv2.bitwise_and(real, real, mask=fgmask)

        # Isolate the red colors
        reds = cv2.inRange(frame, redlower, redupper)
        frame = cv2.bitwise_and(frame, frame, mask=reds)

        # Perform closing to remove noise
        frame = cv2.erode(frame, kernel, iterations=3)
        frame = cv2.dilate(frame, kernel, iterations=7)

        # Find the contours in the modified image
        # TODO:oti onie params?
        cnts, _ = cv2.findContours(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

        # initialize center of detected object
        center = None

        # Proceed if contours have been found
        if len(cnts) > 0:
            # Sort the contours and find the largest one -- we assume it belongs to the tracked object
            cnt = sorted(cnts, key=cv2.contourArea, reverse=True)[0]

            # Get the radius of the enclosing circle around the found contour
            ((x, y), radius) = cv2.minEnclosingCircle(cnt)

            # Draw the circle around the contour
            cv2.circle(real, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            center = (int(x), int(y))

        # Is the menu touched?
        if center is not None:
            if 0 <= center[1] <= 50:
                index = int(center[0] / 50)
                if index >= 11:
                    points = [[] for i in range(11)]
                    paintWindow = np.zeros((480, 640, 3), np.uint8)
                else:
                    color_index = index

            points[color_index].append(center)

        # drawing so far
        for c in range(0, len(points)):
            if len(points[c]) != 0:
                for i in range(0, len(points[c]) - 2):
                    cv2.line(paintWindow, points[c][i], points[c][i + 1], colors[c], 2)
                    cv2.line(real, points[c][i], points[c][i + 1], colors[c], 2)

        # show the color chart
        for i in range(len(chart)):
            real[i] = chart[i]

        # if user closed window, quit
        if event == sg.WIN_CLOSED or event == 'Exit':
            save_query(paintWindow)
            break

        # update images in window
        window.FindElement('real').Update(
            data=cv2.imencode('.png', real)[1].tobytes())
        window.FindElement('paintwindow').Update(
            data=cv2.imencode('.png', paintWindow)[1].tobytes())

    cap.release()
