# -*- coding: utf-8 -*-
"""
Created on Tue May 23 17:47:01 2017

@author: Christine
"""
# Imports
import matplotlib.pyplot as plt
import numpy as np
import xml.etree.ElementTree as etree


# Functions
def xrdoverlay():
#     print('Assume the directory path is \Data\XRD. \
#           Be sure to include the .xml suffix')
     #filename = input('Enter filename: ')
     #print(filename)

    filename0 = '20170519 - ThEA2PbI4 + A.xml'
    filename1 = '20170626 - ThEA2MA4Pb5I16.xml'
    filename2 = '20170626 - ThEA2MA9Pb10I31.xml'

    tree0 = etree.parse(filename0)
    tree1 = etree.parse(filename1)
    tree2 = etree.parse(filename2)

    root0 = tree0.getroot()
    root1 = tree1.getroot()
    root2 = tree2.getroot()

    # Create x arrays spanning the 2Theta range
#    x0 = np.arange(float(root0[0][2][0].text), \
#                   float(root0[0][2][1].text) + float(root0[0][2][2].text),\
#                   float(root0[0][2][2].text), dtype = None )
    x0 = np.arange(float(root0[0][2][0].text),
                float(root0[0][2][1].text) + float(root0[0][2][2].text),
                float(root0[0][2][2].text), dtype=None)
    x12 = np.arange(float(root1[0][2][0].text),
                float(root1[0][2][1].text) + float(root1[0][2][2].text),
                float(root1[0][2][2].text), dtype=None)

    # Create empty y arrays
    y0 = []
    y1 = []
    y2 = []

    data0 = root0[0][2][6].text
    data1 = root1[0][2][6].text
    data2 = root2[0][2][6].text

    # counting variable to eliminate extra data pts in graph0
    # (TEA control) from final figure
#    count = 1

    # Write data to the y arrays
    for data in data0.split():
        y0.append(float(data))
        # Since 5 + 0.03(100) = 8, to ignore
        # the extra leading data points, we need to discard
        # exactly 100 data points (i.e. 5, 5.03, ..., 7.99)
#        if count > 100 and count < 1502:
#           y0.append(float(data))
#        count += 1
    for data in data1.split():
        y1.append(float(data))
    for data in data2.split():
        y2.append(float(data))

#     print(len(y0))
#     print(len(y1))
    print(len(x0))

    plt.figure(1)
    plt.subplot(311)
    plt.plot(x0, y0, 'r', label='n = 40')
    plt.legend(loc='upper right')
    plt.xticks([10, 20, 30, 40, 50],[])
#    plt.title('XRD Spectra')

    plt.subplot(312)
    plt.plot(x12, y1, 'b', label='n = 60')
    plt.legend(loc='upper right')
    plt.ylabel('Intensity (counts)')
    plt.xticks([10, 20, 30, 40, 50],[])

    plt.subplot(313)
    plt.plot(x12, y2, 'k', label='n = ∞')
    plt.legend(loc='upper right')
    plt.show()

     # ∞
     # Create a plot with plot and axes labels
#     plt.plot(x1,y1)

#     plt.legend(loc = 'upper right')
    plt.xlabel('2θ (deg)')

# Run program
xrdoverlay()
