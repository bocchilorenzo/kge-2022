from requests import request
import json
from bs4 import BeautifulSoup
import re
import string
import time
from geopy.geocoders import Nominatim
from pprint import pprint  # Only for debugging purposes

# THE CODE HERE IS NOT FINAL, IT NEEDS TO BE FINISHED AND CLEANED


def clean_string(input_string):
    """
    Utility function to clean the input string.
    The filters are chosen by hand when scraping the values.
    NOTE: Only add filters, don't remove them

    :param input_string: String to be cleaned
    :return: Cleaned string
    """
    return input_string.strip().replace(u"\xa0â€‹", "").replace(u"â€‹", "").replace(u"\n", "").replace(u"\t", "").replace(u"\xa0", "").replace(u"\u200b", "")


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

    # Uncomment the following and comment lines [99-101] to download the page instead of using the local one
    """ res = request('get', url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:106.0) Gecko/20100101 Firefox/106.0'})
    with open('prova.html', 'w', encoding='utf-8') as f:
        f.write(res.text)

    if res.ok:
        soup = BeautifulSoup(res.text, 'lxml') """
    with open('prova3.html', "r") as f:
        page = f.read()
    soup = BeautifulSoup(page, 'lxml')
    split_title = clean_string(soup.find(
        "div", {"id": "header_1"}).contents[1].string).split("-")

    table_values = soup.find_all('dd')
    teaching_units_html = soup.find(id="table1").find('tbody').find_all("tr")
    teaching_units = []
    for i in range(len(teaching_units_html)):
        unit = teaching_units_html[i].find_all("td")
        unit_information = {
            'unit_name': clean_string(unit[0].string),
            'activity_type': clean_string(unit[1].string) if unit[1].string else '',
            'duration_hours': clean_string(unit[2].string) if unit[2].string else '',
            'type_teaching': clean_string(unit[3].string) if unit[3].string else '',
            'subject_area': clean_string(unit[4].string) if unit[4].string else '',
            'credits': clean_string(unit[5].string) if unit[5].string else ''
        }
        teaching_units.append(unit_information)

    partitions_html = soup.find(id="table2").find('tbody').find_all("tr")
    partitions = []
    last_rowspan = {
        'partition': 1,
        'syllabus': 1
    }
    append_new = True
    professor = {
        'count': 0,
        'name': '',
        'tenured': True
    }
    for i in range(len(partitions_html)):
        partition = partitions_html[i].find_all("td")
        if list(last_rowspan.values()) == [1, 1]:
            partition_information = {
                'partition_name': clean_string(partition[0].string),
                'period': clean_string(partition[1].string),
                'teacher': {'name': [clean_string(partition[2].string) if partition[2].string else ''], 'tenured': [True if partition[3].find('img') else False]},
                'syllabus_link': 'https://www.esse3.unitn.it/'+partition[4].find('a')['href'] if partition[4].find('a') else '' if partition[4] else '',
            }
            last_rowspan = {
                'partition': int(partition[0]['rowspan']),
                'syllabus': int(partition[4]['rowspan'])
            }
            if partition[2].string and clean_string(partition[2].string) != '':
                professor['count'] += 1
                professor['name'] = clean_string(partition[2].string)
                professor['tenured'] = True if partition[3].find('img') else False
        else:
            if last_rowspan['partition'] <= 1:
                partition_information = {
                    'partition_name': clean_string(partition[0].string),
                    'period': clean_string(partition[1].string),
                    'teacher': {'name': [clean_string(partition[2].string) if partition[2].string else ''], 'tenured': [True if partition[3].find('img') else False]},
                    'syllabus_link': '',
                }
                append_new = True
                if partition[2].string and clean_string(partition[2].string) != '':
                    professor['count'] += 1
                    professor['name'] = clean_string(partition[2].string)
                    professor['tenured'] = True if partition[3].find('img') else False
            else:
                last_rowspan['partition'] -= 1
                partitions[-1]['teacher']['name'].append(clean_string(
                    partition[0].string) if partition[0].string else '')
                partitions[-1]['teacher']['tenured'].append(
                    True if partition[1].find('img') else False)
                append_new = False
                if partition[0].string and clean_string(partition[0].string) != '':
                    professor['count'] += 1
                    professor['name'] = clean_string(partition[0].string)
                    professor['tenured'] = True if partition[1].find('img') else False

            if last_rowspan['syllabus'] <= 1:
                partition_information['syllabus_link'] = clean_string(partition[4].string) if len(
                    partition) >= 5 and partition[4] else partition_information['syllabus_link']
            else:
                last_rowspan['syllabus'] -= 1
                if partitions[-1]['syllabus_link'] == '':
                    partitions[-1]['syllabus_link'] = clean_string(partition[2].string) if len(
                        partition) >= 3 and partition[2] else partition_information['syllabus_link']
        if append_new:
            partitions.append(partition_information)
    if professor['count'] == 1:
        for partition in partitions:
            partition['teacher']['name'] = [professor['name']]
            partition['teacher']['tenured'] = [professor['tenured']]

    information = {
        'id': clean_string(" ".join(split_title[0:-1])),
        'title': clean_string(split_title[-1]),
        'year': table_values[0].contents[0].string[0],
        'type_course': clean_string(table_values[1].contents[0]),
        'credits': clean_string(table_values[2].contents[0].string.split(" ")[0]),
        'lesson_type': clean_string(soup.find("desc_tipo_att").contents[0].string),
        'exam_type': clean_string(table_values[4].contents[0].string),
        'evaluation_type': clean_string(table_values[5].contents[0].string),
        'lesson_period': clean_string(table_values[6].contents[0].string),
        'teaching_units': teaching_units,
        'partitions': partitions
    }
    """ else:
        # add better error control with an exception
        print(f"Cannot download the page from {url}.") """

    """ with open('prova_esse3.json', 'w', encoding='utf-8') as f:
        json.dump(information, f) """
    pprint(information)
    return information

