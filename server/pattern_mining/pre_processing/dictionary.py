import pandas as pd
from os import path
import json
from typing import List

class Mapping:
    '''
    SPMF library requires items and events in form of numbers

    Saving two dictionaries for 1:1 mapping, since we want two way searching key->value and value->key
    in order not to iterate a dictionary for value->key everytime and keep it O(1), we save two dictionaries
    '''
    _event_to_code_path = None
    _code_to_event_path = None
    event_to_code = {}
    code_to_event = {}

    def __init__(self, event_to_code_path, code_to_event_path):
        self._event_to_code_path = event_to_code_path
        self._code_to_event_path = code_to_event_path
        if not (path.exists(self._event_to_code_path) and path.exists(self._code_to_event_path)):
            self._generate_mappings()
            self._save_mappings()

        else:
            self._load_mappings()

    def _load_mappings(self):
        with open(self._event_to_code_path, 'r') as jf:
            self.event_to_code = json.load(jf)
        with open(self._code_to_event_path, 'r') as jf:
            self.code_to_event = json.load(jf)

    def _save_mappings(self):
        with open(self._event_to_code_path, 'w') as outfile:
            json.dump(self.event_to_code, outfile, indent=4)
        with open(self._code_to_event_path, 'w') as outfile:
            json.dump(self.code_to_event, outfile, indent=4)

    def _generate_mappings(self):
        raise NotImplementedError("Please Implement this method")


class AirportMapping(Mapping):

    def __init__(self):
        Mapping.__init__(self, "pattern_mining/data/mapping/airport/event_to_code.json",
                         "pattern_mining/data/mapping/airport/code_to_event.json")

    def _get_all_type(self, files: List, column: str) -> set:
        '''
        :param files: list of turnaround files
        :param column: event/item column
        :return: list of unique events in turnaround logs/items in delta logs
        '''
        unique_events = set()
        for tf in files:
            df = pd.read_csv(tf, sep=';')
            unique_events.update(list(df[column].unique()))
        return unique_events

    def _add_tags(self, event: str, code: int, tags: List) -> int:
        '''
        adds tags to base event and extends the dictionaries with new entries
        the base event is set as the parent event of the tagged entries

        :param event: base event, for example, "fuller connected"
        :param code: number code assigned to base event
        :param tags: list of tags to be added to base event
        :return: the last number used in the dictionaries after adding the tags
        '''
        parent_code = code
        for tag in tags:
            code += 1
            tagged = tag + " " + event
            self.event_to_code[tagged] = {'code': code, 'parent': event, 'tag': tag}
            self.code_to_event[code] = {'event': tagged, 'parent': parent_code, 'tag': tag}
        return code

    def _generate_mappings(self):
        '''
        creates event-number and number-event mappings for events/deltas in dataset
        base events, like fueller connected, will be assigned a number
        for each base event, three other labelled events are added to dictionaries with number and parent event
        '''

        # removed filenames for confidentiality
        turnaround_files = ["pattern_mining/data/airport/file1.csv",
                            "pattern_mining/data/airport/file2.csv",
                            "pattern_mining/data/airport/file3.csv"]
        delta_files = ["pattern_mining/data/airport/file4.csv",
                       "pattern_mining/data/airport/file5.csv",
                       "pattern_mining/data/airport/file6.csv"]
        all_raw_event_type = self._get_all_type(turnaround_files, 'Type')
        all_deltas = self._get_all_type(delta_files, 'name')
        code = 1
        tags = ['early', 'delayed', 'ontime']
        for event in all_raw_event_type:
            self.event_to_code[event] = {'code': code}
            self.code_to_event[code] = {'event': event}
            last_used_code = self._add_tags(event, code, tags)
            code = last_used_code + 1
        tags = ['short', 'long', 'ontime']
        for event in all_deltas:
            self.event_to_code[event] = {'code': code}
            self.code_to_event[code] = {'event': event}
            last_used_code = self._add_tags(event, code, tags)
            code = last_used_code + 1


class FlaredownMapping(Mapping):

    def __init__(self):
        Mapping.__init__(self, "pattern_mining/data/mapping/flaredown/event_to_code.json",
                         "pattern_mining/data/mapping/flaredown/code_to_event.json")

    def _generate_mappings(self):
        '''
        creates event-number and number-event mappings for events in dataset
        events correspond to trackable_name in Flaredown dataset
        each entry includes tag corresponding to trackable_type

        * parent is added to keep consistent with post-processing classes, since the project was originally
            built solely for the airport dataset
        '''
        records = pd.read_csv("C:/Users/user/Downloads/archive/export_filtered.csv")
        pairs = records[['trackable_name', 'trackable_type']].drop_duplicates()

        code = 1
        for i, pair in pairs.iterrows():
            name = pair['trackable_name']
            tag = pair['trackable_type']
            self.event_to_code[name] = {'code': code, 'tag': tag, 'parent': name}
            self.code_to_event[code] = {'event': name, 'tag': tag, 'parent': code}
            code += 1


if __name__ == "__main__":
    mappings = AirportMapping()
