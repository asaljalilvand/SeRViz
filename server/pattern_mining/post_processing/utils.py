from functools import lru_cache
import pandas as pd
import pickle
import os
import math
from typing import Iterable, List, Tuple
from pattern_mining.post_processing.post_processing import parse_rules, remove_redundant_rules, get_sequences_per_rule, \
    get_pattern_by_id, parse_itemsets, get_sequences_per_fis
from pattern_mining.post_processing.rule_dag import RuleDAG
from pattern_mining.post_processing.itemset_graph import ItemsetGraph
from pattern_mining.pre_processing.dictionary import AirportMapping, FlaredownMapping
from pattern_mining.mining import spmf_manager

# global data ####################################################################################

# waiting for airport permission to use anonymous data
labels_df = pd.DataFrame() #pd.read_pickle("pattern_mining/data/HIAA_anonymized/labeled_sequences.pkl") # sequences removed, only ids (NDA)
delta_labels_df = pd.DataFrame() #pd.read_pickle("pattern_mining/data/HIAA_anonymized/labeled_deltas.pkl") # deltas removed, only ids (NDA)
flat_flight_tid = pd.DataFrame() #pd.read_csv("pattern_mining/data/HIAA_anonymized/turnaround_arr_dep_flights.csv")
weather_tid_df = pd.DataFrame() #pd.read_csv("pattern_mining/data/HIAA_anonymized/tid_weather.csv")
performance_detail_df = pd.DataFrame() #pd.read_csv("pattern_mining/data/HIAA_anonymized/performance_detail.csv")
delta_performance_detail_df = pd.DataFrame() #pd.read_csv("pattern_mining/data/HIAA_anonymized/delta_performance_detail.csv")
# Nan not a valid json literal, problems in parsing response in front-end
# performance_detail_df = performance_detail_df.where(pd.notnull(performance_detail_df), None)
# delta_performance_detail_df = delta_performance_detail_df.where(pd.notnull(delta_performance_detail_df), None)
ce_mapping = AirportMapping()

flaredown_df = pd.read_pickle("pattern_mining/data/flaredown/sequences.pkl")
user_demographics = pd.read_csv("pattern_mining/data/flaredown/user_demographics.csv")
fl_mapping = FlaredownMapping()


def _get_id_col(data: str) -> str:
    return 'Turnaround ID' if data == 'airport' else 'user_id'


def get_heatmap_series(flight_df: pd.DataFrame) -> dict:
    '''
    :param flight_df: flight information dataframe
    :return: dictionary of data series required for Plotly Javascript for calendar heatmap
    '''
    x = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    y = []
    z = []
    heatmap = pd.crosstab(flight_df.daytime, flight_df.weekday)
    for daytime, days in heatmap.iterrows():
        y.append(daytime)
        z.append([int(days[day]) for day in x if day in days])
    return {'x': x, 'y': y, 'z': z}


def df_to_nested(dataframe: pd.DataFrame, _groupby: list, level=0, col='count'):
    '''
    generates nested dataframe for sunburst graph in Plotly Javascript required format
    inspired by this post https://stackoverflow.com/q/50338778
    '''
    result = []

    if level == (len(_groupby) - 1):
        df = dataframe.groupby(_groupby[level])
        parent_cols = _groupby[:level]
        for key, val in df:  # Iterate through groups
            row = val.head(1)
            parents = "-".join(str(list(row[p])[0]) for p in parent_cols)
            result.append({'labels': key, 'values': int(val[col].sum()), 'parents': parents,
                           'ids': parents + "-" + str(key)})

    else:
        df = dataframe.groupby(_groupby[level])
        parent_cols = _groupby[:level]
        level += 1  # Level0 -> Level1 (increase level)
        for key, val in df:  # Iterate through groups
            if level == 1:
                parents = ""
                ids = key
            else:
                row = val.head(1)
                parents = "-".join(str(list(row[p])[0]) for p in parent_cols)
                ids = parents + "-" + str(key)

            result.append({'labels': key, 'values': int(val[col].sum()), 'parents': parents,
                           'ids': ids})
            result.extend(df_to_nested(val, _groupby, level, col))

        level -= 1  # Level1 -> Level0 (decrease level)

    return result


