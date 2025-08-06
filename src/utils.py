import os
import sys
import json
import math
import numpy as np

import asyncio
import playwright
from playwright.async_api import async_playwright

from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio

TIMEOUT_1h  = 3600000   # 60 min
TIMEOUT_30m = 1800000   # 30 min
TIMEOUT_15m =  900000   # 15 min
TIMEOUT_10m =   600000  # 10 min
TIMEOUT_5m  =   300000  #  5 min
TIMEOUT_2m  =   120000  #  2 min
TIMEOUT_1m  =    60000  #  1 min
TIMEOUT_30s =    30000  # 30 sec
TIMEOUT_10s =    10000  # 10 sec
TIMEOUT_5s  =     5000  #  5 sec
TIMEOUT_3s  =     3000  #  3 sec
TIMEOUT_1s  =     1000  #  1 sec

TIMEOUT = TIMEOUT_3s

def get_data(input_folder, extensions="pdb,mrc", verbose=1):
    """
    Extract input data information from a given folder.

    Parameters
    ----------
    input_folder : str
        Folder containing subfolders with volume and pdb files.
    extensions : str, optional
        Comma-separated list of file extensions to consider. Default is "pdb,mrc".
    verbose : int, optional
        Verbosity level. 0 is quiet, 1 is verbose. Default is 1.

    Returns
    -------
    data : list of dict
        List of dictionaries containing information about each dataset.
        Each dictionary has keys:
            - i: index of dataset
            - id: unique identifier for dataset
            - dir: path to dataset folder
            - vol: volume file name
            - pdb: pdb file name
            - fvol: absolute path to volume file
            - fpdb: absolute path to pdb file
            - fout: absolute path to output json file
    """
    if verbose: print(f" - Extracting input data info...")
    pdb_format, vol_format = "." + np.array(extensions.split(","))
    input_folder = os.path.abspath(input_folder)

    vids = [f for f in os.listdir(input_folder) if not f.startswith(".") and os.path.isdir(os.path.join(input_folder, f))]
    data = []
    for i, vid in enumerate(vids):
        folder = f"{input_folder}/{vid}"
        vis = [f for f in os.listdir(folder) if f.endswith(vol_format)]
        pis = [f for f in os.listdir(folder) if f.endswith(pdb_format)]
        if len(vis) > 1 or len(pis) > 1: raise Exception(f"Multiple volumes or pdbs in: {folder}")
        if len(vis) < 1: raise FileNotFoundError(f"Could not find volume in: {folder}")
        if len(pis) < 1: raise FileNotFoundError(f"Could not find pdb in: {folder}")
        data.append({
            "i": i,
            "id": vid + "-" + vis[0].split(".")[0],
            "dir": folder,
            "vol": vis[0],
            "pdb": pis[0],
            "fvol": os.path.abspath(f"{folder}/{vis[0]}"),
            "fpdb": os.path.abspath(f"{folder}/{pis[0]}"),
            "fout": os.path.abspath(f"{folder}/CMM_results.json")
        })
    if verbose: print(f"   Total dataset length: {len(data)}")
    return data

async def get_context(p, headless, timeout):
    """
    Launch a new browser context with a specific user agent and viewport.
    
    Parameters
    ----------
    p: playwright.playwright.Playwright
        The Playwright instance.
    headless: bool
        Whether to launch the browser in headless mode.
    timeout: int
        The default timeout for the context.
    
    Returns
    -------
    browser: playwright.chromium.Browser
        The launched browser.
    context: playwright.chromium.BrowserContext
        The launched browser context.
    """
    browser = await p.chromium.launch(headless=headless)  # Set to True for headless mode'
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="en-US"
    )
    context.set_default_timeout(timeout)
    return browser, context

