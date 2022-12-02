from requests import request
import json
from bs4 import BeautifulSoup
from copy import deepcopy
import time
from geopy.geocoders import Nominatim
# from pprint import pprint  # Only for debugging purposes
import random
import uuid
from utilities.utilities import append_data, clean_string, initialize_dataset, save_dataset, set_total_size


def get_initial_data(urls, filenames):
    """
    Download the json files about courses, organizational structure
    and staff from dati.trentino.it

    :param urls: Array of URLs to download
    :param filenames: Array of the file names to use when saving the file
    :return: All the downloaded data and the extracted URLs
    """
    downloaded_data = []
    # URL_REGEX = r"""((?:(?:https|ftp|http)?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:it)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:it)\b/?(?!@)))"""

    for i in range(len(urls)):
        print(f"Downloading {urls[i]}...")
        res = request('get', urls[i], headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:106.0) Gecko/20100101 Firefox/106.0'})
        if res.ok:
            file_to_json = json.loads(res.text)  # Convert string to JSON

            # Save file
            save_dataset(file_to_json, filenames[i], 'json')

            """ with open('urls.txt', 'w', encoding='utf-8') as f:
                f.write(str(subjects_urls)) """

            downloaded_data.append(file_to_json)
        else:
            # add better error control with an exception
            print(f"Cannot download data from {urls[i]}.")

    return downloaded_data


