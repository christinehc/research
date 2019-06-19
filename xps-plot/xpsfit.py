"""
xpsfit.py
~~~~~~~~~

Wrapper functions that fully automate the XPS P 2p fitting and plotting process
for data taken from SSI S-Probe data.

Note that as currently written, initial fits of the data (including baseline)
are required.  Working to remove this requirement in future versions.
"""

# Imports
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from lmfit import models
from operator import add
from functools import reduce

from xpstools import read_xps_data_from_excel, take_energy_range, \
                    get_background_subtracted_data, doublet_peakshape_model, \
                    multiple_doublet_model, xps_fit, plot_xps_fit


# Functions
def calculate_component_percentages(fit):
    """Calculates the relative percentages of each signal in the P 2p XPS
    spectrum according to XPS fit outputs.
    """
    components = fit.eval_components()
    uniqueprefixes = sorted(list(set([s[:-2] for s in components.keys()])))
    intensities = {}
    for p in uniqueprefixes:
        intensities[p] = np.sum(components[p+'1_'] + components[p+'2_'])
    total = np.sum(list(intensities.values()))
    for k, v in intensities.items():
        intensities[k] = v / total
    return intensities

def calculate_p_deltas(fit):
    """Calculates the distance (in eV) between P(0) peak center and subsequent
    P peak centers.
    """
    pdict = {}
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    pks = int(len(fit.params) / 12)
    for i in range(pks)[1:]:
        pdict[f'a{alphabet[i]}_dist'] = abs(
            fit.params[f'a1_center'].value - fit.params[f'{alphabet[i]}1_center'].value
        )
    return pdict

def full_xps_fit(file, sheet, name=False, skip=7, b=False, c=False, residuals=False):
    """
    Given a file path and desired prefix (for data naming scheme),
    performs the full gamut of XPS analyses on a P 2p XPS dataset,
    from calculating fits (based on Lorentzians) to generating a
    simple plot of the fitted data.

    Args:
        file: /path/to/file/containing/P2p/xps/data
        name: Name of output files (saves as both PDF and PNG).
              Does not save output files if False.
        b: (optional) If the middle
        c: (optional)
        residuals: (optional) Shows residuals plot.

    Returns:

    Raises:
    """
    # Load initial data
    data = read_xps_data_from_excel(file, sheet_name=sheet, skiprows=skip)
    pathfolder = os.path.dirname(file)
    fitoutput, model, parameters = xps_fit(data, [120.0, 123, 124.0], [1, 0.1, 0.25])

    # Standardize all data such that the first peak occurs at 130 eV
    shift = 130 - fitoutput.params['a1_center'].value
    newdata = read_xps_data_from_excel(file, sheet_name=sheet, skiprows=skip, be_shift=shift)
    newfitoutput, newmodel, newparameters = xps_fit(newdata, [130.0, 133.0, 134.0], [1, 0.1, 0.25])

    # Constrain b and c
    if b:
        newfitoutput.params['b1_center'].set(b, vary=False)
    if c:
        newfitoutput.params['c1_center'].set(c, vary=False)

    # Allow resolution to be unconstrained and rerun fit
    for k, v in newfitoutput.params.items():
        if 'gamma' in k:
            v.set(expr='a1_gamma')
        if 'sigma' in k:
            v.set(expr='a1_sigma')
    newfitoutput.params['a1_gamma'].set(vary=True)
    newfitoutput.params['a1_sigma'].set(vary=True)
    newfitoutput.fit()

    # Plot data
    print(f'Data for {name}',
      f'Proportions are {calculate_component_percentages(newfitoutput)}',
      f'Distances are {calculate_p_deltas(newfitoutput)}',
      sep='\n')

    if residuals:
        fig, axs = plt.subplots(2, figsize=(8,6), sharex=True, gridspec_kw={'hspace': 0, 'height_ratios': [1,2.5]})
        newfitoutput.plot_residuals(ax=axs[0])
        plot_xps_fit(newfitoutput, ax=axs[1], showallcomponents=True)

        # Hide x labels and tick labels for all but bottom plot.
        for ax in axs:
            ax.label_outer()
            ax.set(title=None)
            if ax.get_legend():
                ax.get_legend().remove()

    elif not residuals:
        plt.figure(figsize=(8,4))
        plot_xps_fit(newfitoutput, showallcomponents=True)

    plt.rcParams['xtick.labelsize']=12
    plt.rcParams['ytick.labelsize']=12
    plt.rcParams['axes.labelsize']=14

    if name:
        plt.savefig(f"{pathfolder}/xpsfit/{name}.pdf", bbox_inches='tight', transparent=True)
        plt.savefig(f"{pathfolder}/xpsfit/{name}.png", bbox_inches='tight', transparent=True)
    plt.show()

    return

