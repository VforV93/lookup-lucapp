from answer_bot import solve_quiz, bcolors
import os
import modules.mydecorators as mydecorators
import modules.emulator as em
import win32.win32api as win32
import time


@mydecorators.timeit("main")
def main(snapper: em.Snapper):
    solve_quiz(snapper)
    snapper.store()


if __name__ == '__main__':
    os.system("adb devices")
    keypressed = input(bcolors.WARNING + '\nPress 1 to use ADB(Phone connected) or 2 with emulator or q to quit:\n' + bcolors.ENDC)
    if keypressed != 'q':
        try:
            snapper = em.getSnapperFactory(keypressed)
        except Exception as e:
            print(bcolors.FAIL + "\nUnknown input" + bcolors.ENDC)
            print(e)
            
        while True:
            keypressed = input(bcolors.WARNING + '\nPress s to screenshot live game or q to quit:\n' + bcolors.ENDC)
            if keypressed == 'c':
                em.get_cords()
            elif keypressed == 's':
                snapper.store()
                #snapper.screen()
                #main(snapper)
            elif keypressed == 'q':
                break
            else:
                print(bcolors.FAIL + "\nUnknown input" + bcolors.ENDC)
