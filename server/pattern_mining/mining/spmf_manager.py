import pandas as pd
import numpy as np
import os
from spmf import Spmf
import pathlib
import uuid
from pattern_mining.pre_processing.dictionary import AirportMapping
from typing import Iterable, List

spmf_jar_dir = str(pathlib.Path(__file__).parent.absolute())+"/thirdparty"
data_dir = str(pathlib.Path(__file__).parent.parent.absolute()) + "/data/spmf"


def _generate_CONVERTED_FROM_TEXT():
    map = AirportMapping()
    CONVERTED_FROM_TEXT = "@CONVERTED_FROM_TEXT\n"
    for key, value in map.code_to_event.items():
        if "parent" in value:
            CONVERTED_FROM_TEXT += ("@ITEM=" + str(key) + "=" + value['event'] + "\n")
    return CONVERTED_FROM_TEXT


def generate_input_line_from_list(record: List, itemset=False) -> str:
    '''
    :param record: list of numbers for frequent itemsets and association rules and sequential rules OR
    list of tuples for complex sequences (simultaneous events). Events in each tuple must be sorted
    :param itemset: if the list is a transaction or a sequence
    :return: string in format of SPMF input format
    '''

    item_set = set()
    line = ""
    # The value "-1" indicates the end of an itemset.
    # The value "-2" indicates the end of a sequence (it appears at the end of each line).
    for element in record:
        if itemset:
            if isinstance(element, np.int32):
                item_set.add(element)
            else:  # tuple for simultaneous events
                for event in element:
                    item_set.add(event)
        else:
            if isinstance(element, np.int32):
                line += str(element) + " -1 "
            else:
                for event in element:
                    line += str(event) + ' '
                line += "-1 "

    if item_set:
        item_set = list(item_set)
        item_set.sort()  # SPMF requirement
        for item in item_set:
            line += str(item) + ' '
    else:
        line += "-2"
    line += "\n"
    return line


def generate_input_file(records: Iterable, itemset=False, converted_from_text=False, is_spmf_format=False) -> str:
    '''
    :param records: iterable object of lists. Each list is a transaction or a sequence. Complex sequences must be
        represented with list of tuples
    :param itemset: if the records are transaction or sequence
    :param converted_from_text: use a dictionary for converting numbers to names in output.
        more details in SPMF documentation
    :param is_spmf_format: if the records are already in spmf format
    :return: file name of the SPMF input
    '''
    id = str(uuid.uuid4().hex)
    filename = id + '.txt'
    filename = os.path.join(data_dir, filename)
    file = open(filename, "w")

    if converted_from_text:
        file.write(_generate_CONVERTED_FROM_TEXT())

    for record in records:
        if not is_spmf_format:
            record = generate_input_line_from_list(record, itemset)
        file.write(record)

    file.close()

    return filename


def run(sm_algorithm, input_file, support='15%', confidence='60%', window=15, max_cons=1, itemset=False) -> str:
    '''
    Runs SPMF Java executable with input arguments, returns file name of SPMF output
    '''
    id = str(uuid.uuid4().hex)
    output_filename = id + '.txt'
    output_file = os.path.join(data_dir, output_filename)
    arguments = [support]
    if not itemset:
        arguments.append(confidence)
    if sm_algorithm == 'TRuleGrowth':
        arguments.extend([window, window, max_cons])
    spmf = Spmf(sm_algorithm, input_filename=input_file, spmf_bin_location_dir=spmf_jar_dir,
                output_filename=output_file, arguments=arguments, memory=350)
    spmf.run()
    return output_file


if __name__ == "__main__":
    sequence_df = pd.read_pickle("pattern_mining/data/HIAA/labeled_sequences.pkl")
    delta_df = pd.read_pickle("pattern_mining/data/HIAA/labeled_deltas.pkl")
    input = generate_input_file(sequence_df['Sequence'])
    run('TRuleGrowth', input, support='10%')
    input = generate_input_file(delta_df['Sequence'], itemset=True)
    run('FPGrowth_itemsets', input, itemset=True)
