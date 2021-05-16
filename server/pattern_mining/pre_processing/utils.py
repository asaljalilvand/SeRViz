import pandas as pd
import numpy as np
from datetime import datetime
import json
import calendar
from typing import List, Tuple
from pattern_mining.pre_processing.dictionary import AirportMapping


def gate_turnaround_duration(gate_df: pd.DataFrame, unit='hour') -> pd.DataFrame:
    '''
    :param gate_df: Assaia turnaround event log dataframe
    :param unit: duration unit: day, hour, min, sec
    :return: dataframe with two columns: turnaround id - duration
    '''
    grouped = gate_df.groupby('Turnaround ID')
    turnaround_duration = []
    for group in grouped:
        rows = group[1].reset_index()
        duration = get_absolute_time_difference(rows.iloc[0]['Timestamp'], rows.iloc[-1]['Timestamp'], unit)
        turnaround_duration.append([group[0], duration])
    turnaround_duration_df = pd.DataFrame(turnaround_duration, columns=['Turnaround ID', 'duration'])
    return turnaround_duration_df


def get_absolute_time_difference(time1: datetime, time2: datetime, unit='sec'):
    '''
    :param time1: datetime value
    :param time2: datetime value
    :param unit: difference unit: day, hour, min , sec
    :return: absolute time difference
    '''
    difference = time1 - time2 if time1 > time2 else time2 - time1
    if unit == 'min':
        return int(difference.total_seconds() / 60.0)
    elif unit == 'hour':
        return difference.total_seconds() // 3600
    elif unit == 'day':
        return difference.days
    return difference.total_seconds()


def remove_overnight(turnaround_df: pd.DataFrame, overnight_hour=6) -> pd.DataFrame:
    '''
    removes turnarounds with duration longer than overnight_hour from logs
    '''
    duration_df = gate_turnaround_duration(turnaround_df)
    overnight_flights = list(duration_df[duration_df['duration'] >= overnight_hour]['Turnaround ID'])
    return turnaround_df[~turnaround_df['Turnaround ID'].isin(overnight_flights)].copy()


def flatten_turnarounds(turnaround_df: pd.DataFrame) -> Tuple[pd.DataFrame, List]:
    '''
    :param turnaround_df: Assaia turnaround log, each row is one event
    :return: turnaround log with each turnaround as a row, events as columns
    '''
    columns = list(turnaround_df['Type'].unique())
    length = len(turnaround_df['Turnaround ID'].unique())
    flattened = pd.DataFrame(np.nan, index=[i for i in range(length)], columns=columns)
    flattened['Turnaround ID'] = '-'
    groups = turnaround_df.groupby('Turnaround ID')
    index = 0
    for t in groups:
        flattened.at[index, 'Turnaround ID'] = t[0]
        for i, e in t[1].iterrows():
            type = e['Type']
            flattened.at[index, type] = e['Timestamp']
        index += 1
    flattened[columns] = flattened[columns].apply(pd.to_datetime)
    return flattened, columns


def merge_flights(gate_df_dict: dict, flights_df: pd.DataFrame) -> pd.DataFrame:
    '''
    merges turnaround log with flight information. matches by timestamp, gate, arrival and departure

    :param gate_df_dict: dictionary of logs. key=gate number, value:log dataframe
    :param flights_df: flight info for the time period of log collection
    :return: one dataframe of merged logs with flights
    '''

    # Placeholder for T-ID
    flights_df['Turnaround ID'] = '-'
    flights_df['Performance'] = '-'

    for index, flight in flights_df.iterrows():

        # Required information for finding a match in gate dfs
        movement_type = flight['A/D']  # ARR or DEP
        fdate = flight['DATE']
        stand = flight['Stand']
        actual_time = flight['Act Time']
        fdatetime = datetime.combine(fdate, actual_time)
        match_col = 'Aircraft entered stand' if movement_type == 'ARR' else 'Aircraft left stand'
        threshold = 5 * 60  # 5 minutes

        gate_df = gate_df_dict[stand]
        match = gate_df[gate_df[match_col].dt.date == fdate]  # find same date
        for i, m in match.iterrows():  # find almost same time
            if (get_absolute_time_difference(fdatetime, m[match_col]) <= threshold):
                flights_df.at[index, 'Turnaround ID'] = m['Turnaround ID']
                flights_df.at[index, 'Performance'] = m['Performance']
                break

    # Remove unmatched flights
    flights_df = flights_df[flights_df['Turnaround ID'] != '-']

    return flights_df