def get_sunburst_format(df: pd.DataFrame, levels: list) -> dict:
    '''
    :param df: dataframe for sunburst graph
    :param levels: category levels in sunburst
    :return: dictionary of data series for sunburst graph in Plotly Javascript required format
    '''
    tmp = df.copy()
    tmp['count'] = 1
    sunburst_data = df_to_nested(tmp, levels)
    sunburst_data = pd.DataFrame(sunburst_data)
    return {column: list(sunburst_data[column]) for column in sunburst_data.columns}


@lru_cache()
def get_performance(sequence_ids: list, pattern_items: list, rule=True,anonymized=True) -> dict:
    '''
    :param sequence_ids: turnaround ids
    :param pattern_items: items in rules/frequent itemsets that must be displayed in detail table in front-end
    :param rule: if table is for sequential rules
    :return: dictionary of rows and columns in format required for Vuetify data table
    '''
    if rule:
        prfmnc = performance_detail_df[performance_detail_df['Turnaround ID'].isin(sequence_ids)]
    else:
        prfmnc = delta_performance_detail_df[delta_performance_detail_df['Turnaround ID'].isin(sequence_ids)]

    if anonymized:
        return {
            'performance_rows': prfmnc.to_dict(orient='records'),
            'performance_columns': [{'value': col, 'text': col} for col in prfmnc.columns]
        }

    else:
        columns = ["Turnaround ID", "DATE", "AL", "A/C Type", "Stand", "Arr Sch Time",
               "Arr Act Time",
               "Dep Sch Time", "Dep Act Time", "weekday", "daytime", "Performance"]
        if 'duration' in prfmnc.columns:
            columns.append('duration')

        stat_cols = []
        for parent_code in pattern_items:
            parent_name = ce_mapping.code_to_event[str(parent_code)]['event']
            if parent_name == 'Aircraft entered stand':  # always 0, since it's the origin
                continue
            stat_cols.extend([parent_name, parent_name + " min", parent_name + " 0.4 quantile", parent_name + " median",
                          parent_name + " 0.6 quantile", parent_name + " max"])

        columns.extend(stat_cols)
        if 'sequence' in prfmnc.columns:
            columns.append('sequence')
        else:
            columns.append('delta_set')

    return {
        'performance_rows': prfmnc[columns].to_dict(orient='records'),
        'performance_columns': [{'value': col, 'text': col + " (s)" if col in stat_cols else col} for col in columns]
    }


def get_demo_map(user_ids) -> dict:
    '''
    :param user_ids: user ids in Flaredown dataset
    :return: dictionary of countries and count of users per country in Plotly choropleth map in Javascript
    '''
    users = user_demographics[user_demographics['user_id'].isin(user_ids)]
    country_count = users['country'].value_counts()
    return {'z': list(country_count), 'locations': list(country_count.index)}


@lru_cache()
def get_pc_format(seq_ids_per_pattern: List[list] = None) -> List[dict]:
    '''
    :param seq_ids_per_pattern: list where each element is a list of sequence ids
        if None, the return value is a list with one dictionary for the entire dataset
    :return: list of dictionaries of weather data series in format required by Plotly parallel coordinates in Javascript
    '''
    dimensions = []
    if seq_ids_per_pattern is None:
        medians = [weather_tid_df.median(numeric_only=True).astype(float).to_dict()]
    else:
        medians = [weather_tid_df[weather_tid_df['Turnaround ID'].isin(ids)].median(numeric_only=True).astype(float)
                       .to_dict()
                   for ids in seq_ids_per_pattern]

    for column in weather_tid_df.select_dtypes(exclude=['object']).columns:
        dimension = {'label': column,
                     'range': [weather_tid_df[column].min().astype(float),
                               weather_tid_df[column].max().astype(float)],
                     'values': [median[column] for median in medians]}
        dimensions.append(dimension)
    return dimensions


def remove_file(filename: str):
    try:
        os.remove(filename)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))


