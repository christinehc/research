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
import numpy as np
import matplotlib.pyplot as plt

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
        intensities[k] = f"{(v / total) * 100:0.2f}%"
    return intensities

def calculate_p_deltas(fit):
    """Calculates the distance (in eV) between P(0) peak center and subsequent
    P peak centers.
    """
    pdict = {}
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    pks = int(len(fit.params) / 12)
    for i in range(pks)[1:]:
        pdict[f'a{alphabet[i]}_dist'] = f"{abs(fit.params[f'a1_center'].value - fit.params[f'{alphabet[i]}1_center'].value):0.2f} eV"
    return pdict

def full_xps_fit(file, sheet, peaks=3, name=False, skip=7, b=False, c=False, residuals=False):
    """
    Given a file path and desired prefix (for data naming scheme), performs the
    full gamut of XPS analyses on a P 2p XPS dataset, from calculating fits
    (based on pseudo-Voigt profiles) to generating a simple plot of the fitted
    data.

    Performs fittings to up to 5 separate P peaks, with initial guesses for the
    binding energies constrained as follows:
        a: initial guess for binding energy in the range of P(0) (~130 eV)
        b - e: initial guess for binding energy for oxidized P (~133-135 eV)
    The LMFIT package will use these initial guesses and iteratively find the
    "actual peaks" optimized according to least-squares fitting.

    (Note: in the following code, binding energies are shifted -10 eV
    relative to real values due to experimental setup (samples are run in the
    S-Probe as insulators, which adds a ~-10 eV shift to raw data).)

    Args:
        file: /path/to/file/containing/xps/data
        sheet: 'Sheet7' by default. Name of sheet (withinin Excel file), as a
            string, containing P 2p data.
        peaks: (optional) 3 by default. Number of peaks to fit.  Accepts any
            integer from 1 to 5.
        name: (optional) False by default. Accepts a string to be used to name
            output files. Saves output spectra as two files (./xpsfit/[name].pdf
            and ./xpsfit/[name].png, where "." is the directory containing the
            file specified above. If False, generates but does not save spectra.
        skip: (optional) skip=7 by default. Sets the number of rows in the
            XPS data Excel file to skip. Manually opening the file to determine
            the correct number of rows to skip may be necessary.
        b: (optional) False by default. Accepts a numeric value at which to fix
            the peak center of b.
        c: (optional) False by default. Accepts a numeric value at which to fix
            the peak center of c.
        residuals: (optional) False by default. Shows residuals plot if True.
    """
    # Load initial data
    data = read_xps_data_from_excel(file, sheet_name=sheet, skiprows=skip)

    # Sanity check(s)
    assert type(peaks) == int, "Error: peaks arg must be an integer."
    assert peaks <= 5 and peaks > 0, "Error: peaks arg must be between 1 and 5."

    # Default initial guesses for P peaks
    peak_be = [120.0, 123.0, 124.0, 124.5, 125.0]
    peak_height = [1.0, 0.1, 0.25, 0.2, 0.2]

    # Fit data
    fitoutput, model, parameters = xps_fit(data,
                                        peak_be[:peaks],
                                        peak_height[:peaks]
                                        )

    # Standardize all data such that the first peak (a) is centered at at 130 eV
    shift = 130 - fitoutput.params['a1_center'].value

    newdata = read_xps_data_from_excel(file,
                                    sheet_name=sheet,
                                    skiprows=skip,
                                    be_shift=shift
                                    )
    new_be = [(be + 10) for be in peak_be]
    newfitoutput, newmodel, newparameters = xps_fit(newdata,
                                                    new_be[:peaks],
                                                    peak_height[:peaks]
                                                    )

    # Constrain b and c
    if b:
        assert float(b), "Error: arg b must be either a numeric value or False."
        newfitoutput.params['b1_center'].set(b, vary=False)
    if c:
        assert float(b), "Error: arg c must be either a numeric value or False."
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

    # Print proportions and B.E. shifts
    print(f'Data for {name}', #small bug: outputs "Data for False" if no name
      f'Proportions are {calculate_component_percentages(newfitoutput)}',
      f'Distances are {calculate_p_deltas(newfitoutput)}',
      sep='\n')

    # Plot data
    if residuals:
        fig, axs = plt.subplots(2,
                                figsize=(8,6),
                                sharex=True,
                                gridspec_kw={'hspace': 0,
                                            'height_ratios': [1,2.5]
                                            }
                                )
        newfitoutput.plot_residuals(ax=axs[0])
        plot_xps_fit(newfitoutput, ax=axs[1], showallcomponents=True)

        # Hide x labels and tick labels for all but bottom plot.
        for ax in axs:
            ax.label_outer()
            ax.invert_xaxis()
            ax.set(title=None)
            if ax.get_legend():
                ax.get_legend().remove()

    elif not residuals:
        plt.figure(figsize=(8,4))
        plot_xps_fit(newfitoutput, showallcomponents=True)
        plt.gca().invert_xaxis()

    # Increasing default text label sizes
    plt.rcParams['xtick.labelsize']=12
    plt.rcParams['ytick.labelsize']=12
    plt.rcParams['axes.labelsize']=14

    if name:
        pathfolder = os.path.dirname(file)
        if not os.path.exists(f'{pathfolder}/xpsfit'):
            os.makedirs(f'{pathfolder}/xpsfit')
        plt.savefig(f"{pathfolder}/xpsfit/{name}.pdf",
                    bbox_inches='tight',
                    transparent=True)
        plt.savefig(f"{pathfolder}/xpsfit/{name}.png",
                    bbox_inches='tight',
                    transparent=True)

    plt.show()

    return
