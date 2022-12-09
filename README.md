# kge-2022
Repo for the course of Knowledge Graph Engineering (2022, University of Trento)

## Repository structure
- datasets = folder containing the datasets in each stage of the processing, from the original data to the final formatted data
- old_backup = old files kept as backup for a quick rollback
- scripts = playground files to test code before using it in the main files. The code will either be not commented or badly commented
- test_pages = a few html pages downloaded from Esse3 to test out the scraping under different conditions
- utilities = utility functions used multiple times in the scripts

The scraping and downloading of data is done in the download_scrape.py file and the formal_mod_data.py script transforms the data for the formal modeling part. The main.py is just a wrapper to launch the process.

## How to use
- run the main.py