def mine_patterns(records: Iterable, support: int, confidence: int = None, window: int = None, itemset=False,
                  is_spmf_format=False) -> str:
    '''
    :param records: list of transactions/sequences
    :param support: support
    :param confidence: confidence (for sequential rules)
    :param window: window (for TRuleGrowth)
    :param itemset: if True mine frequent itemsets else mine sequential rules
    :param is_spmf_format: True indicates the transactions/sequences in list are already in SPMF input format
        else the spmf_manager will generate the appropriate input format
    :return: path of the SPMF output file
    '''
    input = spmf_manager.generate_input_file(records, itemset=itemset, is_spmf_format=is_spmf_format)
    try:
        if itemset:
            output_file = spmf_manager.run('FPGrowth_itemsets', input, str(support) + "%", itemset=True)
        else:
            output_file = spmf_manager.run('TRuleGrowth', input, str(support) + "%", str(confidence) + "%",
                                       window)
    except:
        remove_file(input)
        raise TypeError("java.lang.IllegalArgumentException")
    remove_file(input)
    return output_file


@lru_cache()
def get_sequences_by_pattern_id(all_patterns: list, pattern_ids: list, detailed: bool = False, rule=True) -> Tuple:
    '''
    :param all_patterns: list of Rule/FrequentItemSet objects
    :param pattern_ids: list of pattern ids, used for filtering all_patterns
    :param detailed: if True, list of all items used in the filtered patterns is returned, used for front-end detail table
    :param rule: if the patterns are sequential rules or frequent itemsets
    :return: tuple of the following
        - all sequence/transaction ids related to filtered patterns
        - sequence/transaction ids per pattern
        - all unique items used in patterns
    '''
    sequence_ids = set()
    seq_ids_per_pattern = []
    pattern_items = set()

    for pattern_id in pattern_ids:
        pattern = get_pattern_by_id(all_patterns, pattern_id)
        sequence_ids.update(pattern.seq_ids)
        seq_ids_per_pattern.append(tuple(pattern.seq_ids))
        if detailed:
            if rule:
                pattern_items.update([ce_mapping.code_to_event[str(item)]['parent'] for item in pattern.LHS])
                pattern_items.add(ce_mapping.code_to_event[str(pattern.RHS)]['parent'])
            else:
                pattern_items.update([ce_mapping.code_to_event[str(item)]['parent'] for item in pattern.items])

    return tuple(sequence_ids), tuple(seq_ids_per_pattern), tuple(pattern_items)


@lru_cache()
def get_views_by_sequence_ids(sequence_ids: list = None, seq_ids_per_pattern: List[list] = None,
                              data='airport') -> Tuple:
    '''
    :param sequence_ids: sequence/transaction ids, if None, graph data uses all airport dataset
    :param seq_ids_per_pattern: sequence/transaction ids per pattern
    :param data: dataset identifier: 'airport' or 'flaredown'
    :return: data in front-end required format
        airport data: sunburst, heatmap, parallel coordinates and performance
        flaredown data: sunburst and map, only for all the records
    '''
    if data == 'flaredown':
        sunburst = get_sunburst_format(user_demographics[user_demographics['user_id'].isin(sequence_ids)],
                                       ['sex', 'age_group'])
        map_series = get_demo_map(sequence_ids)
        return sunburst, map_series, {}

    if sequence_ids is None:
        # show all the sequences info
        sunburst = get_sunburst_format(flat_flight_tid, ['Stand', 'Performance', 'AL', 'A/C Type'])
        time_dist_heatmap = get_heatmap_series(flat_flight_tid)

    else:
        flights = flat_flight_tid[flat_flight_tid['Turnaround ID'].isin(sequence_ids)]
        time_dist_heatmap = get_heatmap_series(flights)
        sunburst = get_sunburst_format(flights, ['Stand', 'Performance', 'AL', 'A/C Type'])

    pc = get_pc_format(seq_ids_per_pattern)
    return sunburst, time_dist_heatmap, pc


@lru_cache()
def get_tids_from_query(filter: dict, data='airport') -> set:
    '''
    :param filter: filtering options for sequences/transactions
    :param data: dataset identifier: 'airport' or 'flaredown'
    :return: set of sequence/transaction ids
    '''
    if data == 'airport':
        return filter_airport_records(filter)
    return filter_flaredown_records(filter)


