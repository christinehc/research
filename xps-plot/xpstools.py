"""
tools.py
~~~~~~~~

Functions for fitting XPS P 2p spectrum outputs from the UW MAF SSI S-Probe.

Primarily written by W.H., with modifications by C.C.
"""

# Imports
from lmfit import models
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from operator import add
from functools import reduce


# Functions
def read_xps_data_from_excel(file, sheet_name, skiprows=7, be_shift=0):
    """Reads XPS data from Excel file outputs and returns data as a
    pandas dataframe.

    Args:
        file: name of Excel file (.xlsx)
        sheet_name: sheet (in Excel file) with P 2p or N 1s data
        skiprows:

    Returns:
        File information parsed into a pandas dataframe.

    Raises:
        'File does not match peak finding pattern Pk01, Pk02, ...,
            returning raw columns'
            Error message if the columns in the input file do not match
            expected columns.
    """
    raw = pd.read_excel(file, sheet_name=sheet_name, skiprows=skiprows)

    try:
        new = pd.DataFrame()
        new['BindingEnergy'] = raw['B. E.'] + be_shift
        new['Counts'] = raw['Counts']
        new['FitRegion_BindingEnergy'] = raw['PkGrp1_BE'] + be_shift
        new['FitBackground'] = raw['PkGrp1_Count']
        new['FitEnvelope'] = raw['PkFitEnv1']

        #Search for variable number of peaks
        peaki = 1
        while True:
            try:
                new['Peak{}'.format(peaki)] = raw['Pk0{}'.format(peaki)]
                peaki += 1
            except KeyError:
                break
    except KeyError:
        print('File does not match peak finding pattern Pk01, Pk02, ..., returning raw columns')
        new = pd.DataFrame()
        new['BindingEnergy'] = raw['B. E.'] + be_shift
        new['Counts'] = raw['Counts']
        for k in raw.keys():
            if k != 'B. E.' and k != 'Count':
                new[k] = raw[k]
    return new

def plot_xps_data_matplotlib(xpsdataframe, element='N', name=False):
    """Plots XPS data from an input pandas dataframe.

    Args:
        xpsdataframe: dataframe containing relevant XPS data
            (parsed using read_xps_data_from_excel)
        element: default is 'N'
            (string; accepts 'N' or 'P')
        name: default is False
    """
    colors = ['black', 'black', 'grey','fuchsia', 'blue', 'blue', 'lightblue']
    plt.scatter(xpsdataframe['BindingEnergy'], xpsdataframe['Counts'], s=5, c='black')

    x = xpsdataframe['FitRegion_BindingEnergy']
    colorcount = 0

    for k in xpsdataframe.keys()[3:]:
        plt.plot(x, xpsdataframe[k], label=k, color=colors[colorcount], alpha=0.8)
        colorcount += 1

    # Sets ranges depending on element
    if element == 'N':
        plt.xlim(392, 408)
        folder = 'N1s'
    elif element == 'P':
        plt.xlim(126, 137)
        folder = 'P2p'

    # Make tick labels larger
    plt.rcParams['xtick.labelsize']=12
    plt.rcParams['ytick.labelsize']=12
    plt.rcParams['axes.labelsize']=14

    plt.xlabel('Binding Energy (eV)')
    plt.ylabel('Intensity (a.u.)')
    plt.gca().invert_xaxis()

    # Option to save data
    if name and element=='N':
        plt.savefig(f"/mnt/c/Users/Christine/Documents/School/Work/Data/XPS/{folder}/{name}.pdf",
                    bbox_inches='tight', transparent=True)
        plt.savefig(f"/mnt/c/Users/Christine/Documents/School/Work/Data/XPS/{folder}/{name}.png",
                    bbox_inches='tight', transparent=True)

    plt.show()

def take_energy_range(energies, data, erange):
    indices = (energies >= erange[0]) & (energies <= erange[1])
    return np.array([energies[indices], data[indices]])

def get_background_subtracted_data(xpsdataframe):
    croppednans = xpsdataframe['FitRegion_BindingEnergy'][pd.notna(xpsdataframe['FitRegion_BindingEnergy'])]
    upper = croppednans.iloc[0]
    lower = croppednans.iloc[-1]
    energies, data = take_energy_range(xpsdataframe['BindingEnergy'], xpsdataframe['Counts'], [lower, upper])
    assert (energies - croppednans < 1e-10).all(), 'Energy grid of BindingEnergy and FitRegion_BindingEnergy did not match'
    new = {}
    new['BindingEnergy'] = energies
    new['Counts'] = data - xpsdataframe['FitBackground'][pd.notna(xpsdataframe['FitBackground'])]
    return pd.DataFrame(new)