def scrape_esse3(url):
    """
    Scrape the given URL and extract all the needed information

    :param url: Url to scrape
    :return: Dictionary of information for the given URL
    """

    # Uncomment the following and comment lines [99-101] to download the page instead of using the local one
    res = request('get', url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:106.0) Gecko/20100101 Firefox/106.0'})
    # with open('prova.html', 'w', encoding='utf-8') as f:
    #     f.write(res.text)
    if res.ok:
        soup = BeautifulSoup(res.text, 'lxml')
        # with open('prova3.html', "r") as f:
        #     page = f.read()
        # soup = BeautifulSoup(page, 'lxml')
        course_id = uuid.uuid4().hex
        if soup.find(id='header2').find('h2').string == "Errore":
            information = {
                'id': course_id,
                'year': 'NA',
                'typeCourse': 'NA',
                'credits': 'NA',
                'lessonType': 'NA',
                'examType': 'NA',
                'evaluationType': 'NA',
                'lessonPeriod': 'NA'
            }
        else:
            table_values = soup.find_all('dd')
            teaching_units_html = soup.find(
                id="table1").find('tbody').find_all("tr")
            teaching_units = []
            for i in range(len(teaching_units_html)):
                unit = teaching_units_html[i].find_all("td")
                unitId = uuid.uuid4().hex
                if len(unit) < 6:
                    # Probably an error in the input, see https://www.esse3.unitn.it/Guide/PaginaADContest.do?ad_cont_id=10661*94459*2022*2017*9999
                    previous_unit = teaching_units_html[i-1].find_all("td")
                    unit_information = {
                        'courseId': course_id,
                        'name': clean_string(previous_unit[0].string),
                        'activityType': clean_string(unit[0].string) if unit[0].string else '',
                        'durationHours': clean_string(unit[1].string) if unit[1].string else '',
                        'typeTeaching': clean_string(unit[2].string) if unit[2].string else '',
                        'subjectArea': clean_string(unit[3].string) if unit[3].string else '',
                        'credits': clean_string(unit[4].string) if unit[4].string else '',
                        'id': unitId
                    }
                else:
                    unit_information = {
                        'courseId': course_id,
                        'name': clean_string(unit[0].string),
                        'activityType': clean_string(unit[1].string) if unit[1].string else '',
                        'durationHours': clean_string(unit[2].string) if unit[2].string else '',
                        'typeTeaching': clean_string(unit[3].string) if unit[3].string else '',
                        'subjectArea': clean_string(unit[4].string) if unit[4].string else '',
                        'credits': clean_string(unit[5].string) if unit[5].string else '',
                        'id': unitId
                    }
                teaching_units.append(unit_information)

            partitions_html = soup.find(id="table2").find(
                'tbody').find_all("tr") if soup.find(id="table2") else None
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
            if partitions_html:
                for i in range(len(partitions_html)):
                    partition = partitions_html[i].find_all("td")
                    partitionId = uuid.uuid4().hex
                    if list(last_rowspan.values()) == [1, 1]:
                        partition_information = {
                            'name': clean_string(partition[0].string),
                            'period': clean_string(partition[1].string),
                            'teacher': {'name': [clean_string(partition[2].string, 'prof') if partition[2].string else ''], 'tenured': [True if partition[3].find('img') else False]},
                            'syllabusLink': 'https://www.esse3.unitn.it/'+partition[4].find('a')['href'] if partition[4].find('a') else '' if partition[4] else '',
                        }
                        last_rowspan = {
                            'partition': int(partition[0]['rowspan']),
                            'syllabus': int(partition[4]['rowspan'])
                        }
                        if partition[2].string and clean_string(partition[2].string, 'prof') != '':
                            professor['count'] += 1
                            professor['name'] = clean_string(
                                partition[2].string, 'prof')
                            professor['tenured'] = True if partition[3].find(
                                'img') else False
                    else:
                        if last_rowspan['partition'] <= 1:
                            partition_information = {
                                'name': clean_string(partition[0].string),
                                'period': clean_string(partition[1].string),
                                'teacher': {'name': [clean_string(partition[2].string, 'prof') if partition[2].string else ''], 'tenured': [True if partition[3].find('img') else False]},
                                'syllabusLink': '',
                            }
                            append_new = True
                            if partition[2].string and clean_string(partition[2].string) != '':
                                professor['count'] += 1
                                professor['name'] = clean_string(
                                    partition[2].string, 'prof')
                                professor['tenured'] = True if partition[3].find(
                                    'img') else False
                        else:
                            last_rowspan['partition'] -= 1
                            partitions[-1]['teacher']['name'].append(clean_string(
                                partition[0].string, 'prof') if partition[0].string else '')
                            partitions[-1]['teacher']['tenured'].append(
                                True if partition[1].find('img') else False)
                            append_new = False
                            if partition[0].string and clean_string(partition[0].string) != '':
                                professor['count'] += 1
                                professor['name'] = clean_string(
                                    partition[0].string, 'prof')
                                professor['tenured'] = True if partition[1].find(
                                    'img') else False

                        if last_rowspan['syllabus'] <= 1:
                            partition_information['syllabusLink'] = clean_string(partition[4].string) if len(
                                partition) >= 5 and partition[4] else partition_information['syllabusLink']
                        else:
                            last_rowspan['syllabus'] -= 1
                            if partitions[-1]['syllabusLink'] == '':
                                partitions[-1]['syllabusLink'] = clean_string(partition[2].string) if len(
                                    partition) >= 3 and partition[2] else partition_information['syllabusLink']
                    if append_new:
                        partition_information['courseId'] = course_id
                        partition_information['id'] = partitionId
                        partitions.append(partition_information)
                if professor['count'] == 1:
                    for partition in partitions:
                        partition['teacher']['name'] = [professor['name']]
                        partition['teacher']['tenured'] = [
                            professor['tenured']]

            course_year = '0'
            year_tmp = table_values[0].contents[0].string.split(',')
            if len(year_tmp) > 1:
                course_year = year_tmp[0][0] + '&' + year_tmp[1][1]
            elif table_values[0].contents[0].string[0] in {'1', '2', '3', '4', '5'}:
                course_year = table_values[0].contents[0].string[0]
            else:
                course_year = clean_string(table_values[0].contents[0].string)
            information = {
                'id': course_id,
                'year': course_year,
                'typeCourse': clean_string(table_values[1].contents[0]),
                'credits': clean_string(table_values[2].contents[0].string.split(" ")[0]),
                'lessonType': clean_string(soup.find("desc_tipo_att").contents[0].string if soup.find("desc_tipo_att") else ''),
                'examType': clean_string(table_values[4].contents[0].string),
                'evaluationType': clean_string(table_values[5].contents[0].string),
                'lessonPeriod': clean_string(table_values[6].contents[0].string)
            }
    else:
        # add better error control with an exception
        print(f"Cannot download the page from {url}.")
        return {}, [], []

    """ with open('prova_esse3.json', 'w', encoding='utf-8') as f:
        json.dump(information, f) """
    # pprint(information)
    return information, partitions, teaching_units


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
    geolocator = Nominatim(
        user_agent="Mozilla/5.0 (Windows NT 10.0; rv:105.0) Gecko/20100101 Firefox/105.0")
    query = geolocator.geocode(query=address)
    if query:
        r = request('get', f"https://www.openstreetmap.org/api/0.6/way/{query.raw.get('osm_id')}.json", headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:106.0) Gecko/20100101 Firefox/106.0'})
        if r.ok:
            return json.loads(r.text)
        else:
            return {}
    else:
        return {}


