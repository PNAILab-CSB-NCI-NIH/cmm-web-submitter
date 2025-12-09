# Automated Web Submission Script for CMM Analysis

[![build](https://github.com/PNAILab-CSB-NCI-NIH/cmm-web-submitter/actions/workflows/ci.yml/badge.svg)](https://github.com/PNAILab-CSB-NCI-NIH/cmm-web-submitter/actions/workflows/ci.yml)  
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)  


This repository contains a Python script that automates the submission of `.pdb`/`.cif` and `.mrc` file pairs to the [CheckMyMetal (CMM) web server](https://cmm.minorlab.org/), triggers analysis, and downloads the resulting JSON output.

It uses Playwright for browser automation and supports parallel execution with asynchronous programming.

---

## Features

- Uploads `.pdb` and `.mrc` files to the CMM website.
- Automates analysis initiation and downloads results as JSON.
- Handles batches of submissions with optional parallelism.
- Verbosity control and dry-run (testing) mode.

---

## Folder Structure

Your input folder should contain subfolders (one per dataset). Each subfolder must include:
- Exactly **one `.pdb`/`.cif` file**
- Exactly **one `.mrc` file**

Example:
```
volumes/
├── volume_1/
│   ├── model.pdb
│   └── map.mrc
├── volume_2/
│   ├── model.pdb
│   └── map.mrc
```

Since the density maps are large files, you can obtain them at [Zenodo](https://doi.org/10.5281/zenodo.16367407) and place them in the ./volumes (currently empty). There are 2 examples of density maps and pdb files in the 'volumes' folder at Zenodo, exemplifying the usage of the automated script.

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/PNAILab-CSB-NCI-NIH/cmm-web-submitter.git
cd cmm-web-submitter
```

### 2. Create a Conda environment

```bash
conda create -n cmm_submitter python=3.11
conda activate cmm_submitter
```

### 3. Install requirements with pip

```bash
pip install -r requirements
```

### 4. Install Playwright browser drivers

```bash
playwright install
```

---
## ⚠️ Ethical Use Notice
Please be conscientious when using this tool, especially with the provided ability to run parallel requests. <b>The CMM web server is a valuable public resource </b> developed to support the research community, and its backend infrastructure is not publicly documented. Submitting too many simultaneous jobs may unintentionally overload or disrupt the service for others.

We recommend limiting parallel submissions to 4 sessions or fewer to minimize potential impact, and that is the reason we limited the maximum number of parallel sessions to 4. Use this tool responsibly and understand that you are solely responsible for how you use it. The authors of this script are not liable for any misuse or consequences arising from excessive automated access.

> The CMM platform is an important public contribution to the structural biology community — please help ensure its continued availability by using it thoughtfully and respectfully.

That said, we observed that processing <b>~70 structures with 4 parallel sessions completes in about ~20 minutes</b>, depending on connection speed, indicating that moderate parallelism is effective, efficient, and sufficient without overloading the system.

---
## Usage

To test the submission, simply run:

```bash
python cmm_run.py -i volumes
```

For parallelism (4), use
```bash
python cmm_run.py -i volumes -c 4
```

To run the script without dry-run:
```bash
python cmm_run.py -i volumes -c 4 -r 1
```

### Arguments:

| Argument             | Default     | Description                              |
|----------------------|-------------|------------------------------------------|
| `-i`, `--input_folder` | `"volumes"` | Folder containing input subfolders |
| `-f`, `--format` | `"pdb,mrc"` | File formats for model and volume |
| `-c`, `--n_cpus`       | `1` | Number of CPUs to use (parallelism) |
| `-n`, `--n_files_per_div` | `1` | Files per process split |
| `-v`, `--verbose`      | `1` | Verbosity level |
| `-b`, `--headless`     | `1` | Run in headless mode (1=True, 0=False) |
| `-r`, `--run`          | `0` | Set to 1 to actually submit jobs |

> To avoid running the script unintentionlly, the dry-run mode is enabled by default (`-r 0`). you've verified your input setup and are confident everything is correct, set `-r 1` to proceed with the automated submission and result retrieval.

---
## Optional: Run via Jupyter Notebook
For users who prefer an interactive environment, a Jupyter Notebook is provided, that guides you through the submission process step by step.

This is particularly useful for:

- First-time users or those unfamiliar with command-line tools
- Verifying input structures before bulk submission
- Debugging or modifying specific runs interactively

To launch the notebook:

```bash
jupyter notebook cmm_note.ipynb &
```

Make sure you’ve activated the environment first:
```bash
conda activate cmm_submitter
```

Preferably, you may also simply add the environment to your current installed jupyter-lab and start from there.

---

## 📝 Output

- Results are saved to `run.json` including errors, in case of debugging needed.
- Individual outputs are stored as `CMM_results.json` in each dataset's subfolder.
- Errors (if any) are logged in `error.txt`.

---

## 🔧 Troubleshooting

- If you get timeout errors, check your internet connection or try increasing `TIMEOUT_*` values in the jupyter notebook.
- Make sure your input folders contain exactly one `.pdb` and one `.mrc` file each.
- If you get errors in a few structures only, use the jupyter notebook to filter the submitted data by the error indexes.

---

## 📄 License

MIT License. See `LICENSE` file for details.

## Citing

If CMM-Web-Submitter helped your research, please cite:

Zenodo:
```bibtex
@software{cmmsub2025,
  author = {Degenhardt, Hermann F. and Degenhardt, Maximilia F. S. and Wang, Yun-Xing},
  title = {CMM Web Submitter: Scripted web interface for parallel file submission and result retrieval from CheckMyMetal (CMM)},
  year = {2025},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.16367407},
  url = {https://doi.org/10.5281/zenodo.16367407},
}
```