def find_performance(flatten_gate: pd.DataFrame, original_gate: pd.DataFrame) -> pd.DataFrame:
    '''
    :param flatten_gate: dataframe with one row per turnaround and events as columns
    :param original_gate: Assaia log with one row per event
    :return: flatten_gate with a new column showing performance as H=high or L=low
    '''
    df = flatten_gate.merge(gate_turnaround_duration(original_gate, unit='min'), on=('Turnaround ID'))
    df['Performance'] = np.where(df['duration'] <= 75, 'H', 'L')
    return df


def flatten_flights(flight_tid_df: pd.DataFrame) -> pd.DataFrame:
    '''
    flight information is recoreded as one row per arrival/departure. flight number might be different for the two
    this function builds one row per flight with all arrival/departure info

    :param flight_tid_df: flight-turnaround dataframe, one row per arrival/departure
    :return: dataframe with one row per turnaround with both arrival and departure flight information
    '''
    result = []
    columns = ['DATE', 'AL', 'A/C Type', 'Stand', 'Turnaround ID', 'Performance',
               'Arr Flight', 'Arr City', 'Arr Sch Time', 'Arr Est Time', 'Arr Act Time',
               'Dep Flight', 'Dep City', 'Dep Sch Time', 'Dep Est Time', 'Dep Act Time',
               'weekday', 'daytime']
    for id in flight_tid_df['Turnaround ID'].unique():
        arrival = flight_tid_df[(flight_tid_df['Turnaround ID'] == id) & (flight_tid_df['A/D'] == 'ARR')]
        departure = flight_tid_df[(flight_tid_df['Turnaround ID'] == id) & (flight_tid_df['A/D'] == 'DEP')]

        # if a turnaround has both ARR, key info. will come from arrival, else departure
        key_info = False
        row = []
        hour = -1
        if len(arrival) != 0:
            arrival = arrival.iloc[0]
            row.extend(
                [arrival['DATE'], arrival['AL'], arrival['A/C Type'], arrival['Stand'], id, arrival['Performance'],
                 arrival['Flight'], arrival['City'], arrival['Sch Time'], arrival['Est Time'], arrival['Act Time']])
            key_info = True
            hour = arrival['Act Time'].hour

        if len(departure) != 0:
            departure = departure.iloc[0]
            if not key_info:
                row.extend([departure['DATE'], departure['AL'], departure['A/C Type'], departure['Stand'], id,
                            departure['Performance']])
                row.extend([np.NaN] * 5)  # arrival info missing
                hour = departure['Act Time'].hour
            row.extend([departure['Flight'], departure['City'], departure['Sch Time'], departure['Est Time'],
                        departure['Act Time']])
        else:
            row.extend([np.NaN] * 5)
        weekday = calendar.day_name[row[0].weekday()]
        if (hour >= 5) and (hour < 12):
            daytime = 'morning'
        elif (hour >= 12) and (hour < 17):
            daytime = 'afternoon'
        elif (hour >= 17) and (hour < 21):
            daytime = 'evening'
        else:
            daytime = 'night'
        row.extend([weekday, daytime])
        result.append(row)

    return pd.DataFrame(result, columns=columns)


