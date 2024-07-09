from subprocess import PIPE, Popen
import subprocess
import os
import time
import msvcrt
from printrun.printcore import printcore

#preconditions
# usb port connect von windows aus
# wsl usb port accept mit 2 befehlen 
# 

# GCode
# G90: absolute koordinaten, G91: relative Koordinaten ab aktueller Position
# M84: Motoren aus
# G0 Y1: Gehe zu position y0, andere achsen nicht ändern
# G28 Y: Home Y Achse (vgl. G0 Y0)

txt_location = "C:\\Users\\mah19\\OneDrive\\Desktop\\tmp.txt"
csv_location = "C:\\Users\\mah19\\OneDrive\\Desktop\\tmp.csv"
measure_duration = 12
pm_startup_duration = 3

#region process utils

def send_command(process, command):
    process.stdin.write(command)
    process.stdin.flush()
    process.stdin.write(b"\n")
    process.stdin.flush()

#endregion

#region pm

def init_proxmark():
    with open(txt_location, 'w') as file:
        pm = subprocess.Popen(["wsl"], stdin=PIPE, stdout=file)
        send_command(pm, b'cd ~/source/GITHUB/RfidResearchGroup/proxmark3 && pwd')
        send_command(pm, b'./pm3')
        time.sleep(pm_startup_duration)
        return pm

def run_hf_reader(process):
    print("measuring...")
    send_command(process, b'hf 14a reader')
    time.sleep(measure_duration)

def cleanup_process(process):
    send_command(process, b'exit')
    process.stdin.close()
    process.wait()

#endregion

# region printer

def init_printer():
    printer = printcore('COM7',250000)
    while not printer.online:
        time.sleep(0.1)
    
    printer.send_now("M84") #home bed
    input("Move bed to 0 and then press enter...")
    
    return printer

def move(printer, i):
    printer.send_now('G1 Y' + str(i))
    print("now on " + str(i) + "mm")

def cleanup_printer(printer):  
    printer.disconnect()

# endregion

#region file utils

def read_numbers_from_file():
    strippedLines = []
    with open(txt_location, 'r') as text_file:
        lines = text_file.readlines()
        for line in lines:
            if "successes" in line:
                strippedLines.append(line[4:7])	        
    return strippedLines

def write_to_csv(values):
    csvStr = ",".join([str(v) for v in values])
    with open(csv_location, 'a') as csv_file:
        csv_file.write(csvStr)
        csv_file.write("\r\n")
# endregion

pm = init_proxmark()
printer = init_printer()

start_distance = int(input("Ab wann interessanter Bereich:"))
end_distance = int(input("Bis wann interessanter Bereich:"))

print("Starting measurements. Press Ctrl+C to stop...\r\n")

try:
    #initial scan
    for i in range(start_distance, end_distance + 1, 1):
        move(printer, i)
        run_hf_reader(pm)
except KeyboardInterrupt:
    print('interrupted!')

print("Done, going to cleanup...")
cleanup_printer(printer)
cleanup_process(pm)

print("writing to file...")
headers = range(start_distance, end_distance + 1, 1)
write_to_csv(headers)
numbers = read_numbers_from_file()
write_to_csv(numbers)