async def get_new_page(browser):
    """
    Create a new page, and disable the navigator.webdriver property and the navigator.mediaDevices.enumerateDevices method.
    
    Parameters
    ----------
    browser: playwright.chromium.Browser
        The Playwright browser instance.
    
    Returns
    -------
    page: playwright.chromium.Page
        The new page.
    """
    page = await browser.new_page()
    await page.evaluate("""
        if (navigator.mediaDevices) {
            Object.defineProperty(navigator.mediaDevices, 'enumerateDevices', {
                get: () => () => []
            });
        }
    """)
    await page.evaluate("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    return page
            

async def download_core(args):
    """
    Download the results of the CMM analysis for a list of input structures.

    Parameters
    ----------
    args: tuple
        A tuple containing the following elements:
            - data: list of dictionaries
                Each dictionary contains the following keys:
                    - 'i': int
                        The index of the structure in the input list.
                    - 'id': str
                        The id of the structure.
                    - 'fpdb': str
                        The path to the input PDB file.
                    - 'pdb': str
                        The name of the input PDB file.
                    - 'fvol': str
                        The path to the input volume file.
                    - 'vol': str
                        The name of the input volume file.
                    - 'fout': str
                        The path to the output JSON file.
            - v: int
                The verbosity level.
            - headless: bool
                Whether to run the browser in headless mode.

    Returns
    -------
    output: dict
        A dictionary containing the following keys:
            - 'processed': list of str
                The list of ids that were processed.
            - 'success': list of str
                The list of ids that were successfully processed.
            - 'failed': list of str
                The list of ids that failed.
            - 'failed_reason': dict of str
                A dictionary where the keys are the ids of the failed structures, and the values are the corresponding error messages.
    errors: list of str
        The list of ids that failed.

    Notes
    -----
    This function starts a Playwright session, and for each structure in the input list, it:
        - Accesses the CMM website.
        - Sets the input files.
        - Runs the analysis.
        - Downloads the results.
        - Validates the results.
        - Closes the page.
    Finally, it prints the results and closes the browser.
    """
    # Get and set args
    data, v, headless = args

    # Start a Playwright session
    errors = []
    output = {"processed": [], "success": [], "failed": [], "failed_reason": {}}
    async with async_playwright() as p:
        browser, context = await get_context(p, headless, TIMEOUT)
        for data_i in data:
            page = await get_new_page(browser)
            try:
                # Start Processing
                if v > 1: print(f"\n - PROCESSING {data_i['i']:>3} | id: {data_i['id']}")
                label_i = f"{data_i['i']}-{data_i['id']}"
                pdb_path, pdb_i = data_i["fpdb"], data_i["pdb"]
                vol_path, vol_i = data_i["fvol"], data_i["vol"]
                out_path = data_i["fout"]

                # Access website and set input files
                if v > 1: print(f"   > Accessing WEB: 'https://cmm.minorlab.org/'...")
                await page.goto("https://cmm.minorlab.org/", timeout=TIMEOUT)

                if v > 1: print(f"   > Setting PDB: {pdb_i}")
                pdb_selector = 'input[id="pdbfile"]'  
                await page.set_input_files(pdb_selector, pdb_path, timeout=TIMEOUT)

                if v > 1: print(f"   > Setting VOL: {vol_i}")
                vol_selector = 'input[id="densfile-2fo"]'  
                await page.set_input_files(vol_selector, vol_path, timeout=TIMEOUT)

                # Run Analysis and Download Results
                if v > 1: print(f"   > Running Analysis...")
                button = page.locator("#show_container > table:nth-child(3) > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(9) > td > h5 > b > button")
                await button.click(timeout=TIMEOUT_10m)
                
                if v > 1: print(f"   > Downloading Results: {out_path}")
                async with page.expect_download() as download_info:
                    await page.eval_on_selector("a:has-text('JSON')", "el => el.click()")
                download = await download_info.value
                await download.save_as(out_path)
                await page.wait_for_load_state(timeout=TIMEOUT_30s)

                # Validate
                if not os.path.exists(out_path):
                    raise FileNotFoundError(f"Could not find downloaded file.")
                output["success"].append(label_i)
            except Exception as e:
                err_msg = "\n" + str(e)
                err_msg = err_msg.replace("\n", "\n       ")
                print(f"\n [!] Error in label = {data_i}: {err_msg}")
                errors.append(label_i)
                output["failed"].append(label_i)
                output["failed_reason"][label_i] = str(e)
                with open("error.txt", "a") as ferror:
                    ferror.write(f"\n [!] Error in label = {label_i}: {err_msg}")
            output["processed"].append(label_i)
            await page.close()

        # Close the browser
        await browser.close()

        # Print results
        if v > 1:
            print(f" - Successfully downloaded {len(data) - len(errors)} out of {len(data)}")
            print(f" - The following ids failed:\n     > {errors}")

    return output, errors

async def submit(data, v=0, n_cpus=1, n_files_per_div=1, headless=True):
    """
    Submit data to the CMM web server and download results.

    Parameters
    ----------
    data : list of str
        A list of paths to input files.
    v : int, optional
        Verbosity level. 0 is silent, 1 prints a progress bar, 2 prints a
        progress bar and each file processed, and 3 prints all output.
        Defaults to 0.
    n_cpus : int, optional
        Number of CPUs to use for parallel processing. Defaults to 1.
    n_files_per_div : int, optional
        Number of files to divide into a single parallel session. Defaults to 1.
    headless : bool, optional
        Whether to run the browser in headless mode. Defaults to True.

    Returns
    -------
    output : dict
        A dictionary containing the following keys:
            - "processed": list of str, ids of files that were processed
            - "success": list of str, ids of files that were successfully downloaded
            - "failed": list of str, ids of files that failed
            - "failed_reason": dict, ids as keys and error messages as values
    errors : list of str
        A list of ids of files that failed.
    """
    n_data = len(data)
    if n_cpus > 4: raise ValueError("Number of parallel sessions cannot be higher than 4.")
    if n_cpus == 1:
        output, errors = await download_core((data, v, headless))
    else:
        args = []
        div = math.ceil(n_data/n_files_per_div)
        for i in range(div):
            n_min = i*n_files_per_div
            n_max = (i+1)*n_files_per_div
            if n_min >= n_data: break
            if n_max >= n_data: n_max = n_data
            args.append((data[n_min:n_max], 0, True))

        semaphore = asyncio.Semaphore(n_cpus)
        async def download_core_limited(arg):
            async with semaphore:
                return await download_core(arg)
        results = await tqdm_asyncio.gather(*[download_core_limited(arg) for arg in args], desc=" - Process")
        
        errors = []
        output = {"processed": [], "success": [], "failed": [], "failed_reason": {}}
        dtypes = {"processed": list, "success": list, "failed": list, "failed_reason": dict}
        dkeys = list(output.keys())
        pbar = tqdm(total=len(results), desc=" - Merging", ascii=True, unit=" split", unit_scale=True, ncols=80)
        for d, e in results:
            errors.extend(e)
            for key in dkeys:
                if dtypes[key] == list: output[key].extend(d[key])
                else: output[key].update(d[key])
            pbar.update(1)
        pbar.close()

        # Print results
        print(f" - Successfully downloaded {len(data) - len(errors)} out of {len(data)}")
        if len(errors) > 0: print(f" - The following ids failed:\n   > {errors}")
        else: print(f" - No errors")

    return output, errors

def save_json(data, fname):
    """
    Save the given data to a json file.

    Parameters
    ----------
    data : dict or list
        The data to save to the json file.
    fname : str
        The path to the json file to save the data to.

    Returns
    -------
    None
    """
    print(f" - Saving results")
    with open(fname, "w") as f:
        json.dump(data, f, indent=4)
    print(f"   Stored at {fname}")

def dry(data, args):
    """
    Print information about the data and arguments, but do not run the submission.

    Parameters
    ----------
    data : list of dict
        The data to submit.
    args : list of str
        The command-line arguments.

    Returns
    -------
    None
    """
    print(f" - Dry-run mode:")
    print(f"   Arguments: {args[1:]}")
    print(f"   Number of folders: {len(data)}")
    if len(data) > 0:
        print(f"   Data[0]:")
        print(json.dumps(data[0], indent=4))