<h1 align="center">fmri 2 mat</h1>

<p align="center">
  Nuisance-regresses fMRIPrep BOLD data with its confounds and extracts mean time series for each region of a volumetric parcellation using nilearn.
</p>

<p align="center">
  <a href="https://github.com/brainlife/abcd-spec"><img src="https://img.shields.io/badge/ABCD_Spec-v1.1-green.svg" alt="ABCD Spec v1.1"></a>
  <a href="https://doi.org/10.25663/brainlife.app.369"><img src="https://img.shields.io/badge/Brainlife-brainlife.app.369-blue.svg" alt="Run on brainlife.io"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-see_LICENSE-lightgrey.svg" alt="License"></a>
</p>

## At a glance

<!-- brainlife-app:begin (generated from the App manifest; edit the manifest, not this block) -->

> **Nuisance-regresses fMRIPrep BOLD data with its confounds and extracts mean time series for each region of a volumetric parcellation using nilearn.**

Runs nilearn-based nuisance regression on a preprocessed BOLD image using the fMRIPrep confounds file (strategy, band-pass filter, smoothing and spike regression are configurable), then extracts the mean time series of every parcel. Use it after fMRIPrep to get denoised BOLD and regional time series for connectivity analysis. The BOLD image, mask and parcellation must be aligned (same space); if tr is empty the TR is read from the BOLD metadata. Leave inspace at data: the code accepts only 'data' or 'labels', so the 'label' option fails.