def get_address_information(address):
    """
    Fetch and return the address information from OpenStreetMap

    :param address: Address to look up in OSM
    :return: Dictionary with the information for the input address
    """
    # Check the Nominatim TOS before using this, it allows maximum 1 request per second
    # https://operations.osmfoundation.org/policies/nominatim/
    # Also check the OSM wiki regarding the API
    # https://wiki.openstreetmap.org/wiki/API_v0.6
    geolocator = Nominatim(user_agent="Mozilla/5.0 (Windows NT 10.0; rv:105.0) Gecko/20100101 Firefox/105.0")
    query = geolocator.geocode(query=address)
    r = request('get', f"https://www.openstreetmap.org/api/0.6/way/{query.raw.get('osm_id')}.json", headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:106.0) Gecko/20100101 Firefox/106.0'})
    if r.ok:
        return json.loads(r.text)
    else:
        return {}

def integrate_organization(organization):
    """
    Add to the organization received in input the information gathered from OpenStreetMap

    :param organization: The organization to integrate
    :return: The integrated organization
    """

    return organization

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
    # 'organization',
    # 'organization_en',
    # 'person',
    # 'person_en'
]

""" data, extracted_urls = get_initial_data(urls, filenames, extract_urls)
departments = extract_departments(data[0], data[1])

with open('departments.json', 'w', encoding='utf-8') as f:
    json.dump(departments, f, indent=2) """

""" for url in extracted_urls[0]:
    information = scrape_esse3(url)
    # What are we doing with this information?
    time.sleep(2) """

# Uncomment the following to test the scraping function
# scrape_esse3("https://www.esse3.unitn.it/Guide/PaginaADContest.do?ad_cont_id=10704*95962*2022*2018*9999")

# Test the OSM address retrieval
print(get_address_information("Via Adalberto Libera, 3, Trento, TN"))
