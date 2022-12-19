from utilities.utilities import append_data, clean_string, initialize_dataset, save_dataset, set_total_size
import json
import uuid
from shutil import copy2

def adapt_datasets():
    # first, copy and paste files from the "generated" folder which remain the same in the formal modeling
    copy2('datasets/generated/course_partition.json',
        'datasets/formal_modeling/course_partition.json')
    copy2('datasets/generated/teaching_unit.json',
        'datasets/formal_modeling/teaching_unit.json')

    # extract from the person dataset all the professors, phd students and staff members
    with open('datasets/generated/person_en_final.json', encoding='utf-8') as f:
        old_per_data = json.load(f)['value']

        phd_student = initialize_dataset()
        professor = initialize_dataset()
        staff_member = initialize_dataset()

        for p in old_per_data['data']:
            if p['role'].lower().find('teaching') != -1 or p['role'].lower().find('professor') != -1:
                append_data(professor, p)
            elif p['role'] == 'PhD student':
                append_data(phd_student, p)
            else:
                append_data(staff_member, p)

        set_total_size(phd_student)
        set_total_size(professor)
        set_total_size(staff_member)

        save_dataset(phd_student, 'formal_modeling/phd_student', 'json')
        save_dataset(professor,
                    'formal_modeling/professor', 'json')
        save_dataset(staff_member, 'formal_modeling/staff_member', 'json')

    # extract from the courses dataset all the courses and degree programs
    with open('datasets/generated/course.json', encoding='utf-8') as f:
        # first we read all the phd students to extract their ids
        phd_ids = set()
        with open("datasets/formal_modeling/phd_student.json", encoding='utf-8') as f2:
            phd_students = json.load(f2)['value']['data']
            for phd in phd_students:
                phd_ids.add(phd['id'])
        
        old_course_data = json.load(f)['value']
        degree_program = initialize_dataset()
        deg_prog_lookup = {}
        course = initialize_dataset()

        for c in old_course_data['data']:
            if c['degreeProgram'] not in deg_prog_lookup:
                to_add = {'id': uuid.uuid4().hex, 'name': c['degreeProgram'], 'universityId': 'STO0000001'}
                append_data(degree_program, to_add)
                deg_prog_lookup[to_add['name']] = to_add['id']
                c['degreeProgramId'] = to_add['id']
            else:
                c['degreeProgramId'] = deg_prog_lookup[c['degreeProgram']]

            del c['degreeProgram']
            if c['assistantId'] in phd_ids:
                c['assistant_phd'] = c['assistantId']
                c['assistant_professor'] = ""
            else:
                c['assistant_professor'] = c['assistantId']
                c['assistant_phd'] = ""
            del c['assistantId']
            append_data(course, c)

        set_total_size(degree_program)
        set_total_size(course)

        save_dataset(degree_program, 'formal_modeling/degree_program', 'json')
        save_dataset(course, 'formal_modeling/course', 'json')

    libraries = set()
    # extract from the organizations dataset all the departments, phd programs and the university
    with open('datasets/generated/organization_en_final.json', encoding='utf-8') as f:
        old_org_data = json.load(f)['value']
        department = initialize_dataset()
        university = initialize_dataset()
        phd_program = initialize_dataset()

        for o in old_org_data['data']:
            o['universityId'] = 'STO0000001'
            if 'library' in o['name'].lower():
                libraries.add(o['address'])

            if o['subType'] == 'degree program':
                del o['subType'], o['unitType'], o['address'], o['email'], o['phoneNumber']
                append_data(phd_program, o)
            elif o['subType'] == "university":
                to_append = {
                    "id": o['id'],
                    "name": o['name'],
                    "startTime": "October 2022",
                    "endTime": "January 2023",
                    "latitude": "46.0626733",
                    "longitude": "11.12657322",
                    "altitude": "272"
                }
                append_data(university, to_append)
            else:
                del o['unitType']
                append_data(department, o)

        set_total_size(department)
        set_total_size(university)
        set_total_size(phd_program)

        save_dataset(department, 'formal_modeling/department', 'json')
        save_dataset(phd_program, 'formal_modeling/phd_program', 'json')
        save_dataset(university, 'formal_modeling/university', 'json')

    # extract from the buildings dataset all the libraries
    with open('datasets/generated/buildings.json', encoding='utf-8') as f:
        buildings = json.load(f)['value']

        libraries_data = initialize_dataset()

        for p in buildings['data']:
            if p['address'] in libraries:
                append_data(libraries_data, {
                    "id": uuid.uuid4().hex,
                    "address": p['address'],
                    "name": p['osm_tags']['name'],
                    "email": p['osm_tags']['email'],
                    "website": p['osm_tags']['website'],
                    "alt_name": p['osm_tags']['alt_name'],
                    "short_name": p['osm_tags']['short_name'],
                    "opening_hours": p['osm_tags']['opening_hours'],
                    "phone": p['osm_tags']['phone'],
                    "wheelchair": p['osm_tags']['wheelchair'],
                    'universityId': 'STO0000001'
                })

        set_total_size(libraries_data)

        save_dataset(libraries_data, 'formal_modeling/libraries', 'json')

    # manually create the dataset for the student accomodations
    student_residence = initialize_dataset()
    append_data(student_residence, {
                    "id": uuid.uuid4().hex,
                    "address": "Via della Malpensada, 140, 38128 Trento",
                    "name": "Studentato S. Bartolameo",
                    "alt_name": "Sanba",
                    "wheelchair": "",
                    'universityId': 'STO0000001'
                })
    append_data(student_residence, {
                    "id": uuid.uuid4().hex,
                    "address": "Piazza Valeria Solesin, 1, Trento",
                    "name": "Studentato Mayer",
                    "alt_name": "Mayer",
                    "wheelchair": "",
                    'universityId': 'STO0000001'
                })
    append_data(student_residence, {
                    "id": uuid.uuid4().hex,
                    "address": "Via della Gora 9, Rovereto",
                    "name": "Residenza A. Barelli Rovereto",
                    "alt_name": "",
                    "wheelchair": "",
                    'universityId': 'STO0000001'
                })
    set_total_size(student_residence)

    save_dataset(student_residence, 'formal_modeling/student_residence', 'json')