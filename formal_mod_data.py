from utilities.utilities import append_data, clean_string, initialize_dataset, save_dataset, set_total_size
import json
import uuid
from shutil import copy2

# first, copy and paste files from the "generated" folder which remain the same in the formal modeling
copy2('datasets/generated/course_partition.json',
      'datasets/formal_modeling/course_partition.json')
copy2('datasets/generated/teaching_unit.json',
      'datasets/formal_modeling/teaching_unit.json')


with open('datasets/generated/course.json', encoding='utf-8') as f:
    old_course_data = json.load(f)['value']
    degree_program = initialize_dataset()
    deg_prog_lookup = {}
    course = initialize_dataset()

    for c in old_course_data['data']:
        if c['degreeProgram'] not in deg_prog_lookup:
            to_add = {'id': uuid.uuid4().hex, 'name': c['degreeProgram']}
            append_data(degree_program, to_add)
            deg_prog_lookup[to_add['name']] = to_add['id']
            c['degreeProgramId'] = to_add['id']
        else:
            c['degreeProgramId'] = deg_prog_lookup[c['degreeProgram']]

        del c['degreeProgram']
        append_data(course, c)

    set_total_size(degree_program)
    set_total_size(course)

    save_dataset(degree_program, 'formal_modeling/degree_program', 'json')
    save_dataset(course, 'formal_modeling/course', 'json')

    # course['data'] = old_course_data['data']

with open('datasets/generated/organization_en_final.json', encoding='utf-8') as f:
    old_org_data = json.load(f)['value']
    department = initialize_dataset()
    management_structure = initialize_dataset()
    phd_program = initialize_dataset()

    for o in old_org_data['data']:
        if o['subType'] == 'degree program':
            del o['subType'], o['unitType'], o['address'], o['email'], o['phoneNumber']
            append_data(phd_program, o)
        elif o['subType'] == 'academic department':
            del o['subType'], o['unitType']
            append_data(department, o)
        else:
            o['subType'], o['unitType']
            append_data(management_structure, o)

    set_total_size(department)
    set_total_size(management_structure)
    set_total_size(phd_program)

    save_dataset(department, 'formal_modeling/department', 'json')
    save_dataset(management_structure,
                 'formal_modeling/management_structure', 'json')
    save_dataset(phd_program, 'formal_modeling/phd_program', 'json')

    # course['data'] = old_course_data['data']
