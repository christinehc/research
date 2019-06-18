# -*- coding: utf-8 -*-
"""
Created on Thu May 25 15:29:46 2017

@author: Christine
"""
# Imports
import numpy as np
import math


# Functions
def miller(pkarray = [], *arrays):

    # Check that input is as an array
    assert type(pkarray) != list, "Error: Input must be in list format."

    wavelength = 0.154059

    # Make min theta a global variable for calculations
    thetamin = pkarray[0] / 2
    sinthetaminsq = (np.sin(math.radians(thetamin)))**2

    # Create array for interatomic spacings
    ds = []

    # Create empty array for sin(theta)^2 ratios
    ratios = []

    # Find Miller indices for each peak in the given array
    for pk in pkarray:
         # Check that list elements are numbers
         try:
             pk = float(pk)
         except:
             print('Error: Input list must contain numerical peak values.')
             return
          theta = math.radians(pk / 2)
          sinthetasq = (np.sin(theta))**2
          d = wavelength / (2 * np.sin(theta))
          sqratio = sinthetasq / sinthetaminsq
#          print(sqratio)
          ratios.append(sqratio)
          ds.append(d)
#          print(ratios)
          # Convert 2theta to sin(theta)^2

     # Iterate until all ratios are approximately whole numbers
     loop = True
     count = 1
     while loop == True:
          for ratio in ratios:
               newratio = ratio * count
#               print(np.absolute(newratio - int(newratio)))
               if np.absolute(newratio - round(newratio)) > 0.4:
                    count += 1
#                    print(count)
                    break
          else:
               loop = False
#          print(count)
#     print(count)
     ratios = [count*ratio for ratio in ratios]
     ratios = [round(newratio) for newratio in ratios]
#     print(ratios)

     # Assume a = a for PEA
#     a = 3.25085

#     Ns = [(a/d)**2 for d in ds]

     print(ratios)
#     print(ds)
#     print(Ns)

     for ratio in ratios:
          hkl = [0,0,0]
          N = hkl[0]**2 + hkl[1]**2 + hkl[2]**2
          while N != ratio:


     print('hkl (in no particular order)')

#     for newratio in ratios:
#          hkl[0]
