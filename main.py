from answer_bot import solve_quiz, bcolors, AnswerBot
import os
import modules.emulator as em
import modules.mydecorators as mydecorators
import win32.win32api as win32
import time
from serpapi.google_search_results import GoogleSearchResults


@mydecorators.timeit("main")
def main(ansbot: AnswerBot):
    try:
        if snapper.screen(clean=False, as_str=False) >= 0:
            ansbot.solve_quiz()
            # ansbot._snapper.store()
            # TODO save the score/result to the questans.csv
        else:
            print(bcolors.FAIL + "Snapper.screen error during the screen acquisition" + bcolors.ENDC)
    except Exception as e:
        print(e) 


if __name__ == '__main__':
    os.system("adb devices")
    keypressed = ''
    while keypressed != 'q':
        keypressed = input(bcolors.WARNING + '\nPress 1 to use ADB(Phone/Emulator connected) or 2 to PCScreen capture or q to quit:\n' + bcolors.ENDC)
        try:
            snapper = em.getSnapperFactory(keypressed)
            ansbot = AnswerBot(snapper)
            while True:
                keypressed = input(bcolors.WARNING + '\nPress s to screenshot live game or q to quit:\n' + bcolors.ENDC)
                if keypressed == 'c':
                    em.get_cords()
                elif keypressed == 's':
                    main(ansbot)
                elif keypressed == 'q':
                    break
                else:
                    print(bcolors.FAIL + "\nUnknown input" + bcolors.ENDC)
        except Exception as e:
                    print(bcolors.FAIL + "\nUnknown input" + bcolors.ENDC)
                    print(e)