def doublet_peakshape_model(mainpeakpos=120, gamma=0.15, sigma=0.35, splitting=-0.84, ratio=2, prefix='a'):
    """Makes lmfit model of doublet shape.

    Model is composed of two voigts with fixed Lorentzian
     and Gaussian widths and fixed splitting and peak ratios.

    Args:
        mainpeakpos: Energy (eV) position of main peak.
        gamma: Lorentzian width (in voigt model).
        sigma: Gaussian width (in voigt model).
        splitting: Energy gap (eV) between the two components
        ratio: Ratio of peak heights a1/a2

    Returns:
        lmfit model, lmfit pars

    Raises:
        Nothing.
    """
    prefix1 = prefix + '1_'
    prefix2 = prefix + '2_'
    mod = models.VoigtModel(prefix=prefix1)+models.VoigtModel(prefix=prefix2)
    pars = mod.make_params()
    parsdict = dict([[prefix2+'amplitude',{'expr': prefix1+'amplitude*'+str(1/ratio), 'value': 1/ratio, 'vary': False}],
                     [prefix2+'gamma', {'expr': prefix1+'gamma', 'value': gamma, 'vary': False}],
                     [prefix2+'center', {'expr': prefix1+'center-'+str(splitting), 'value': mainpeakpos-splitting, 'vary': False}],
                     #[prefix2+'fraction', {'expr': '', 'value': fraction, 'vary': False}],
                     [prefix1+'sigma', {'expr': '', 'value': sigma, 'vary': False}],
                     [prefix1+'gamma', {'expr': '', 'value': gamma, 'vary': False}],
                     [prefix1+'center', {'expr': '', 'value': mainpeakpos, 'vary': True}],
                     #[prefix1+'fraction', {'expr': '', 'value': fraction, 'vary': False}],
                     [prefix2+'sigma', {'expr': prefix1+'sigma', 'value': sigma, 'vary': False}]])
    for k,v in parsdict.items():
        pars[k].set(vary=v['vary'],expr=v['expr'])
    for k,v in parsdict.items():
        pars[k].value=v['value']
    return mod, pars

def multiple_doublet_model(centralenergies, relativeintensities):
    assert len(centralenergies) == len(relativeintensities), 'Intensities and energies must have same length.'
    models = []
    parslist = []
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    for i in range(len(centralenergies)):
        mod, pars = doublet_peakshape_model(centralenergies[i], prefix=alphabet[i])
        pars[alphabet[i]+'1_amplitude'].set(value=relativeintensities[i])
        models.append(mod)
        parslist.append(pars)
    totalmodel = reduce(add, models)
    totalpars = reduce(add, parslist)
    return totalmodel, totalpars

def xps_fit(xpsdataframe, centralenergies, relativeintensities):
    bgsub = get_background_subtracted_data(xpsdataframe)
    energies = bgsub['BindingEnergy']
    data = bgsub['Counts']
    mod, pars = multiple_doublet_model(centralenergies, relativeintensities)
    for k in pars.keys():
        if '1_amplitude' in k:
            pars[k].set(value=data.max() * pars[k].value)
    fit = mod.fit(data, params=pars, x=energies)
    return fit, mod, pars

def plot_xps_fit(fit, showallcomponents=False, ax=None):
    """User can specify axis.
    """
    x = fit.userkws['x']

    if ax == None:
        fig, ax = plt.subplots()

    ax.scatter(x, fit.data, label='Data', s=5, c='black')
    ax.plot(x, fit.eval(x=x), label='Fit', c='black')
    components = fit.eval_components(x=x)

    #colors = ['grey', 'blue', 'fuchsia', 'k']
    pkcolors = ['grey', 'grey', 'fuchsia', 'fuchsia', 'blue', 'blue', 'seagreen', 'seagreen', '#ceb301', '#ceb301']

    uniqueprefixes = sorted(list(set([s[:-2] for s in components.keys()])))
    colorcount = 0

    #for p in uniqueprefixes:
    #    ax.plot(x, components[p+'1_'] + components[p+'2_'], label=p, color=colors[colorcount], alpha=0.8)
    #    colorcount += 1

    ax.axhline(y=0, color='k', alpha=0.8)

    if showallcomponents:
        colorcount = 0
        for k, v in components.items():
            ax.plot(x, v, color=pkcolors[colorcount], alpha=0.9)
            #ax.fill_between(x, 0, v, color=pkcolors[colorcount], alpha=0.9)
            colorcount += 1

    #plt.legend()
    ax.set_xlim(126, 137)
    ax.set_xlabel('Binding Energy (eV)')
    #ax.invert_xaxis()
    ax.set_ylabel('Intensity (a.u.)')
    #plt.show()
