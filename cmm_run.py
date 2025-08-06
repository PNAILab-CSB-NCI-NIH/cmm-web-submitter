import os
import sys
import argparse
import asyncio

sys.path.append(os.path.dirname(__file__))
import src.utils

async def main(input_folder, format, n_cpus, n_files_per_div, verbose, headless, run):
    data = src.utils.get_data(input_folder, format, verbose)
    args = (data, verbose, n_cpus, n_files_per_div, headless)
    src.utils.TIMEOUT = src.utils.TIMEOUT_30s

    if run:
        out, _ = await src.utils.submit(*args)
        src.utils.save_json(out, "run.json")
    else: src.utils.dry(data, args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit volumes for processing.")
    parser.add_argument("-i", "--input_folder", type=str, default="volumes", help="Path to input folder")
    parser.add_argument("-f", "--format", type=str, default="pdb,mrc", help="File formats for model and volume")
    parser.add_argument("-c", "--n_cpus", type=int, default=1, help="Number of CPUs to use")
    parser.add_argument("-n", "--n_files_per_div", type=int, default=1, help="Files per division")
    parser.add_argument("-v", "--verbose", type=int, default=1, help="Verbosity level")
    parser.add_argument("-b", "--headless", type=int, default=True, help="Run browser in headless mode")
    parser.add_argument("-r", "--run", type=int, default=False, help="Run process")

    args = parser.parse_args()

    # Run the async main function
    asyncio.run(main(
        args.input_folder,
        args.format,
        args.n_cpus,
        args.n_files_per_div,
        args.verbose,
        args.headless,
        args.run
    ))