@lru_cache()
def filter_flaredown_records(filter: dict) -> set:
    '''
    :param filter: filtering options for sequences/transactions in Flaredown
    :return: set of user ids filtered by age, sex and country
    '''
    age_group = filter['age']
    sex = filter['sex']
    countries = filter['countries']
    ids = set(user_demographics.query("age_group in @age_group & sex in @sex")['user_id'])
    if len(countries) != 0:
        ids = ids.intersection(
            user_demographics.query("country in @countries")['user_id'])
    return ids


@lru_cache()
def filter_airport_records(filter: dict) -> set:
    '''
    :param filter: filtering options for sequences/transactions in airport dataset
    :return: set of turnaround ids filtered by stand, airline and weather condition range
    '''
    stand = filter['stand']
    airline = filter['airline']
    at_min = filter['at'][0]
    at_max = filter['at'][1]
    gt_min = filter['gt'][0]
    gt_max = filter['gt'][1]
    rh_min = filter['humid'][0]
    rh_max = filter['humid'][1]

    ids = set()
    ids.update(flat_flight_tid.query("Stand in @stand & AL in @airline")['Turnaround ID'])
    ids = ids.intersection(
        weather_tid_df.query("AT>=@at_min & AT<=@at_max & GT>=@gt_min & GT<=@gt_max & RH>=@rh_min & RH<=@rh_max")
        ['Turnaround ID'])
    return ids


def filter_by_event(sequences_df: pd.DataFrame, event_filters: list, data='airport') -> pd.DataFrame:
    '''
    :param sequences_df: sequences/transactions meta information dataframe
    :param event_filters: filtering options for sequences/transactions
    :param data: dataset identifier: 'airport' or 'flaredown'
    :return: dataframe of filtered turnaround/users
    '''
    if data == 'airport':
        return filter_by_event_code(sequences_df, event_filters, 'Sequence')
    else:
        return filter_by_event_name(sequences_df, event_filters, 'Sequence_flat')


def filter_by_event_code(sequences_df: pd.DataFrame, event_filters: list, seq_col: str,
                         all_filters=True) -> pd.DataFrame:
    '''
    :param sequences_df: dataframe of transactions/sequences
    :param event_filters: list of item/event number codes for filtering transactions/sequences
    :param seq_col: transaction/sequence column in dataframe
    :param all_filters: if True each transaction/sequence must contain all elements of event_filters else at least one
    :return: dataframe of filtered turnaround/users
    '''
    if len(event_filters) == 0:
        return sequences_df

    return sequences_df[
        sequences_df[seq_col].apply(
            lambda sequence: all(int(event) in sequence for event in event_filters) if all_filters else
            any(int(event) in sequence for event in event_filters))]


def filter_by_event_name(sequences_df: pd.DataFrame, event_filters: list, seq_col: str) -> pd.DataFrame:
    '''
    filters records by item/event names. The match is not strict and is done by checking if the filters are substrings
        of record item/event names. Any record that has at least one match is included.

    :param sequences_df: ataframe of transactions/sequences
    :param event_filters: list of item/event names for filtering transactions/sequences
    :param seq_col: transaction/sequence column in dataframe
    :return: dataframe of filtered turnaround/users
    '''
    codes = []
    if (len(event_filters) == 0 or all(
            len(event) == 0 for event in event_filters)):  # empty list or list of empty strings
        return sequences_df

    for event in event_filters:
        if len(event) != 0:
            codes.extend([value['code'] for key, value in fl_mapping.event_to_code.items() if event in key.lower()])

    if len(codes) == 0:  # query didn't match anything in the dictionary
        return pd.DataFrame()
    return filter_by_event_code(sequences_df, codes, seq_col, all_filters=False)


def get_df_setup(data='airport', itemset=False) -> Tuple[pd.DataFrame, str, bool]:
    '''
    :param data: dataset identifier: 'airport' or 'flaredown'
    :param itemset: if the transaction dataframe should be returned or sequence
    :return: dataframe of records for mining, column of records, if the records are already in SPMF input format
    '''
    if data == 'flaredown':
        sequences_df = flaredown_df
        seq_col = 'spmf_transaction_line' if itemset else 'spmf_sequence_line'
        is_spmf_format = True
    else:
        sequences_df = delta_labels_df if itemset else labels_df
        seq_col = 'Sequence'
        is_spmf_format = False
    return sequences_df, seq_col, is_spmf_format