def get_delta_from_origin(gate_df: pd.DataFrame, events_columns: List, origin='Aircraft entered stand',
                          time_all_from_origin=True) -> pd.DataFrame:
    '''
    time events from an origin in seconds

    :param gate_df: flat turnarounds dataframe
    :param events_columns: subset of the columns of the dataframe that include event timestamps
    :param origin: set if all events must be timed from the same origin
    :param time_all_from_origin: set if all events must be timed from the same origin
    :return: dataframe where the values in event colums are time difference from the origin in seconds
    '''
    delta_df = gate_df.copy()
    outliers = set()
    end_start_dict = {'closed': 'open', 'disconnected': 'connected', 'left stand': 'entered stand', 'connected': origin}
    for i, row in delta_df.iterrows():
        for c in events_columns:
            if pd.isna(delta_df.loc[delta_df.index[i], c]):
                continue
            delta = np.nan
            if not time_all_from_origin and row['Performance'] == 'L' and any(
                    [key in c for key in end_start_dict.keys()]):
                # the goal of this part is when seeing events like "passenger door closed", something left stand, etc.,
                # find the appropriate starting point to time it from.
                # for example, the fuelling related things should be timed from when the fueller has entered the stand.
                # Those starting points themselves, should be timed from aircraft entered stand.
                for key in end_start_dict.keys():
                    if key in c:
                        entity = c[:(
                            c.find(key))]  # for example, "fueller" part from "fueller on stand" or "fueller connected"
                        if (entity + 'entered stand') in events_columns:
                            timing_origin = entity + 'entered stand'

                        elif (
                                entity + 'on stand') in events_columns:  # this one is for fuelling events, that unlike others, the verb is "on stand" instead of "entered stand".
                            timing_origin = entity + 'on stand'
                        elif key == 'connected':  # such as Aft highloader connected. it doesn't have any "entered stand" type of
                            # events. it's just connecting and disconnecting. so the connecting part should be timed from "Aircraft entered stand"
                            # the reason I check connected is that, for some things, like Aft highloader, there are just connect/disconnect.
                            # But for Aft starboard catering, it enters stand, connects, disconnects and then leaves.
                            timing_origin = end_start_dict[key]
                        else:
                            timing_origin = entity + end_start_dict[key]
                        delta = (row[c] - row[timing_origin]).total_seconds()
                        if delta < -60:
                            print("outlier: " + timing_origin + " " + str(row[timing_origin]) + " --> " + c + " " + str(
                                row[c]) + " " + row['Turnaround ID'])
                            outliers.add(row['Turnaround ID'])
                        break
            else:
                delta = (row[c] - row[origin]).total_seconds()
                if delta < -300:
                    print("outlier: " + origin + " " + str(row[origin]) + " --> " + c + " " + str(row[c]) + " " + row[
                        'Turnaround ID'])
                    outliers.add(row['Turnaround ID'])

            delta_df.at[i, c] = delta
    if len(outliers) > 0:
        print("Removing #" + str(len(outliers)) + " turnarounds with negative deltas")
        delta_df = delta_df[~delta_df['Turnaround ID'].isin(outliers)]

    return delta_df


def get_order_of_event_by_timestamp(turnaround_id: str, original_df: pd.DataFrame) -> List:
    '''
    :param turnaround_id: id of turnaround
    :param original_df: Assaia log
    :return: the chronological order of events for the turnaround with turnaround_id
    '''
    events = original_df.loc[original_df['Turnaround ID'] == turnaround_id]
    events = events.sort_values(by='Timestamp')
    unique_events = []
    for event in events['Type']:
        if event not in unique_events:
            unique_events.append(event)
    return unique_events


def get_status(scheduled: datetime.time, actual: datetime.time, date: datetime.date) -> str:
    '''
    get flight status by comparing actual vs scheduled arrival/departure
    :param scheduled: scheduled time of arrival/departure
    :param actual: actual time of arrival/departure
    :param date: arrival/departure date
    :return: status: delayed, ontime or early
    '''
    scheduled = datetime.combine(date, scheduled)
    actual = datetime.combine(date, actual)
    diff = (scheduled - actual).total_seconds() / 60
    if diff < -15:
        return 'delayed'
    if diff >= -15 and diff < 15:
        return 'ontime'
    return 'early'


