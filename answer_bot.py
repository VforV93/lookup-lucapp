'''

	TODO:
	* Implement normalize func
	* Attempt to google wiki \"...\" part of question
	* Rid of common appearances in 3 options
	* Automate screenshot process
	* Implement Asynchio for concurrency

	//Script is in working condition at all times
	//TODO is for improving accuracy

'''

# answering bot for trivia HQ and Cash Show
import json
import urllib.request as urllib2
from bs4 import BeautifulSoup
from google import google
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import pyscreenshot as Imagegrab
import sys
# import wx
from halo import Halo


# for terminal colors 
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# sample questions from previous games
sample_questions = {}

# list of words to clean from the question during google search
remove_words = []

# negative words
negative_words = []

# GUI interface 
# def gui_interface():
# 	app = wx.App()
# 	frame = wx.Frame(None, -1, 'win.py')
# 	frame.SetDimensions(0,0,640,480)
# 	frame.Show()
# 	app.MainLoop()
# 	return None


def load_json():
    """ Loads a list of words to be removed and negative words from a json file to a variable.
    It loads also questions from the previous games.
    """
    global remove_words, sample_questions, negative_words
    remove_words = json.loads(open("Data/settings.json").read())["remove_words"]
    negative_words = json.loads(open("Data/settings.json").read())["negative_words"]
    sample_questions = json.loads(open("Data/questions.json").read())


def screen_grab(to_save):
    """ Takes a screenshot and saves it."""
    # 31,228 485,620 co-ords of screenshot// left side of screen
    im = Imagegrab.grab(bbox=(31,228,485,640))
    im.save(to_save)


def crop_image(path):
    image = cv2.imread(path)
    height, width = image.shape[:2]

    # # GETTING THE QUESTION
    # # Let's get the starting pixel coordiantes (top left of cropped top)
    # start_row, start_col = int(height * 23/100), int(0)
    # # Let's get the ending pixel coordinates (bottom right of cropped top)
    # end_row, end_col = int(height * 44/100), int(width)
    #
    # cropped_img = image[start_row:end_row, start_col:end_col]
    # cv2.imwrite("Screens/question.png", cropped_img)
    #
    # # GETTING ANSWER 1
    # start_row, start_col = int(height * 44/100), int(0)
    # end_row, end_col = int(height * 55/100), int(width)
    #
    # cropped_img = image[start_row:end_row, start_col:end_col]
    # cv2.imwrite("Screens/answer1.png", cropped_img)
    #
    # # GETTING ANSWER 2
    # start_row, start_col = int(height * 55 / 100), int(0)
    # end_row, end_col = int(height * 66 / 100), int(width) # + 11 from the top
    #
    # cropped_img = image[start_row:end_row, start_col:end_col]
    # cv2.imwrite("Screens/answer2.png", cropped_img)
    #
    # # GETTING ANSWER 3
    # start_row, start_col = int(height * 65 / 100), int(0)
    # end_row, end_col = int(height * 77 / 100), int(width)
    #
    # cropped_img = image[start_row:end_row, start_col:end_col]
    # cv2.imwrite("Screens/answer3.png", cropped_img)

    # GETTING THE QUESTION AND THE ASWERS
    # Let's get the starting pixel coordiantes (top left of cropped top)
    start_row, start_col = int(height * 23/100), int(0)
    # Let's get the ending pixel coordinates (bottom right of cropped top)
    end_row, end_col = int(height * 78/100), int(width)

    cropped_img = image[start_row:end_row, start_col:end_col]
    cv2.imwrite("Screens/cropped.png", cropped_img)

    return "Screens/cropped.png"


