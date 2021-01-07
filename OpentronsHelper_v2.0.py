import tkinter as tk
from tkinter import filedialog
import csv
import ScriptMaker_v2

def createScript():  
    global user_input

    #print("making script with " + str(user_input[0][0:4]) + " and sample in " + sampleStart.get())
    ScriptMaker_v2.createScript(user_input, sampleStart.get(), temperature.get())
    
def extractCSV():
    csvFile = filedialog.askopenfilename()
    global user_input
    #usr_input-stores data from csv
    for i in range(3):
        user_input.append([])
    with open(csvFile, newline='') as csvfile:
        csvInput= csv.reader(csvfile, delimiter=' ', quotechar='|')
        for row in csvInput:
            for data in row:
                helperData = data.split(",")
                for num in range(len(helperData)):
                    if helperData[num] != '':
                        user_input[num].append(helperData[num])
                    elif helperData[num] == '':
                        user_input[num].append(0)

global user_input
user_input = []
root = tk.Tk()
frame1= tk.Frame(master=root)
lbl_csv = tk.Label(master= frame1, text="Import a CSV: Col 1: uL of Water per well, Col 2 (optional): uL of Sample per well, Col 3 (optional): number of 1:10 dilutions")
button = tk.Button(master= frame1, text='Select CSV', command=extractCSV)
lbl_csv.pack()
button.pack()

lbl_sample = tk.Label(master=frame1, text="What is your is your sample in?")
lbl_sample.pack()

sampleStart = tk.StringVar(frame1)
sampleOptions = ["96 well plate", "1.5mL Tubes"]
for text in sampleOptions:
    tk.Radiobutton(frame1, text=text, variable=sampleStart, value=text).pack()

lbl_temp = tk.Label(frame1, text="Do you want temp block on at 4C?")
lbl_temp.pack()

temperature = tk.StringVar(frame1)
tempOptions = ["yes", "no"]
for text in tempOptions:
    tk.Radiobutton(frame1, text=text, variable=temperature, value=text).pack()

button2 = tk.Button(master=frame1, text="Create Script", command=createScript)
button2.pack()
frame1.pack()
root.mainloop()