def one_component_xps_fit(file, sheet, name=False, skip=7, residuals=False):
    """Same function as full_xps_fit, but with only 1 peak fitted to account
    for the control only having 1 component.

    Args:

        file: /path/to/file/containing/P2p/xps/data
        name: Name of output file (saves both) If False, does not save a new file.

    Returns:

    Raises:
    """
    # Load initial data
    data = read_xps_data_from_excel(file, sheet_name=sheet, skiprows=skip)
    pathfolder = os.path.dirname(file)
    fitoutput, model, parameters = xps_fit(data, [120.0], [1])

    # Standardize all data such that the first peak occurs at 130 eV
    shift = 130 - fitoutput.params['a1_center'].value
    newdata = read_xps_data_from_excel(file, sheet_name=sheet, skiprows=skip, be_shift=shift)
    newfitoutput, newmodel, newparameters = xps_fit(newdata, [130.0], [1])

    # Allow resolution to be unconstrained and rerun fit
    for k, v in newfitoutput.params.items():
        if 'gamma' in k:
            v.set(expr='a1_gamma')
        if 'sigma' in k:
            v.set(expr='a1_sigma')
    newfitoutput.params['a1_gamma'].set(vary=True)
    newfitoutput.params['a1_sigma'].set(vary=True)
    newfitoutput.fit()

    # Plot data
    print(f'Data for {name}')

    # Residuals plot
    if residuals:
        fig, axs = plt.subplots(2, figsize=(8,6), sharex=True, gridspec_kw={'hspace': 0, 'height_ratios': [1,2.5]})
        newfitoutput.plot_residuals(ax=axs[0])
        plot_xps_fit(newfitoutput, ax=axs[1], showallcomponents=True)

        # Hide x labels and tick labels for all but bottom plot.
        for ax in axs:
            ax.label_outer()
            ax.set(title=None)
            if ax.get_legend():
                ax.get_legend().remove()

    elif not residuals:
        plt.figure(figsize=(8,4))
        plot_xps_fit(newfitoutput, showallcomponents=True)

    plt.rcParams['xtick.labelsize']=12
    plt.rcParams['ytick.labelsize']=12
    plt.rcParams['axes.labelsize']=14

    if name:
        plt.savefig(f"{pathfolder}/xpsfit/{name}.pdf", bbox_inches='tight', transparent=True)
        plt.savefig(f"{pathfolder}/xpsfit/{name}.png", bbox_inches='tight', transparent=True)
    plt.show()

    return

def two_component_xps_fit(file, sheet, name=False, skip=7, residuals=False, skipshift=False):
    """
    Same function as full_xps_fit, but with only 2 peaks fitted to account
    for samples with only 2 components.

    INPUTS

    file:   file path
    name:   Name of data
    """
    # Load initial data
    data = read_xps_data_from_excel(file, sheet_name=sheet, skiprows=skip)
    pathfolder = os.path.dirname(file)
    fitoutput, model, parameters = xps_fit(data, [120.0, 123.0], [1, 0.1])

    # Standardize all data such that the first peak occurs at 130 eV
    if not skipshift:
        shift = 130 - fitoutput.params['a1_center'].value
        newdata = read_xps_data_from_excel(file, sheet_name=sheet, skiprows=skip, be_shift=shift)
        newfitoutput, newmodel, newparameters = xps_fit(newdata, [130.0, 133.0], [1, 0.1])

    # Calculate AB distance
    #ab_dist = abs(newfitoutput.params['a1_center'].value - newfitoutput.params['b1_center'].value)

    else:
        newdata = read_xps_data_from_excel(file, sheet_name=sheet, skiprows=skip, be_shift=9.6)
        newfitoutput, newmodel, newparameters = xps_fit(newdata, [130.0, 134, 135], [0.1, 1, 1])

        newfitoutput.params['a1_center'].set(130.0, vary=False)

        newfitoutput.fit()
        #print(newfitoutput.params['a1_center'].value)

    # Allow resolution to be unconstrained and rerun fit
    for k, v in newfitoutput.params.items():
        if 'gamma' in k:
            v.set(expr='a1_gamma')
        if 'sigma' in k:
            v.set(expr='a1_sigma')
    newfitoutput.params['a1_gamma'].set(vary=True)
    newfitoutput.params['a1_sigma'].set(vary=True)
    newfitoutput.fit()

    # Plot data
    print(f'Data for {name}',
          f'Proportions are {calculate_component_percentages(newfitoutput)}',
          f'Distances are {calculate_p_deltas(newfitoutput)}',
          sep='\n')

    if residuals:
        fig, axs = plt.subplots(2, figsize=(8,6), sharex=True, gridspec_kw={'hspace': 0, 'height_ratios': [1,2.5]})
        newfitoutput.plot_residuals(ax=axs[0])
        plot_xps_fit(newfitoutput, ax=axs[1], showallcomponents=True)

        # Hide x labels and tick labels for all but bottom plot.
        for ax in axs:
            ax.label_outer()
            ax.set(title=None)
            if ax.get_legend():
                ax.get_legend().remove()

    elif not residuals:
        plt.figure(figsize=(8,4))
        plot_xps_fit(newfitoutput, showallcomponents=True)

    plt.rcParams['xtick.labelsize']=12
    plt.rcParams['ytick.labelsize']=12
    plt.rcParams['axes.labelsize']=14

    if name:
        plt.savefig(f"{pathfolder}/xpsfit/{name}.pdf", bbox_inches='tight', transparent=True)
        plt.savefig(f"{pathfolder}/xpsfit/{name}.png", bbox_inches='tight', transparent=True)
    plt.show()

    return