def get_geospatial_data(dep_data, addresses):
    """
    Fetch and save the geospatial data about Uni departments from OpenStreetMap

    :param dep_data: departments_en file
    :param addresses: Addresses to use
    """
    print("Getting addresses from OpenStreetMap...")
    osm_data = initialize_dataset()
    tags_to_use = {'addr:city',
                   'addr:country',
                   'addr:housenumber',
                   'addr:postcode',
                   'addr:street',
                   'alt_name',
                   'amenity',
                   'email',
                   'long_name',
                   'name',
                   'name:en',
                   'name:it',
                   'old_name',
                   'opening_hours',
                   'phone',
                   'short_name',
                   'website',
                   'wheelchair'}
    for address in addresses:
        info = get_address_information(address)
        tags = {}
        if bool(info):
            for tag in tags_to_use:
                tags[tag] = info['elements'][0]['tags'][tag] if tag in info['elements'][0]['tags'] else ''
            tags['timestamp'] = info['elements'][0]['timestamp']
        append_data(osm_data, {'address': address, 'osm_tags': tags})
        time.sleep(1.5)

    problematic_addresses = [building['address']
                             for building in osm_data['value']['data'] if not bool(building['osm_tags'])]
    i = 0
    while i < len(osm_data['value']['data']):
        if osm_data['value']['data'][i]['address'] in problematic_addresses:
            del osm_data['value']['data'][i]
        else:
            i += 1

    set_total_size(osm_data)
    save_dataset(osm_data, 'generated/buildings', 'json')