| | |
|---|---|
| **Inputs** | `neuro/func/task` · `neuro/parcellation/volume` · `neuro/regressors` · `neuro/mask` |
| **Outputs** | `neuro/func/task` · `generic/timeseries` |
| **Container** | `faskowit/app-fmri-2-mat:brnch-0.1.6` |
| **Resources** | 1 CPUs · 0.5 h walltime |
| **Run it** | [doi.org/10.25663/brainlife.app.369](https://doi.org/10.25663/brainlife.app.369) |

#### Inputs

| Input | Datatype | Required | Description |
|---|---|---|---|
| `fmri` | `neuro/func/task` | yes | from fMRIPrep |
| `parc` | `neuro/parcellation/volume` | yes | From multi-atlas transfer app; should be aligned to preprocessed bold.nii.gz (i.e. same space). The internal functions of this app will re-slice the func and the parc to be on the same voxel grid. |
| `confounds` | `neuro/regressors` | yes | from fMRIPrep |
| `mask` | `neuro/mask` (func) | yes | from fMRIPrep |

#### Outputs

| Output | Datatype | Description |
|---|---|---|
| `output_regress` | `neuro/func/task` | regressed output bold |
| `out_ts` | `generic/timeseries` | new timeseries datatype |

<details>
<summary><b>Parameters</b> (10)</summary>

| Parameter | Type | Default | Description |
|---|---|---|---|
| `strategy` | enum | `36P` | Strategy of nuisance regression, all strategies include linear de-trending Options: `36P`, `24aCompCor`, `globalsig`, `linear`, `24aCompCorGsr`. |
| `tr` | number |  | If you know the TR, you can set it here. Script will also try to automatically read it from BL info (try this first). |
| `smoothfwhm` | number | `0` | FWHM of spatial smoothing kernel applied to bold.nii.gz (put 0 for no smoothing) |
| `lowpass` | number | `0.08` | Low-pass temporal filter |
| `highpass` | number | `0.008` | High-pass temporal filter |
| `addlinear` | boolean | `true` | Add linear regressor to nuisance regression. This makes your time series generally centered around 0. |
| `spikethresh` | number | `9999` | If you want a spike regressor for frames that exceed a certain FD threshold, set that threshold here. Threshold is typically in the 0.5 to 1 range; else, "9999" means no spike regressor. |
| `inspace` | enum | `data` | In almost ALL cases, this should be set to 'data'. It will take a super long time to run the app if you set it to 'label' and you might run out of memory. Options: `data`, `label`. |
| `savets` | boolean | `true` | Save the regional time series (required to produce the out_ts output). |
| `nomatrix` | boolean | `true` | Skip computing the correlation matrix and only extract time series. |

</details>

<!-- brainlife-app:end -->

## Versions on brainlife.io

This repository hosts several Apps, each built from its own branch.

| App | Branch | Run it | Status |
|---|---|---|---|
| fMRI Timeseries Extraction | [`0.1.6`](https://github.com/faskowit/app-fmri-2-mat/tree/0.1.6) | [doi:10.25663/brainlife.app.369](https://doi.org/10.25663/brainlife.app.369) | current |
| fMRI to Connectivity Matrices | [`0.1.5`](https://github.com/faskowit/app-fmri-2-mat/tree/0.1.5) | [doi:10.25663/brainlife.app.167](https://doi.org/10.25663/brainlife.app.167) | available |

## Running the App

### On brainlife.io

Open the App at [doi.org/10.25663/brainlife.app.369](https://doi.org/10.25663/brainlife.app.369), choose `neuro/func/task`, `neuro/parcellation/volume`, `neuro/regressors`, `neuro/mask` from your project, set the parameters and press **Execute**. The results are saved to your project as `neuro/func/task`, `generic/timeseries`.

### Locally

You need [Singularity/Apptainer](https://apptainer.org/) (the App runs in `faskowit/app-fmri-2-mat:brnch-0.1.6`), [`jq`](https://jqlang.github.io/jq/).

1. Clone this repository and check out the App's branch (`git checkout 0.1.6`).
2. Create `config.json` with the paths to your inputs and the parameters:

   ```json
   {
       "fmri": "/path/to/fmri/fmri",
       "parc": "/path/to/parc/parc",
       "key": "/path/to/parc/key",
       "label": "/path/to/parc/label",
       "confounds": "/path/to/confounds/confounds",
       "mask": "/path/to/mask/mask",
       "strategy": "36P",
       "tr": "",
       "smoothfwhm": 0,
       "lowpass": 0.08,
       "highpass": 0.008,
       "addlinear": true,
       "spikethresh": 9999,
       "inspace": "data",
       "savets": true,
       "nomatrix": true
   }
   ```

3. Run `./main`.

## Troubleshooting

- **ERROR: need an fmri, parc, and confounds file**: Provide the fmri, parc and confounds inputs.
- **ERROR: space can only be 'data' or 'labels'**: Set inspace to data (or labels).
- **output csv file not created! error**: Check that the parcellation is aligned to the BOLD image and that the regression step succeeded.

## Citing

If you use this App, please cite it, the software it builds on and brainlife.io:

- fMRI Timeseries Extraction. brainlife.io App. [doi:10.25663/brainlife.app.369](https://doi.org/10.25663/brainlife.app.369)
- Fischl. FreeSurfer. *NeuroImage* 62:774-781 (2012). [doi:10.1016/j.neuroimage.2012.01.021](https://doi.org/10.1016/j.neuroimage.2012.01.021)
- Abraham et al. Machine learning for neuroimaging with scikit-learn. *Frontiers in Neuroinformatics* 8 (2014). [doi:10.3389/fninf.2014.00014](https://doi.org/10.3389/fninf.2014.00014)
- Esteban et al. fMRIPrep: a robust preprocessing pipeline for functional MRI. *Nature Methods* 16:111-116 (2018). [doi:10.1038/s41592-018-0235-4](https://doi.org/10.1038/s41592-018-0235-4)
- Hayashi S, Caron BA, Heinsfeld AS, et al. brainlife.io: a decentralized and open-source cloud platform to support neuroscience research. *Nature Methods* 21:809–813 (2024). [doi:10.1038/s41592-024-02237-2](https://doi.org/10.1038/s41592-024-02237-2)
- Avesani P, McPherson B, Hayashi S, et al. The open diffusion data derivatives, brain data upcycling via integrated publishing of derivatives and reproducible open cloud services. *Scientific Data* 6:69 (2019). [doi:10.1038/s41597-019-0073-y](https://doi.org/10.1038/s41597-019-0073-y)

## Authors

- Josh Faskowitz

## Funding

[![Wellcome-226486/Z/22/Z](https://img.shields.io/badge/Wellcome-226486%2FZ%2F22%2FZ-purple.svg)](https://wellcome.org/)
[![NIH-NINDS-U24NS140384](https://img.shields.io/badge/NIH_NINDS-U24NS140384-green.svg)](https://reporter.nih.gov/project-details/11261037)
[![NIH-NINDS-UM1NS132207](https://img.shields.io/badge/NIH_NINDS-UM1NS132207-green.svg)](https://reporter.nih.gov/project-details/11411328)
[![NIH-NIBIB-R01EB029272](https://img.shields.io/badge/NIH_NIBIB-R01EB029272-green.svg)](https://reporter.nih.gov/project-details/10262925)
[![NIH-NIBIB-R01EB030896](https://img.shields.io/badge/NIH_NIBIB-R01EB030896-green.svg)](https://reporter.nih.gov/project-details/10428625)
[![NIH-NIMH-R01MH126699](https://img.shields.io/badge/NIH_NIMH-R01MH126699-green.svg)](https://reporter.nih.gov/project-details/10460628)
[![NIH-NIDCD-R01DC020088](https://img.shields.io/badge/NIH_NIDCD-R01DC020088-green.svg)](https://reporter.nih.gov/project-details/11140284)
[![NSF-BCS-1734853](https://img.shields.io/badge/NSF_BCS-1734853-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1734853)
[![NSF-BCS-2203524](https://img.shields.io/badge/NSF_BCS-2203524-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2203524)
[![NSF-IIS-1636893](https://img.shields.io/badge/NSF_IIS-1636893-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1636893)
[![NSF-OAC-2148729](https://img.shields.io/badge/NSF_OAC-2148729-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2148729)
[![NSF-IIS-1912270](https://img.shields.io/badge/NSF_IIS-1912270-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1912270)
[![NSF-IIS-2148700](https://img.shields.io/badge/NSF_IIS-2148700-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2148700)
[![NSF-OAC-1916518](https://img.shields.io/badge/NSF_OAC-1916518-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1916518)

<sub>brainlife.io, which runs this App, is publicly funded by Wellcome, the U.S. National Institutes of Health and the U.S. National Science Foundation; acknowledging that support helps keep it running.</sub>

## License

See [LICENSE](LICENSE).
