# -*- coding: utf-8 -*-
"""
Created on Sat May 20 14:11:03 2017

@author: Christine
"""
import matplotlib.pyplot as plt, \
       numpy, \
       xml.etree.ElementTree as etree

def xrdxmlplot():
#     print('Assume the directory path is \Data\XRD. \
#           Be sure to include the .xml suffix')
     #filename = input('Enter filename: ')
     #print(filename)
          
     
     filename = '20170615 - ThEA2MA59Pb60I181.xml'
     tree = etree.parse(filename)
     root = tree.getroot()
     
     # Create empty y array
     y = []
     data = root[0][2][6].text
     
     # Write data to the y array
     for datapoint in data.split():
          y.append(float(datapoint))
          
     # Create x array spanning the 2Theta range
     x = numpy.arange(8,50.035,0.035,dtype = None)
     
     # Create a plot with plot and axes labels
     plt.plot(x,y)
     plt.title('XRD Spectrum')
     plt.ylabel('Intensity (counts)')
     plt.xlabel('2θ (deg)')
          
#     print(y)
     
#     print(root[0][2][6].tag)
#     print(root[0][2][6].text)

#     for datapoint in data.split():
#          print(datapoint)
          
     #for data in root.findall('.//Pattern/ScanTrace/Data', namespaces = None):
      #    print (data)
     
          #for num in ThEAData.findall('.Pattern/ScanTrace/Data'):
          #     y.append(num)
     
         # print(y) 

     #print (x)
     #y = xmlAttr.getContent,ctxt.xpathEval('//MDI date/diagram/point/@totaldensity')
     
# Run program
xrdxmlplot()