def start():
    """
    Main function that executes all the code
    """

    # Set the urls to scrape
    urls = [
        'https://dati.unitn.it/du/Course/en',
        'https://dati.unitn.it/du/Organization/en',
        'https://dati.unitn.it/du/Person/en'
    ]

    # Set the names for the files
    filenames = [
        'original/course_en',
        'original/organizational_unit_en',
        'original/person_en'
    ]

    # Download the files and extract the departments
    data = get_initial_data(urls, filenames)
    # departments = extract_departments(data[1])
    # save_dataset(departments, 'generated/departments', 'json')

    # Scraping of the courses from Esse3
    # NOTE: This needs to be cleaned, move repeated code in a function
    partitions_dataset = initialize_dataset()
    teaching_units_dataset = initialize_dataset()
    courses_dataset = initialize_dataset()
    count = 0
    course_errors = set()
    for course in data[0]['value']['data']:
        print(f"Scraping {course['name']}...")
        try:
            information, partitions, teaching_units = scrape_esse3(
            course['webSite'] + '&cod_lingua=eng')
            course_professors, course_assistants = course['professor'], course['assistant']
            del course['professor'], course['assistant']

            if not bool(information) or information['year'] == 'NA':
                course_errors.add(information['id'])

            course.update(information)

            if len(course['department']) > 0:
                course['departmentId'] = course['department'][0]['unitId']
            else:
                course['departmentId'] = ''
            del course['department']

            base = deepcopy(course)

            for professor in course_professors:
                to_append = deepcopy(base)
                to_append.update(
                    {'professorId': professor['id'], 'assistantId': ''})
                append_data(courses_dataset, to_append)

            for assistant in course_assistants:
                to_append = deepcopy(base)
                to_append.update(
                    {'professorId': '', 'assistantId': assistant['id']})
                append_data(courses_dataset, to_append)

            for partition in partitions:
                for i in range(len(partition['teacher']['name'])):
                    for j in range(len(course_professors)):
                        if " ".join([course_professors[j]['name'], course_professors[j]['surname']]).lower() == partition['teacher']['name'][i].lower():
                            to_append = deepcopy(partition)
                            to_append.update({'professorId': course_professors[j]
                                            ['id'], 'tenured': partition['teacher']['tenured'][i]})
                            del to_append['teacher']
                            append_data(partitions_dataset, to_append)

            for unit in teaching_units:
                append_data(teaching_units_dataset, unit)

            # if count == 3:
            #     break
        except:
            course_errors.add(course)
        count += 1
        if count == 100:
            time.sleep(10)
            count = 1
        else:
            time.sleep(random.uniform(1, 2))

    set_total_size(courses_dataset)
    set_total_size(partitions_dataset)
    set_total_size(teaching_units_dataset)

    save_dataset(courses_dataset, 'generated/course', 'json')
    save_dataset(partitions_dataset, 'generated/course_partition', 'json')
    save_dataset(teaching_units_dataset, 'generated/teaching_unit', 'json')

    # Separating the lists from the staff dataset
    person_dataset = initialize_dataset()
    for person in data[2]['value']['data']:
        person['id'] = person['identifier']
        del person['identifier']

        for position in person['position']:
            to_append = deepcopy(person)
            to_append['role'] = position['role']
            to_append['departmentId'] = position['unitId']
            to_append['phoneNumber'] = ""
            del to_append['position'], to_append['phone']

            append_data(person_dataset, to_append)

        if len(person['phone']) > 0:
            for phone in person['phone']:
                to_append = deepcopy(person)
                to_append['phoneNumber'] = phone
                to_append['role'] = ''
                to_append['departmentId'] = ''
                del to_append['position'], to_append['phone']

                append_data(person_dataset, to_append)

    set_total_size(person_dataset)

    save_dataset(person_dataset, 'generated/person_en_final', 'json')

    # Separating the lists from the organization dataset
    organization_dataset = initialize_dataset()
    addresses = set()
    for organization in data[1]['value']['data']:
        if len(organization['email']) > 0:
            organization['email'] = organization['email'][0]
        else:
            organization['email'] = ''
        if len(organization['website']) > 0:
            organization['website'] = organization['website'][0]
        else:
            organization['website'] = ''
        organization['id'] = organization['identifier']

        del organization['unitPath'], organization['identifier']
        addresses.add(organization['address'])

        if len(organization['phone']) > 0:
            for phone in organization['phone']:
                to_append = deepcopy(organization)
                to_append['phoneNumber'] = phone
                del to_append['phone']

                append_data(organization_dataset, to_append)
        else:
            organization['phoneNumber'] = ''
            del organization['phone']
            append_data(organization_dataset, organization)

    set_total_size(organization_dataset)

    addresses.remove('')

    save_dataset(organization_dataset,
                 'generated/organization_en_final', 'json')

    # Download information about the addresses from OpenStreetMap
    get_geospatial_data(data[1], addresses)

    if len(course_errors) > 0:
        print(f"Courses with errors: {', '.join(course_errors)}")
    print("Done!")


start()