def apply_pytesseract(input_image):
    # prepare argparse
    ap = argparse.ArgumentParser(description='HQ_Bot')
    ap.add_argument("-i", "--image", required=False, default=input_image, help="path to input image to be OCR'd")
    ap.add_argument("-p", "--preprocess", type=str, default="thresh", help="type of preprocessing to be done")
    args = vars(ap.parse_args())

    # load the image
    image = cv2.imread(args["image"])
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if args["preprocess"] == "thresh":
        gray = cv2.threshold(gray, 0, 255,
                             cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    elif args["preprocess"] == "blur":
        gray = cv2.medianBlur(gray, 3)

    # store grayscale image as a temp file to apply OCR
    filename = "Screens/{}.png".format(os.getpid())
    cv2.imwrite(filename, gray)

    # load the image as a PIL/Pillow image, apply OCR, and then delete the temporary file
    text = pytesseract.image_to_string(Image.open(filename))
    # os.remove(filename)
    # os.remove(screenshot_file)

    return text

# get OCR text //questions and options
def read_screen():
    # spinner = Halo(text='Reading screen', spinner='bouncingBar')
    # spinner.start()
    print("Taking the screen shot....")
    screenshot_file = "Screens/to_ocr.png"
    #screen_grab(screenshot_file)

    # temporary file used for testing
    screenshot_file = "Screens/livequiz0.jpg"

    question_and_answers = crop_image(screenshot_file)
    text = apply_pytesseract(question_and_answers)
    print(text)

    # show the output images
    # cv2.imshow("Image", image)
    # cv2.imshow("Output", gray)
    # os.remove(screenshot_file)
    # if cv2.waitKey(0):
    #     cv2.destroyAllWindows()
    # print(text)

    # spinner.succeed()
    # spinner.stop()

    exit(0)  # TODO delete this
    return text


# get questions and options from OCR text
def parse_question():
    text = read_screen()
    lines = text.splitlines()
    question = ""
    options = list()
    flag=False

    for line in lines :
        if not flag :
            question=question+" "+line

        if '?' in line :
            flag=True
            continue

        if flag :
            if line != '' :
                options.append(line)

    return question, options

# simplify question and remove which,what....etc //question is string
def simplify_ques(question):
    neg=False
    qwords = question.lower().split()
    if [i for i in qwords if i in negative_words]:
        neg=True
    cleanwords = [word for word in qwords if word.lower() not in remove_words]
    temp = ' '.join(cleanwords)
    clean_question=""
    #remove ?
    for ch in temp:
        if ch!="?" or ch!="\"" or ch!="\'":
            clean_question=clean_question+ch

    return clean_question.lower(),neg


# get web page
def get_page(link):
    try:
        if link.find('mailto') != -1:
            return ''
        req = urllib2.Request(link, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'})
        html = urllib2.urlopen(req).read()
        return html
    except (urllib2.URLError, urllib2.HTTPError, ValueError) as e:
        return ''

# split the string
def split_string(source):
    splitlist = ",!-.;/?@ #"
    output = []
    atsplit = True
    for char in source:
        if char in splitlist:
            atsplit = True
        else:
            if atsplit:
                output.append(char)
                atsplit = False
            else:
                output[-1] = output[-1] + char
    return output

# normalize points // get rid of common appearances // "quote" wiki option + ques
def normalize():
    return None

# take screen shot of screen every 2 seconds and check for question
def check_screen():
    return None

# wait for certain milli seconds 
def wait(msec):
    return None

# answer by combining two words
def smart_answer(content,qwords):
    zipped= zip(qwords,qwords[1:])
    points=0
    for el in zipped :
        if content.count(el[0]+" "+el[1])!=0 :
            points+=1000
    return points

# use google to get wiki page
def google_wiki(sim_ques, options, neg):
    spinner = Halo(text='Googling and searching Wikipedia', spinner='dots2')
    spinner.start()
    num_pages = 1
    points = list()
    content = ""
    maxo=""
    maxp=-sys.maxsize
    words = split_string(sim_ques)
    for o in options:

        o = o.lower()
        original=o
        o += ' wiki'

        # get google search results for option + 'wiki'
        search_wiki = google.search(o, num_pages)

        link = search_wiki[0].link
        content = get_page(link)
        soup = BeautifulSoup(content,"lxml")
        page = soup.get_text().lower()

        temp=0

        for word in words:
            temp = temp + page.count(word)
        temp+=smart_answer(page, words)
        if neg:
            temp*=-1
        points.append(temp)
        if temp>maxp:
            maxp=temp
            maxo=original
    spinner.succeed()
    spinner.stop()
    return points,maxo


# return points for sample_questions
def get_points_sample():
    simq = ""
    x = 0
    for key in sample_questions:
        x = x + 1
        points = []
        simq,neg = simplify_ques(key)
        options = sample_questions[key]
        simq = simq.lower()
        maxo=""
        points, maxo = google_wiki(simq, options,neg)
        print("\n" + str(x) + ". " + bcolors.UNDERLINE + key + bcolors.ENDC + "\n")
        for point, option in zip(points, options):
            if maxo == option.lower():
                option=bcolors.OKGREEN+option+bcolors.ENDC
            print(option + " { points: " + bcolors.BOLD + str(point) + bcolors.ENDC + " }\n")


# return points for live game // by screenshot
def get_points_live():
    neg= False
    question,options=parse_question()
    simq = ""
    points = []
    simq, neg = simplify_ques(question)
    maxo=""
    m=1
    if neg:
        m=-1
    points,maxo = google_wiki(simq, options, neg)
    print("\n" + bcolors.UNDERLINE + question + bcolors.ENDC + "\n")
    for point, option in zip(points, options):
        if maxo == option.lower():
            option=bcolors.OKGREEN+option+bcolors.ENDC
        print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }\n")


# menu// main func
if __name__ == "__main__":
    load_json()
    while(1):
        keypressed = input(bcolors.WARNING +'\nPress s to screenshot live game, sampq to run against sample questions or q to quit:\n' + bcolors.ENDC)
        if keypressed == 's':
            get_points_live()
        elif keypressed == 'sampq':
            get_points_sample()
        elif keypressed == 'q':
            break
        else:
            print(bcolors.FAIL + "\nUnknown input" + bcolors.ENDC)
	