@lru_cache()
def get_sequential_rules(config: dict = None, filter: dict = None, allow_too_many=False, remove_redundant=True,
                         data='airport') -> Tuple[list, list]:
    '''
    :param config: data mining configuration
    :param filter: sequence filtering configuration
    :param allow_too_many: allow parsing of high number of patterns. If False, function returns without post-processing
    :param remove_redundant: if True, removes redundant rules in post-processing
    :param data: dataset identifier: 'airport' or 'flaredown'
    :return: list of Rule objects and list of sequence ids used for data mining
    '''
    sequences_df, seq_col, is_spmf_format = get_df_setup(data, False)

    #NDA restrictions
    if data=='airport':
        with open('pattern_mining/data/HIAA_anonymized/rules.pkl', 'rb') as f:
            rules = pickle.load(f)

    else:
        if config is not None:
            support = config['support']
            confidence = config['confidence']
            window = config['window']
            if filter is not None:
                filtered_tids = get_tids_from_query(filter, data)
                sequences_df = sequences_df[sequences_df[_get_id_col(data)].isin(filtered_tids)]
                sequences_df = filter_by_event(sequences_df, filter['events'], data=data)
                print("#sequences after filtering: " + str(sequences_df.shape[0]))
                if sequences_df.shape[0] == 0:
                    return [], []
            output_file = mine_patterns(list(sequences_df[seq_col]), support=support, confidence=confidence, window=window,
                                    is_spmf_format=is_spmf_format)
        else:
            output_file = "pattern_mining/data/spmf/TRuleGrowth_out.txt"

        # Rule Parsing and Matrix generation
        print('start parsing the rules')
        rules = parse_rules(output_file)
        if config is not None: remove_file(output_file)
        print(str(len(rules)) + " before redundancy removal")
        if len(rules) > 2000 and not allow_too_many:
            return None, None
        if remove_redundant:
            rules = remove_redundant_rules(rules)
        print(str(len(rules)) + " after redundancy removal")
        rules = get_sequences_per_rule(rules, sequences_df, data=data)

    return rules, sequences_df[_get_id_col(data)]


@lru_cache()
def get_rules_graph_matrix_views(rules: list, s_ids: list, data='airport') -> dict:
    '''
    :param rules: list of Rule objects
    :param s_ids: list of sequence ids used for data mining
    :param data: dataset identifier: 'airport' or 'flaredown'
    :return: dictionary of DAG forest, rule matrices and data series for distribution analysis in front-end
    '''
    sequences_df = labels_df if data == 'airport' else flaredown_df
    sequences_df = sequences_df[sequences_df[_get_id_col(data)].isin(s_ids)]

    # DAG matrices
    print("generating DAGS")
    rd = RuleDAG(tagged=False, data=data)
    matrices, full_graph = rd.create_matrices(rules, cluster=False, id_as_column=True)
    print(str(len(matrices)) + " matrices found")

    view1_list = []
    view2_list = []
    view3_list = []
    if len(matrices) == 0 or data == 'flaredown':
        # if no rules found, show all the sequences info
        view1, view2, view3 = get_views_by_sequence_ids(tuple(sequences_df[_get_id_col(data)]), data=data)
        view1_list.append(view1)
        view2_list.append(view2)
        view3_list.append(view3)

    else:
        for matrix in matrices:
            rule_ids = matrix.index
            sequence_ids, seq_ids_per_pattern, pattern_items = get_sequences_by_pattern_id(tuple(rules),
                                                                                           tuple(rule_ids))
            view1, view2, view3 = get_views_by_sequence_ids(sequence_ids, seq_ids_per_pattern)
            view1_list.append(view1)
            view2_list.append(view2)
            view3_list.append(view3)

    # for the front-end, remove rid, and convert each row to dictionary
    headers = [list(m.columns) for m in matrices]
    for i in range(len(headers)):
        headers[i] = [c for c in headers[i] if c not in ["rid", "level", "group"]]

    for i in range(len(matrices)):
        group_rows = []
        for g in matrices[i]['group'].unique():
            new_row = {c: "" for c in matrices[i].columns}
            new_row['group'] = g
            new_row['level'] = 0
            group_rows.append(new_row)
        matrices[i] = pd.concat([matrices[i], pd.DataFrame(group_rows)])
        matrices[i] = matrices[i].to_dict(orient='records')

    views_dict = {
        'overview': full_graph,
        'rule_matrices': matrices,
        'matrices_columns': headers,
        'time_dist_heatmaps': view2_list,
        'sunbursts': view1_list,
        'pc': view3_list,
        'maps': view2_list,
        'count': {'s': sequences_df.shape[0], 'r': len(rules)}
    }
    return views_dict


