
""" Takes a scrrenshot of the app and reads it.

This module uses pytesseract to read the question and the option.
The module functions require the path of the screenshot and the return the readed text.
"""

from PIL import Image
import pytesseract
import cv2
import os
import np
import modules.mydecorators as mydecorators

def show_img(title, img):
    """"Shows an image (Usefull for debugging)."""
    cv2.imshow(title, img)
    cv2.waitKey(2500)

    cv2.destroyAllWindows()


def get_question(image):
    """Reading the question and guessing the line number."""
    height, width = image.shape[:2]

    # The problem of this huge portion of code is that the question hasn't always the same lenght
    # Let's get the starting pixel coordiantes (top left of cropped top)
    start_row, start_col = int(height * 22 / 100), int(0)
    # Let's get the ending pixel coordinates (bottom right of cropped top)
    end_row, end_col = int(height * 38 / 100), int(width)

    cropped_img = image[start_row:end_row, start_col:end_col]
    cv2.imwrite("Screens/question.png", cropped_img)

    question = apply_pytesseract(cropped_img)
    question = question.splitlines()
    question = [x for x in question if x != '']
    linenumber = len(question)
    print("lines in the question: " + str(linenumber))

    # returning the question without \n
    return " ".join(question), linenumber


def get_option(image, lineno, index):
    """" Crops the image to get the interesting portion (that one with an option).

    The image cutting depends on the line number (lineno) of the question.
    This function just works for one option (depending on the index parameter).
    It will be called in parallel to process all the other options."""
    # this values derives from empirical tries
    # they refer to the end position of the question that depends on the lineno
    # for istance if the question has 2 lines, the options will start at crop_cropconfig[2-1]
    crop_config = [42 / 100, 44 / 100, 46 / 100]
    end_q = crop_config[lineno - 1] + (index - 1)*9/100

    height, width = image.shape[:2]

    start_row, start_col = int(height * end_q), int(width * 0.05)
    # they height of an option box is 5/100 of the entire image height (more or less).
    end_row, end_col = int(height * (end_q + 4 / 100)), int(width - (width * 0.05))

    cropped_img = image[start_row:end_row, start_col:end_col]
    #show_img("option" + index, cropped_img)
    imgpath = "Screens/answer" + str(index) + ".png"
    cv2.imwrite(imgpath, cropped_img)

    return cropped_img


def apply_pytesseract(image):
    """Convert the image to black and white and apply pytesseract to get the text"""

    # load the image
    #image = cv2.imread(input_image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    kernel = np.ones((1, 1), np.uint8)
    gray = cv2.dilate(gray, kernel, iterations=1)
    gray = cv2.erode(gray, kernel, iterations=1)

    gray_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    gray_blur = cv2.medianBlur(gray, 3)

    # store grayscale image as a temp file to apply OCR
    filename = "Screens/{}blur.png".format(os.getpid())
    cv2.imwrite(filename, gray_blur)

    # load the image as a PIL/Pillow image, apply OCR, and then delete the temporary file
    text = pytesseract.image_to_string(Image.open(filename))
    os.remove(filename)

    if not text:
        filename = "Screens/{}thresh.png".format(os.getpid())
        cv2.imwrite(filename, gray_thresh)

        # load the image as a PIL/Pillow image, apply OCR, and then delete the temporary file
        text = pytesseract.image_to_string(Image.open(filename))
        os.remove(filename)

    return text
