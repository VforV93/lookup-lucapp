from answer_bot import solve_quiz, bcolors
import os
import modules.emulator as em
import modules.mydecorators as mydecorators
import win32.win32api as win32
import time


@mydecorators.timeit("main")
def main(snapper: em.Snapper):
    try:
        if snapper.screen() >= 0:
            solve_quiz(snapper)
            #snapper.store()
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
            while True:
                keypressed = input(bcolors.WARNING + '\nPress s to screenshot live game or q to quit:\n' + bcolors.ENDC)
                if keypressed == 'c':
                    em.get_cords()
                elif keypressed == 's':
                    main(snapper)
                elif keypressed == 'q':
                    break
                else:
                    print(bcolors.FAIL + "\nUnknown input" + bcolors.ENDC)

        except Exception as e:
                    print(bcolors.FAIL + "\nUnknown input" + bcolors.ENDC)
                    print(e)