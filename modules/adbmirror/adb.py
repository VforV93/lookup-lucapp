import subprocess
from multiprocessing import Process

ADBBIN = 'adb.exe'

def save_to_file(result, as_str, out_file):
	stdout = result.stdout
	mode = 'w' if as_str else 'wb'
	with open(out_file, mode) as file:
		file.write(stdout)

def run_adb(arguments, clean=False, as_str=False, print_out=False, out_file=None):
	if type(arguments) == str:
		arguments = arguments.split(' ')
	result = subprocess.run([ADBBIN] + arguments, stdout=subprocess.PIPE)
	stdout = result.stdout
	if clean:
		stdout = stdout.replace(b'\r\n', b'\n')
	if as_str:
		stdout = stdout.decode("utf-8")
	if print_out:
		print(stdout)
	if out_file:
		proc = Process(target=save_to_file, args=(result, as_str, out_file))
		proc.run()
	return stdout

