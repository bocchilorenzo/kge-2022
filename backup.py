"""
    # VERSION 2
    # create partitions divided in dictionary instead of list
    partitions = {}
    last_rowspan = {
        'partition': 1,
        'syllabus': 1
    }
    previous_partition_name = ''
    for i in range(len(partitions_html)):
        partition = partitions_html[i].find_all("td")
        if list(last_rowspan.values()) == [1, 1]:
            partition_information = {
                'period': clean_string(partition[1].string),
                'teacher': {'name': [clean_string(partition[2].string) if partition[2].string else ''], 'tenured': [True if partition[3].find('img') else False]},
                'syllabus_link': clean_string(partition[4].string) if partition[4].string else '' if partition[4] else '',
            }
            last_rowspan = {
                'partition': int(partition[0]['rowspan']),
                'syllabus': int(partition[4]['rowspan'])
            }
            previous_partition_name = clean_string(partition[0].string)
        else:
            if last_rowspan['partition'] <= 1:
                partition_information = {
                    'period': clean_string(partition[1].string),
                    'teacher': {'name': [clean_string(partition[2].string) if partition[2].string else ''], 'tenured': [True if partition[3].find('img') else False]},
                    'syllabus_link': '',
                }
                previous_partition_name = clean_string(partition[0].string)
            else:
                last_rowspan['partition'] -= 1
                partition_information['syllabus'] = ''
                partition_information['teacher']['name'].append(clean_string(partition[0].string) if partition[0].string else '')
                partition_information['teacher']['tenured'].append(True if partition[1].find('img') else False)
            if last_rowspan['syllabus'] <= 1:
                partition_information['syllabus_link'] = clean_string(partition[4].string) if len(
                    partition) >= 5 and partition[4] else partition_information['syllabus_link']
            else:
                last_rowspan['syllabus'] -= 1
                partition_information['syllabus_link'] = clean_string(partition[2].string) if len(
                    partition) >= 3 and partition[2] else partition_information['syllabus_link']
        partitions[previous_partition_name] = partition_information """