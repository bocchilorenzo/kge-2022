from requests import request
import json
from bs4 import BeautifulSoup
import re
import string
import time
from geopy.geocoders import Nominatim
#from pprint import pprint  # Only for debugging purposes
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
    URL_REGEX = r"""((?:(?:https|ftp|http)?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:it)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:it)\b/?(?!@)))"""

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
            print(f"Cannot download data from {url}.")

    return downloaded_data


def extract_departments(subjects):
    """
    Create a dictionary with all the departments in the University of Trento

    :param subjects: Json file of courses in italian
    :param subjects_english: Json file of courses in english
    :return: A dictionary with the departments
    """
    print("Extracting all departments...")
    departments = initialize_dataset()

    for course in subjects['value']['data']:
        for department in course['department']:
            append_data(departments, {
                'id': department['unitId'],
                'name': department['unitName']
            })
    departments['value']['total'] = len(departments['value']['data'])
    departments['value']['size'] = len(departments['value']['data'])

    return departments


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
        #soup = BeautifulSoup(page, 'lxml')
        course_id = uuid.uuid4().hex
        table_values = soup.find_all('dd')
        teaching_units_html = soup.find(
            id="table1").find('tbody').find_all("tr")
        teaching_units = []
        for i in range(len(teaching_units_html)):
            unit = teaching_units_html[i].find_all("td")
            if len(unit) < 6:
                # Probably an error in the input, see https://www.esse3.unitn.it/Guide/PaginaADContest.do?ad_cont_id=10661*94459*2022*2017*9999
                previous_unit = teaching_units_html[i-1].find_all("td")
                unit_information = {
                    'courseId': course_id,
                    'unitName': clean_string(previous_unit[0].string),
                    'activityType': clean_string(unit[0].string) if unit[0].string else '',
                    'durationHours': clean_string(unit[1].string) if unit[1].string else '',
                    'typeTeaching': clean_string(unit[2].string) if unit[2].string else '',
                    'subjectArea': clean_string(unit[3].string) if unit[3].string else '',
                    'credits': clean_string(unit[4].string) if unit[4].string else ''
                }
            else:
                unit_information = {
                    'courseId': course_id,
                    'unitName': clean_string(unit[0].string),
                    'activityType': clean_string(unit[1].string) if unit[1].string else '',
                    'durationHours': clean_string(unit[2].string) if unit[2].string else '',
                    'typeTeaching': clean_string(unit[3].string) if unit[3].string else '',
                    'subjectArea': clean_string(unit[4].string) if unit[4].string else '',
                    'credits': clean_string(unit[5].string) if unit[5].string else ''
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
                if list(last_rowspan.values()) == [1, 1]:
                    partition_information = {
                        'partitionName': clean_string(partition[0].string),
                        'period': clean_string(partition[1].string),
                        'teacher': {'name': [clean_string(partition[2].string) if partition[2].string else ''], 'tenured': [True if partition[3].find('img') else False]},
                        'syllabusLink': 'https://www.esse3.unitn.it/'+partition[4].find('a')['href'] if partition[4].find('a') else '' if partition[4] else '',
                    }
                    last_rowspan = {
                        'partition': int(partition[0]['rowspan']),
                        'syllabus': int(partition[4]['rowspan'])
                    }
                    if partition[2].string and clean_string(partition[2].string) != '':
                        professor['count'] += 1
                        professor['name'] = clean_string(partition[2].string)
                        professor['tenured'] = True if partition[3].find(
                            'img') else False
                else:
                    if last_rowspan['partition'] <= 1:
                        partition_information = {
                            'partitionName': clean_string(partition[0].string),
                            'period': clean_string(partition[1].string),
                            'teacher': {'name': [clean_string(partition[2].string) if partition[2].string else ''], 'tenured': [True if partition[3].find('img') else False]},
                            'syllabusLink': '',
                        }
                        append_new = True
                        if partition[2].string and clean_string(partition[2].string) != '':
                            professor['count'] += 1
                            professor['name'] = clean_string(
                                partition[2].string)
                            professor['tenured'] = True if partition[3].find(
                                'img') else False
                    else:
                        last_rowspan['partition'] -= 1
                        partitions[-1]['teacher']['name'].append(clean_string(
                            partition[0].string) if partition[0].string else '')
                        partitions[-1]['teacher']['tenured'].append(
                            True if partition[1].find('img') else False)
                        append_new = False
                        if partition[0].string and clean_string(partition[0].string) != '':
                            professor['count'] += 1
                            professor['name'] = clean_string(
                                partition[0].string)
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
                    partitions.append(partition_information)
            if professor['count'] == 1:
                for partition in partitions:
                    partition['teacher']['name'] = [professor['name']]
                    partition['teacher']['tenured'] = [professor['tenured']]

        information = {
            'id': course_id,
            'year': table_values[0].contents[0].string[0],
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


def start():
    """
    Main function that executes all the code
    """

    # Set the urls to scrape
    urls = [
        'https://dati.unitn.it/du/Course',
        'https://dati.unitn.it/du/Course/en',
        'https://dati.unitn.it/du/Organization',
        'https://dati.unitn.it/du/Organization/en',
        'https://dati.unitn.it/du/Person',
        'https://dati.unitn.it/du/Person/en'
    ]

    # Set the names for the files
    filenames = [
        'original/course',
        'original/course_en',
        'original/organization',
        'original/organization_en',
        'original/person',
        'original/person_en'
    ]

    # Download the files and extract the departments
    data = get_initial_data(urls, filenames)
    departments = extract_departments(data[1])
    save_dataset(departments, 'generated/departments', 'json')

    # Scraping of the courses from Esse3
    # NOTE: This needs to be cleaned, move repeated code in a function
    partitions_dataset = initialize_dataset()
    teaching_units_dataset = initialize_dataset()
    course_professors_dataset = initialize_dataset()
    course_departments_dataset = initialize_dataset()
    course_assistants_dataset = initialize_dataset()
    counter = 0
    for course in data[1]['value']['data']:
        print(f"Scraping {course['name']}...")
        information, partitions, teaching_units = scrape_esse3(
            course['webSite'])
        course_departments, course_professors, course_assistants = course[
            'department'], course['professor'], course['assistant']
        del course['department'], course['professor'], course['assistant']

        for professor in course_professors:
            append_data(course_professors_dataset, {
                'courseId': information['id'],
                'professorId': professor['id']
            }
            )
        for department in course_departments:
            append_data(course_departments_dataset, {
                'courseId': information['id'],
                'departmentId': department['unitId']
            }
            )
        for assistant in course_assistants:
            append_data(course_assistants_dataset, {
                'courseId': information['id'],
                'assistantId': professor['id']
            }
            )

        for partition in partitions:
            append_data(partitions_dataset, partition)
        for unit in teaching_units:
            append_data(teaching_units_dataset, unit)

        # This is the inbuilt function to merge dictionaries, needs testing
        course.update(information)
        """ course['id'] = information['id']
        course['teachingYear'] = information['year']
        course['courseType'] = information['type_course']
        course['credits'] = information['credits']
        course['teachingMethods'] = information['lesson_type']
        course['examType'] = information['exam_type']
        course['evalutation'] = information['evaluation_type']
        course['teachingPeriod'] = information['lesson_period']
        course['teachingUnits'] = information['teaching_units']
        course['partitions'] = information['partitions'] """
        count += 1
        if count == 100:
            time.sleep(random.uniform(1, 2))
            count = 1
        else:
            time.sleep(10)
    set_total_size(partitions_dataset)
    set_total_size(teaching_units_dataset)

    save_dataset(data[1], 'generated/course_en_final', 'json')
    save_dataset(partitions_dataset, 'generated/partitions_en', 'json')
    save_dataset(teaching_units_dataset, 'generated/teaching_units_en', 'json')
    save_dataset(course_departments_dataset, 'generated/course_departments_en', 'json')
    save_dataset(course_professors_dataset, 'generated/course_professors_en', 'json')
    save_dataset(course_assistants_dataset, 'generated/course_assistants_en', 'json')

    # Separating the lists from the staff dataset
    roles_dataset = initialize_dataset()
    roles_set = set()
    person_positions_dataset = initialize_dataset()
    person_phone_dataset = initialize_dataset()
    for person in data[5]['value']['data']:
        for position in person['position']:
            role_id = uuid.uuid4().hex
            if position['role'] not in roles_set:
                append_data(roles_dataset, {
                    'roleId': role_id,
                    'roleName': position['role']
                })
                roles_set.add(position['role'])
            append_data(person_positions_dataset, {
                'personId': person['identifier'],
                'roleId': role_id,
                'unitId': position['unitId']
            })
        for phone in person['phone']:
            append_data(person_phone_dataset, {
                'personId': person['identifier'],
                'phoneNumber': phone
            })
        del person['position']
        del person['phone']
    set_total_size(roles_dataset)
    set_total_size(person_positions_dataset)
    set_total_size(person_phone_dataset)

    save_dataset(data[5], 'generated/person_en_final', 'json')
    save_dataset(roles_dataset, 'generated/roles_en', 'json')
    save_dataset(person_positions_dataset, 'generated/person_positions', 'json')
    save_dataset(person_phone_dataset, 'generated/person_phone', 'json')
    del roles_set

    # Separating the lists from the organization dataset
    organization_phone_dataset = initialize_dataset()
    organization_email_dataset = initialize_dataset()
    organization_website_dataset = initialize_dataset()
    organization_path_dataset = initialize_dataset()
    for organization in data[3]['value']['data']:
        for phone in organization['phone']:
            append_data(organization_phone_dataset, {
                'organizationId': organization['identifier'],
                'phoneNumber': phone
            })
        for email in organization['email']:
            append_data(organization_email_dataset, {
                'organizationId': organization['identifier'],
                'emailAddress': email
            })
        for website in organization['website']:
            append_data(organization_website_dataset, {
                'organizationId': organization['identifier'],
                'website': website
            })
        for path in organization['unitPath']:
            append_data(organization_path_dataset, {
                'organizationId': organization['identifier'],
                'unitPath': path
            })
        del organization['phone']
        del organization['website']
        del organization['email']
        del organization['unitPath']
    set_total_size(organization_phone_dataset)
    set_total_size(organization_email_dataset)
    set_total_size(organization_website_dataset)
    set_total_size(organization_path_dataset)

    save_dataset(data[3], 'generated/organization_en_final', 'json')
    save_dataset(organization_phone_dataset, 'generated/organization_phone', 'json')
    save_dataset(organization_email_dataset, 'generated/organization_email', 'json')
    save_dataset(organization_website_dataset, 'generated/organization_website', 'json')
    save_dataset(organization_path_dataset, 'generated/organization_path', 'json')

    # Download information about the addresses from OpenStreetMap
    print("Getting addresses from OpenStreetMap...")
    addresses = set()
    for organization in file_to_json['value']['data']:
        addresses.add(organization['address'])

    addresses.remove('')

    osm_data = initialize_dataset()

    for address in addresses:
        info = get_address_information(address)
        tags = {}
        if bool(info):
            tags = info['elements'][0]['tags']
            tags['timestamp'] = info['elements'][0]['timestamp']
        append_data(osm_data, {'address': address, 'osm_tags': tags})
        time.sleep(1.5)
    set_total_size(osm_data)
    save_dataset(osm_data, 'generated/buildings', 'json')

    print("Done!")


start()
