
""" Takes the screenshot and tries to guess the answer.

Each option is red and searched in parallel.
"""

from multiprocessing import Process, Manager
from modules.imgtotext import *
import numpy as np
from modules.gsearch import *
from threading import Thread
import modules.emulator as em
from operator import itemgetter



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

def get_and_search_option(i, image, question, lineno, negative_question, return_dict):
    """Taking the screenshot and the parsed question this function read one option and search it.

    This function will be called in parallel so that the option detection and the searching is faster."""

    optionimg = get_option(image, lineno, i)
    option = apply_pytesseract(optionimg)

    if option == '':
        points = 0
    else:
        points = google_wiki(question, option, negative_question)
        #searcher.search(question, option, negative_question) #google_wiki(question, option, negative_question)
    
    print("{}-{}-{}".format(option,i,tuple(points)))
    return_dict[option] = (option,i,tuple(points))


class AnswerBot(object):
    def __init__(self, snapper):
        self._snapper  = snapper
        self._manager  = Manager()

    @mydecorators.handle_exceptions
    def solve_quiz(self):
        
        """Given a path to a valid screenshot it tries to solve the quiz in parallel."""
        question, lineno = get_question(self._snapper._image)
        #simpler_question is an object of type ParsedQuestion
        simpler_question, negative_question = simplify_ques_fy2(question)

        # if the answer is negative the results are resversed we check for that one with less matches
        points_coeff = 1
        if negative_question:
            points_coeff = -1

        return_dict = self._manager.dict()

        tasks = []
        for i in [1, 2, 3]:
            # searching in parallel
            proc = Process(target=get_and_search_option, args=(i, self._snapper._image, simpler_question, lineno, negative_question, return_dict))
            proc.start()
            tasks.append(proc)
            #get_and_search_option(i, self._snapper.screenpath(), simpler_question, lineno, negative_question, return_dict)

        for t in tasks:
            t.join()

        ris_vals = sorted(return_dict.values(),key=itemgetter(1))
        
        points_wiki = [ris_vals[0][2][0],ris_vals[1][2][0],ris_vals[2][2][0]]
        points = points_wiki.copy()

        points_gres = [ris_vals[0][2][1],ris_vals[1][2][1],ris_vals[2][2][1]]
        totgres = 0
        for i in range(3):
            if points_gres[i] > 0:
                totgres += points_gres[i]
            if points[i] < 0:
                points[i] = 0

        for i,p in enumerate(points_wiki):
            if p >= 0:
                if points_gres[i] > 0:
                    points[i] += int(100*(points_gres[i]/totgres))
                
                points[i] *= points_coeff
        
        # taking the max match value
        max_point = max(points)
        print("\n" + bcolors.UNDERLINE + question + bcolors.ENDC + "\n")
        return_option = ""

        for i,v in enumerate(points):
            r_opt = ris_vals[i][0]
            if max_point == v:
                return_option = ris_vals[i][0]
                r_opt = bcolors.OKGREEN + return_option + bcolors.ENDC

            print(r_opt + " { points: " + bcolors.BOLD + str(v) + bcolors.ENDC + " }\n")
        print("---------------------------------------")
        return return_option

@mydecorators.handle_exceptions
def solve_quiz(snapper):
    """Given a path to a valid screenshot it tries to solve the quiz in parallel."""
    question, lineno = get_question(snapper.screenpath())
    #simpler_question is an object of type ParsedQuestion
    simpler_question, negative_question = simplify_ques_fy2(question)

    # if the answer is negative the results are resversed we check for that one with less matches
    points_coeff = 1
    if negative_question:
        points_coeff = -1

    manager = Manager()
    return_dict = manager.dict()

    tasks = []
    for i in [1, 2, 3]:
        # searching in parallel
        proc = Process(target=get_and_search_option, args=(i, snapper.screenpath(), simpler_question, lineno, negative_question, return_dict))
        proc.start()
        tasks.append(proc)
        #get_and_search_option(i, snapper.screenpath(), simpler_question, lineno, negative_question, return_dict)

    for t in tasks:
        t.join()

    ris_vals = sorted(return_dict.values(),key=itemgetter(1))
    points = [ris_vals[0][2],ris_vals[1][2],ris_vals[2][2]]

    # taking the max match value
    max_point = max(points)
    print("\n" + bcolors.UNDERLINE + question + bcolors.ENDC + "\n")
    return_option = ""
    for r_opt,r_i,r_p in ris_vals:
        if max_point == r_p:
            return_option = r_opt
            # if this is the "correct" answer it will appear green
            r_opt = bcolors.OKGREEN + r_opt + bcolors.ENDC

        print(r_opt + " { points: " + bcolors.BOLD + str(r_p) + bcolors.ENDC + " }\n")

    print("---------------------------------------")
    return return_option

# Debugging
if __name__ == '__main__':
    #question, lineno = "In quale di queste serie TV ha recitato Will Smith", 3
    #option = ["The Crown","Lost","Willy, il principe di Bel-Air"]
    #question, lineno = "Indica il film in cui il protagonista appare con uno stuzzicadenti", 3
    #option = ["Scusa ma ti chiamo amore","Quo vado?","Johnny Stecchino"]
    #question, lineno = "Dove ha avuto origine la cerimonia del tè", 3
    #option = ["Islanda","Nuova Zelanda","Cina"]
    #question, lineno = "Indica un motore di ricerca di letteratura accademica", 3
    #option = ["Blackboard","Google Scholar","Google Classroom"]
    #question, lineno = "Qual è la corsa ciclistica più lunga tra queste", 3
    #option = ["Tour de France","Cape Town Cycle Tour","Giro d'Italia"]
    question, lineno = "Chi dei seguenti NON è un nano di \"Biancaneve\"", 3
    option = ["Brontolo","Fabbolo","Peppa"]
    #question, lineno = get_question("Screens/screen.png")
    #for i in range(3):
    #    get_option("Screens/screen.png", lineno, i+1)
    #    option.append(apply_pytesseract(get_option("Screens/screen.png", lineno, i+1)))
    simpler_question, negative_question = simplify_ques_fy2(question)

    points_coeff = 1
    if negative_question:
        points_coeff = -1

    manager = Manager()
    return_dict = manager.dict()
    points = []

    for i in [1, 2, 3]:
        pts = google_wiki(simpler_question, option[i-1], negative_question)
        points.append(pts)
    
    max_point = max(points)
    print("\n" + question + "\n")
    r_opt = ''
    for i, r_p in enumerate(points):
        print(option[i] + " { points: " + str(r_p) + " }\n")

    print("---------------------------------------")
