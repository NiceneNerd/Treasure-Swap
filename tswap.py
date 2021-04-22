import argparse
import oead
import sys
import os

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

mu = oead.byml.from_binary(oead.yaz0.decompress(open(resource_path("boxes.sbyml"), "rb").read()))

from tkinter import *
  
root = Tk()
a = Label(root, text ="Hello World")
a.pack()
  
root.mainloop()

