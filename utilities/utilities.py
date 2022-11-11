from os import makedirs, path
import json


def clean_string(input_string):
    """
    Utility function to clean the input string.
    The filters are chosen by hand when scraping the values.
    NOTE: Only add filters, don't remove them

    :param input_string: String to be cleaned
    :return: Cleaned string
    """
    return input_string.strip().replace(u"\xa0â€‹", "").replace(u"â€‹", "").replace(u"\n", "").replace(u"\t", "").replace(u"\xa0", u" ").replace(u"\u200b", "").replace(u"\u00e0", "à")


def initialize_dataset():
    """
    Return an object to use for inizialization of a new dataset.

    :return: Initial dictionary for any dataset
    """
    return {
        "value": {
            "total": 0,
            "size": 0,
            "language": "en",
            "data": []
        }
    }


def append_data(dataset, to_append):
    """
    Utility function to mask away some code and make it more readable

    :param dataset: Dataset to append data to
    :param to_append: Data to append
    """
    dataset['value']['data'].append(to_append)


def save_dataset(dataset, name, file_format):
    """
    Save the dataset given in input

    :param dataset: Dataset to save
    :param name: Name of the dataset
    :param file_format: Format the dataset should be saved in
    """
    filename = f'./datasets/{name}.{file_format}'
    makedirs(path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        if file_format == 'json':
            json.dump(dataset, f, indent=2)


def set_total_size(dataset):
    """
    Sets the values of the 'total' and 'size' fields in a dictionary

    :param dataset: Dataset to manipulate
    """
    dataset['value']['total'] = len(dataset['value']['data'])
    dataset['value']['size'] = len(dataset['value']['data'])