def label_turnarounds(gate_df_dict: dict, flights_df: pd.DataFrame, delta=False, time_all_from_origin=True,
                      group_by_performance=False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    '''
    labels turnaround events as "delayed", "ontime", or "early"

    :param gate_df_dict: dictionary of flat logs/deltas. key=gate number, value:flat log dataframe
    :param flights_df: dataframe with turnaround id and flight information (generated by flatten_flights function)
    :param delta: if gate_dfs are delta or turnarounds sequences
    :param time_all_from_origin: if all events must be timed from the same origin (Aircraft entered stand) for labelling
    :param group_by_performance: if performance should be counted for labelling
    :return: tuple of dataframe, first is the labelled turnarounds all in one dataframe, second is statistical details
        used for labelling
    '''
    label_table = []
    detail_table = []
    statistics = {}
    counter = 0
    if delta:
        detail_key = 'delta_set'
    else:
        detail_key = 'sequence'
    map = AirportMapping()
    for key, value in gate_df_dict.items():
        flights = flights_df[flights_df['Stand'] == key]
        gate = value['df_flat']
        event_types = value['event_types']
        if delta:
            raw = None
            fd = gate.merge(flights, on=('Turnaround ID'), suffixes=('', '_y'))
        else:
            raw = value['df_raw']
            print(key)
            deltas = get_delta_from_origin(gate, event_types, time_all_from_origin=time_all_from_origin)
            fd = deltas.merge(flights, on=('Turnaround ID'), suffixes=('', '_y'))
        if "Performance_y" in fd.columns:
            fd.drop(columns=['Performance_y'], inplace=True)

        group_criteria = ['AL', 'A/C Type', 'weekday', 'daytime']
        if group_by_performance:
            group_criteria.append("Performance")
        groups = fd.groupby(group_criteria)
        for group in groups:
            df = group[1]
            event_stat = {}
            for event in event_types:
                if event in df.columns:
                    event_stat[event] = {'lower': round(df[event].quantile(.33), 2),
                                         'upper': round(df[event].quantile(.66), 2),
                                         'min': df[event].min(), 'max': df[event].max(),
                                         'median': round(df[event].quantile(.5), 2)}
            group_meta_info = {'carrier': group[0][0], 'aircraft': group[0][1], 'weekday': group[0][2],
                               'daytime': group[0][3], 'events': event_stat, 'gate': key}

            for i, e in df.iterrows():
                sequence = []
                sequence_string = ""  # used for front-end, stored to save process time in live demo
                detail = e.to_dict()
                detail['stat_group_id'] = counter
                if not delta:
                    timely_ordered_events = get_order_of_event_by_timestamp(e['Turnaround ID'], raw)
                else:
                    timely_ordered_events = event_types

                for event in timely_ordered_events:
                    if event in df.columns and (not np.isnan(e[event])):
                        lower_bound = event_stat[event]['lower']
                        upper_bound = event_stat[event]['upper']
                        detail.update({event + " 0.4 quantile": lower_bound, event + " 0.6 quantile": upper_bound,
                                       event + " min": event_stat[event]['min'],
                                       event + " max": event_stat[event]['max'],
                                       event + " median": event_stat[event]['median']})
                        if event == 'Aircraft entered stand' and (not pd.isna(e['Arr Sch Time'])):
                            tag = get_status(e['Arr Sch Time'], e['Arr Act Time'], e['DATE'])
                            sequence.append(map.event_to_code[tag + " " + event]['code'])
                            sequence_string = sequence_string + "|" + (tag + " " + event)
                            continue
                        elif event == 'Aircraft left stand' and (not pd.isna(e['Dep Sch Time'])):
                            tag = get_status(e['Dep Sch Time'], e['Dep Act Time'], e['DATE'])
                            sequence.append(map.event_to_code[tag + " " + event]['code'])
                            sequence_string = sequence_string + "|" + (tag + " " + event)
                            continue
                        if e[event] < lower_bound:
                            if delta:
                                sequence.append(map.event_to_code['short ' + event]['code'])
                                sequence_string = sequence_string + "|" + ('short ' + event)
                            else:
                                sequence.append(map.event_to_code['early ' + event]['code'])
                                sequence_string = sequence_string + "|" + ('early ' + event)
                        elif e[event] > upper_bound:
                            if delta:
                                sequence.append(map.event_to_code['long ' + event]['code'])
                                sequence_string = sequence_string + "|" + ('long ' + event)
                            else:
                                sequence.append(map.event_to_code['delayed ' + event]['code'])
                                sequence_string = sequence_string + "|" + ('delayed ' + event)
                        else:
                            sequence.append(map.event_to_code['ontime ' + event]['code'])
                            sequence_string = sequence_string + "|" + ('on-time ' + event)

                label_table.append([e['Turnaround ID'], np.array(sequence), counter])

                detail[detail_key] = sequence_string
                detail_table.append(detail)

            statistics[counter] = group_meta_info
            counter += 1

    with open("pattern_mining/data/HIAA/statistics.json", 'w') as outfile:
        json.dump(statistics, outfile, indent=4)

    return pd.DataFrame(label_table, columns=['Turnaround ID', 'Sequence', 'Statistics Group ID']), \
           pd.DataFrame(detail_table)


def get_tid_weather(flat_gate: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    '''
    finds weather condition for each turnaround by finding the weather recorded nearest to start of the turnaround

    :param flat_gate: flat turnaround log - one row per turnaround
    :param weather: weather dataframe
    :return: dataframe with weather information and turnaround ID
    '''
    merged_df = pd.merge_asof(left=flat_gate, right=weather, left_on='Aircraft entered stand', right_on='timestamp',
                              direction='nearest')
    columns = list(weather.columns)
    columns.append('Turnaround ID')
    return merged_df[columns].copy()


def get_match_in_delta_dict(a_closing: str, b_starting: str, tA: pd.DataFrame, tD: pd.DataFrame) -> Tuple:
    '''
    tA and tD are dataframes of events of the same turnaround, sorted ascending and descending, respectfully.
    this function tries to find a match in the turnaround with a_closing in tA and b_starting in tB

    :param a_closing:the closing event of service "a" logged by Assaia, for example, for boarding service, passenger
        door closed is the closing event
    :param b_starting:the start of the next service, for example, for pushback service, the first event that is logged
        is Pushback started
    :param tA: chronologically ascending events of turnaround
    :param tD: chronologically descending events of turnaround
    :return: paired match rows if found, else None tuple
    '''
    for i, e1 in tD.iterrows():
        for i2, e2 in tA.iterrows():
            if e1['Type'] == a_closing and e2['Type'] == b_starting:
                return e1, e2
    return None, None


def get_delta_df(gate_df: pd.DataFrame, delta_dictionary: dict) -> pd.DataFrame:
    '''
    finds pairs of events in turnarounds if they exist in the sequence

    :param gate_df: Assaia log dataframe
    :param delta_dictionary: key=delta name, value=dict of start and end of services
    :return: dataframe with one row per delta
    '''
    turnarounds = gate_df.groupby('Turnaround ID')
    deltas = []
    for t in turnarounds:
        tA = t[1].sort_values(by='Timestamp')
        tD = t[1].sort_values(by='Timestamp', ascending=False)
        for key, val in delta_dictionary.items():
            e1, e2 = get_match_in_delta_dict(val['a_closing'], val['b_starting'], tA, tD)
            if e1 is None or e2 is None:
                continue
            delta = get_absolute_time_difference(e1['Timestamp'], e2['Timestamp'])
            deltas.append(
                [t[0], key, e1['Timestamp'], e2['Timestamp'], delta])
    deltas_df = pd.DataFrame(deltas, columns=['Turnaround ID', 'name', 'start', 'end', 'duration'])
    return deltas_df


def flatten_delta(delta_df: pd.DataFrame) -> pd.DataFrame:
    '''
    :param delta_df: delta dataframe, one row per delta
    :return: delta dataframe, one row per turnaround, deltas as columns
    '''
    delta_names = list(delta_df['name'].unique())
    length = len(delta_df['Turnaround ID'].unique())
    flattened = pd.DataFrame(None, index=[i for i in range(length)], columns=(['Turnaround ID'] + delta_names))
    flattened['Turnaround ID'] = pd.Series(['-'] * length)
    groups = delta_df.groupby('Turnaround ID')
    index = 0
    for t in groups:
        flattened.at[index, 'Turnaround ID'] = t[0]
        for i, e in t[1].iterrows():
            type = e['name']
            # if pd.isna( flattened.loc[index, type]):
            flattened.at[index, type] = e['duration']
        index += 1
    return flattened
