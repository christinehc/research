# -*- coding: utf-8 -*-
"""
Created on Wed May 24 17:31:57 2017

@author: Christine
"""
# Imports
import numpy as np
import xml.etree.ElementTree as etree


# Upon F5, run program on a loop until user terminates
loop = True


# Instructions
print('Note that the default directory path is C:\...\Data\XRD\.')
print('Do not include the .xml suffix in your entry.')
print('If you are done entering filenames, leave the entry blank')
print('and press ENTER to terminate the program.')


# Functions
def xrd2theta(*args):
    """Identifies XRD peaks given data in XML format.

    Args:
        Array(s) representing range(s) of 2theta in which a peak or peaks exist(s)

    Returns:
    Precise 2theta at which the peak occurs
    """
    # Check that inputs are 1D arrays with 2 elements (i.e. (x,y))
    for arg in args:
        if type(arg) == list:
            # Terminate function if 1D array but not with 2 elements
            if len(arg) != 2:
                print('Error: Must enter each argument as \
                    a range (or list of ranges) for 2theta,\
                    e.g. type([2theta min, max2theta],etc.)')
                return
        # Terminate function if input is not 1D array
        else:
             print('Error: Must enter each argument as \
                a range (or list of ranges) for 2theta,\
                e.g. type([2theta min, max2theta],etc.)')
             return

    # User input
    filename = input('Enter filename (XML format): ') + '.xml'

    # If user input is blank, terminate program loop
    if len(filename) == 4:
        global loop
        loop = False
        print('Program terminated.')
        return

#    print(filename)
#    filename = '20170510 - TEA2PbI4 - control.xml'

    # Read XML file
    tree = etree.parse(filename)
    root = tree.getroot()

    #root[0][2][0].text
    #print(isinstance(root[0][2][0].text,str))

    # Create x arrays spanning the 2Theta range
    x = np.arange(float(root[0][2][0].text), \
               float(root[0][2][1].text) + float(root[0][2][2].text),\
               float(root[0][2][2].text), dtype = None )

#    print(x)

    # Create empty y array
    y = []

    # Create empty array of all peaks
    pkarray = []

    data = root[0][2][6].text

    # Write data to the y arrays
    for data in data.split():
        y.append(float(data))

    for arg in args:
        indices = np.where((x > arg[0]) & (x < arg[1]))
        minindex = indices[0][0]
        maxindex = indices[0][len(indices[0]) - 1]
        pkindex = np.where(y == np.amax(y[minindex:maxindex]))
        if np.amax(y[minindex:maxindex]) > 1000:
            print(f'2Theta peak for range {arg} is {x[pkindex][0]}')
            pkarray.append(x[pkindex][0])
        else:
            print(f'2Theta peak for range {arg} does not exist.')
    print('2Theta peak summary is listed below:')
    print(pkarray)


# Run program
#xrd2theta()
while loop == True:
    xrd2theta([10,15],[15,20],[20,25],[25,30],[30,39],[39,45],[45,50])