@lru_cache()
def get_frequent_itemsets(config: dict = None, filter: dict = None, data='airport') -> tuple:
    '''
    :param config: data mining configuration
    :param filter: transaction filtering configuration
    :param data: dataset identifier: 'airport' or 'flaredown'
    :return: list of FrequentItemSet objects and list of transaction ids used for data mining
    '''
    sequences_df, seq_col, is_spmf_format = get_df_setup(data, True)

    if data=='airport':
        with open('pattern_mining/data/HIAA_anonymized/fis.pkl', 'rb') as f:
            freqitemsets = pickle.load(f)

    else:
        if config is not None:
            support = config['support']
            if filter is not None:
                filtered_tids = get_tids_from_query(filter, data)
                sequences_df = sequences_df[sequences_df[_get_id_col(data)].isin(filtered_tids)]
                sequences_df = filter_by_event(sequences_df, filter['events'], data=data)
                print("#sequences after filtering: " + str(sequences_df.shape[0]))
                if sequences_df.shape[0] == 0:
                    return [], []
            output_file = mine_patterns(list(sequences_df[seq_col]), support=support, itemset=True,
                                    is_spmf_format=is_spmf_format)
        else:
            output_file = "pattern_mining/data/spmf/FPGrowth_itemsets_out.txt"

        freqitemsets = parse_itemsets(output_file)
        if config is not None: remove_file(output_file)
        freqitemsets = get_sequences_per_fis(freqitemsets, sequences_df, data=data)

    return freqitemsets, sequences_df[_get_id_col(data)]


@lru_cache()
def get_fis_matrix_views(fis: list, s_ids: list, data='airport') -> dict:
    '''
    :param fis: list of FrequentItemSet objects
    :param s_ids: list of transaction ids used for data mining
    :param data: dataset identifier: 'airport' or 'flaredown'
    :return: dictionary of pattern matrix and data series for distribution analysis in front-end
    '''
    matrix = ItemsetGraph(data=data).create_matrix(fis)
    headers = [c for c in matrix.columns if c not in ["rid", "level", "group", "support"]]
    headers.append("support")  # must be the last one on front end!
    view1, view2, view3 = get_views_by_sequence_ids(s_ids, data=data)
    return {
        'rule_matrices': [matrix.to_dict(orient='records')],
        'matrices_columns': [headers],
        'time_dist_heatmaps': [view2],
        'sunbursts': [view1],
        'pc': [view3],
        'maps': [view2],
        'count': {'s': len(s_ids), 'r': len(fis)},
        'toomany': '0'
    }


@lru_cache()
def get_filter_options(data='airport') -> dict:
    '''
    :param data: dataset identifier: 'airport' or 'flaredown'
    :return: filtering options for datasets
    '''
    if data == 'airport':
        return {
            'events': [{'value': code, 'text': d['event']} for code, d in ce_mapping.code_to_event.items() if
                       'parent' in d],
            'stand': [int(stand) for stand in flat_flight_tid['Stand'].unique()],
            'airline': list(flat_flight_tid['AL'].unique()),
            'at': {'min': int(math.floor(weather_tid_df['AT'].min())),
                   'max': int(math.ceil(weather_tid_df['AT'].max()))},
            'gt': {'min': int(math.floor(weather_tid_df['GT'].min())),
                   'max': int(math.ceil(weather_tid_df['GT'].max()))},
            'humid': {'min': int(math.floor(weather_tid_df['RH'].min())),
                      'max': int(math.ceil(weather_tid_df['RH'].max()))},
        }
    return {
        'age': list(user_demographics['age_group'].unique()),
        'sex': list(user_demographics['sex'].unique()),
        'country': list(user_demographics['country'].unique())
    }


class HDict(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))


if __name__ == '__main__':
    pass