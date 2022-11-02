from requests import request
import json
from bs4 import BeautifulSoup
import re
import string
import time
from pprint import pprint # Only for debugging purposes

# THE CODE HERE IS NOT FINAL, IT NEEDS TO BE FINISHED AND CLEANED

def clean_string(input_string):
    """
    Utility function to clean the input string.
    The filters are chosen by hand when scraping the values.
    NOTE: Only add filters, don't remove them

    :param input_string: String to be cleaned
    :return: Cleaned string
    """
    return input_string.strip().replace(u"\200b", "").replace(u"\xa0â€‹", "").replace(u"â€‹", "").replace(u"\n", "").replace(u"\t", "")


def get_initial_data(urls, filenames, extract_urls):
    """
    Download the json files about courses, organizational structure
    and staff from dati.trentino.it

    :param urls: Array of URLs to download
    :param filenames: Array of the file names to use when saving the file
    :param extract_urls: Array of booleans that indicate whether to extract the links in the current file or not
    :return: All the downloaded data and the extracted URLs
    """
    downloaded_data = []
    subjects_urls = []
    URL_REGEX = r"""((?:(?:https|ftp|http)?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:it)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:it)\b/?(?!@)))"""

    for i in range(len(urls)):
        res = request('get', urls[i], headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:106.0) Gecko/20100101 Firefox/106.0'})
        if res.ok:
            if extract_urls[i]:
                subjects_urls.append(re.findall(URL_REGEX, res.text))
            subjects_urls[-1] = subjects_urls[-1][1:-1]
            file_to_json = json.loads(res.text)  # Convert string to JSON

            # Save file
            with open(f'{filenames[i]}.json', 'w', encoding='utf-8') as f:
                json.dump(file_to_json, f, indent=2)
            
            """ with open('urls.txt', 'w', encoding='utf-8') as f:
                f.write(str(subjects_urls)) """

            downloaded_data.append(file_to_json)
        else:
            # add better error control with an exception
            print(f"Cannot download data from {url}.")

    return downloaded_data, subjects_urls


def extract_departments(subjects, subjects_english):
    """
    Create a dictionary with all the departments in the University of Trento

    :param subjects: Json file of courses in italian
    :param subjects_english: Json file of courses in english
    :return: A dictionary with the departments
    """
    departments = {}

    for i in range(len(subjects['value']['data'])):
        for j in range(len(subjects['value']['data'][i]['dipartimento'])):
            departments[subjects['value']['data'][i]['dipartimento'][j]['id']] = {
                'name': {
                    'it': subjects['value']['data'][i]['dipartimento'][j]['nome'],
                    'en': subjects_english['value']['data'][i]['department'][j]['unitName']
                }
            }
    return departments


def scrape_esse3(url):
    """
    Scrape the given URL and extract all the needed information

    :param url: Url to scrape
    :return: Dictionary of information for the given URL
    """

    # Uncomment the following and comment lines [97-99] to download the page instead of using the local one
    """ res = request('get', url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:106.0) Gecko/20100101 Firefox/106.0'})
    with open('prova.html', 'w', encoding='utf-8') as f:
        f.write(res.text)

    if res.ok:
        soup = BeautifulSoup(res.text, 'lxml') """
    with open('prova.html', "r") as f:
        page = f.read()
    soup = BeautifulSoup(page, 'lxml')
    
    split_title = soup.find(
        "div", {"id": "header_1"}).contents[1].string.split()
    table_values = soup.find_all('dd')
    
    teaching_units_html = soup.find(id="table1").find('tbody').find_all("tr")
    teaching_units = []
    for i in range(len(teaching_units_html)):
        unit = teaching_units_html[i].find_all("td")
        unit_information = {
            'unit_name': clean_string(unit[0].string),
            'activity_type': clean_string(unit[1].string),
            'duration_hours': clean_string(unit[2].string),
            'type_teaching': clean_string(unit[3].string),
            'subject_area': clean_string(unit[4].string),
            'credits': clean_string(unit[5].string)
        }
        teaching_units.append(unit_information)
    
    # This needs time to do correctly, the table is formatted weirdly
    """ partitions_html = soup.find(id="table2").find('tbody').find_all("tr")
    partitions = []
    for i in range(len(partitions_html)):
        partition = partitions_html[i].find_all("td")
        pprint(partition)
        print(clean_string(partition[1].string))
        partition_information = {
            'partition_name': clean_string(partition[0].string),
            'period': clean_string(partition[1].string),
            'teacher': [clean_string(partition[2].string)],
            'syllabus_link': clean_string(partition[3].string)
        }
        partitions.append(partition_information) """

    information = {
        'id': clean_string(split_title[0]),
        'title': clean_string(" ".join(split_title[3:])),
        'year': table_values[0].contents[0].string[0],
        'type_course': clean_string(table_values[1].contents[0]),
        'credits': clean_string(table_values[2].contents[0].string.split(" ")[0]),
        'lesson_type': clean_string(soup.find("desc_tipo_att").contents[0].string),
        'exam_type': clean_string(table_values[4].contents[0].string),
        'evaluation_type': clean_string(table_values[5].contents[0].string),
        'lesson_period': clean_string(table_values[6].contents[0].string),
        'teaching_units': teaching_units,
        #'partitions': partitions
    }
    """ else:
        # add better error control with an exception
        print(f"Cannot download the page from {url}.") """

    pprint(information)
    return information


# From here the real code starts where all the function calls are made
urls = [
    'https://dati.unitn.it/du/Course',
    'https://dati.unitn.it/du/Course/en',
    # 'https://dati.unitn.it/du/Organization',
    # 'https://dati.unitn.it/du/Organization/en',
    # 'https://dati.unitn.it/du/Person',
    # 'https://dati.unitn.it/du/Person/en'
]
extract_urls = [True, False, False, False]
filenames = [
    'course',
    'course_en',
    #'organization',
    #'organization_en',
    #'person',
    #'person_en'
]

""" data, extracted_urls = get_initial_data(urls, filenames, extract_urls)
departments = extract_departments(data[0], data[1])

with open('departments.json', 'w', encoding='utf-8') as f:
    json.dump(departments, f, indent=2) """

scrape_esse3("https://www.esse3.unitn.it/Guide/PaginaADContest.do?ad_cont_id=10692*93487*2022*2018*9999")

""" for url in extracted_urls[0]:
    information = scrape_esse3(url)
    # What are we doing with this information?
    time.sleep(2) """
