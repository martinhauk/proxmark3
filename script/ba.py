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

#region process utils

def send_command(process, command):
    process.stdin.write(command)
    process.stdin.flush()
    process.stdin.write(b"\n")
    process.stdin.flush()

#endregion

#region pm

def init_proxmark():
    with open("C:\\Users\\mah19\\tmp.txt", 'w') as file:
        pm = subprocess.Popen(["wsl"], stdin=PIPE, stdout=file)
        send_command(pm, b'cd ~/source/GITHUB/RfidResearchGroup/proxmark3 && pwd')
        send_command(pm, b'./pm3')
        time.sleep(5)
        return pm

def run_hf_reader(process):
    print("measuring...")
    send_command(process, b'hf 14a reader')
    time.sleep(16)

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
        
    printer.send_now("G90")# absolute coordinate mode
    
    printer.send_now("G28 Y") #home bed
    print("going home...")
    time.sleep(15) # wait for homing
    
    printer.send_now("G1 Y230") # go to most front position, should be closest to tag
    print("going to front...")
    time.sleep(5) #wait for going to front
    
    printer.send_now("G91") # relative coordinate mode
    return printer

def move(printer, i):
    printer.send_now('G1 Y-1')
    print("now on " + str(i) + "mm")

def cleanup_printer(printer):  
    printer.disconnect()

# endregion

#region file utils

def read_numbers_from_file():
    strippedLines = []
    with open("C:\\Users\\mah19\\tmp.txt", 'r') as text_file:
        lines = text_file.readlines()
        for line in lines:
            if "successes" in line:
                strippedLines.append(line[4:7])	        
    return strippedLines

def write_to_csv(values):
    csvStr = ",".join([str(v) for v in values])
    with open("C:\\Users\\mah19\\tmp.csv", 'a') as csv_file:
        csv_file.write(csvStr)
        csv_file.write("\r\n")
# endregion

printer = init_printer()
pm = init_proxmark()

start_distance = input("Enter initial distance in mm:")
end_distance = input("Enter end distance in mm:")

print("Starting measurements. Press Ctrl+C to stop...\r\n")

try:
    #initial scan
    run_hf_reader(pm)

    #now repeat as often as necessary
    for i in range(int(start_distance) + 1, int(end_distance) + 1, 1):
        move(printer, i)
        run_hf_reader(pm)
except KeyboardInterrupt:
    print('interrupted!')

print("Done, going to cleanup...")
cleanup_printer(printer)
cleanup_process(pm)

print("writing to file...")
headers = range(int(start_distance), int(end_distance) + 1, 1)
write_to_csv(headers)
numbers = read_numbers_from_file()
write_to_csv(numbers)