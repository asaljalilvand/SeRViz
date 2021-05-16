import pandas as pd
from pycountry_convert import country_alpha2_to_country_name
from pattern_mining.pre_processing.dictionary import FlaredownMapping
from pattern_mining.mining.spmf_manager import generate_input_line_from_list

def age_group(age):
    '''
    :param age: number
    :return: age group: chile, youth, adult, senior or invalid
    group definition based on https://www.statcan.gc.ca/eng/concepts/definitions/age2
    '''

    if age >= 0 and age < 15:
        return "child"
    elif age >= 15 and age < 25:
        return "youth"
    elif age >= 25 and age < 65:
        return "adult"
    elif age >= 65 and age < 130:
        return "senior"
    return "invalid"


def hbi_score(value):
    '''
    :param value: HBI score (number in range [0,30])
    :return: Disease severity class based on
        https://badgut.org/information-centre/a-z-digestive-topics/assessing-ibd/
    '''
    value = int(value)
    if value < 5:
        return "Remission"
    elif value >= 5 and value < 7:
        return "Mild Disease"
    elif value >= 8 and value < 16:
        return "Moderate Disease"
    return "Severe Disease"


df = pd.read_csv("C:/Users/user/Downloads/archive/export.csv")
df['user_id'] = pd.Categorical(df['user_id'])
df['user_id'] = df.user_id.cat.codes

# user demographics
demo_df = df[['user_id', 'age', 'sex', 'country']].drop_duplicates()
demo_df['age_group'] = demo_df['age'].apply(age_group)
demo_df = demo_df[demo_df['age_group'] != 'invalid']
demo_df = demo_df[~demo_df['country'].isna()]
demo_df = demo_df[~demo_df['sex'].isna()]
# convert country alpha2 codes to country names for plotly map in front-end
demo_df['country'] = demo_df['country'].apply(lambda c: country_alpha2_to_country_name(c))
df = df[df['user_id'].isin(demo_df['user_id'])]

# only keep the most frequent trackables
frequent_items = []
# I discarded weather because it resulted in a lot of meaningless rules like coffee, sunny -> rain (!)
for trackable in ['Symptom', 'Condition', 'Treatment', 'Tag', 'Food', 'HBI']:
    frequent_items.extend(
        df[df.trackable_type == trackable].trackable_name.value_counts(ascending=False).iloc[0:50].index)

df = df[df['trackable_name'].isin(frequent_items)]

df.loc[df['trackable_type'] == 'HBI', 'trackable_name'] = df[df['trackable_type'] == 'HBI']['trackable_value'].apply(
    hbi_score)

# tag and treatment both start with t, renamed one to avoid complications and changing post-processing and front-end
df.loc[df['trackable_type'] == 'Treatment', 'trackable_type'] = 'Medicine'

# generate a dictionary of events to use for sequence generation
df.to_csv("C:/Users/user/Downloads/archive/export_filtered.csv", index=False)
mapping = FlaredownMapping()

# for sequentila rules, generate one (complex) sequence per user
# events on the same date will be store in a tuple, the events in a tuple must be sorted (SPMF req)
#
# for frequent itemsets, the transaction is a set of unique events per user
rows = []
df.sort_values(by='checkin_date', inplace=True)
for user in df.groupby(['user_id']):
    user_id = user[0]
    user_sequence = []
    user_sequence_flat = []
    dategroups = user[1].groupby("checkin_date")
    if dategroups.ngroups < 5:
        continue
    for date in dategroups:
        gdf = date[1]
        sequence = [int(mapping.event_to_code[item]["code"]) for item in gdf['trackable_name']]
        sequence.sort()  # SPMF requirement
        user_sequence.append(tuple(sequence))
        user_sequence_flat.extend(sequence)
    # saving SPMF input format as well to reduce preprocessing time for live demo
    rows.append([user_id, user_sequence, user_sequence_flat, generate_input_line_from_list(user_sequence, True),
                 generate_input_line_from_list(user_sequence, False)])
sequence_df = pd.DataFrame(rows, columns=['user_id', 'Sequence', 'Sequence_flat', 'spmf_transaction_line',
                                          'spmf_sequence_line'])

df = df[df['user_id'].isin(sequence_df['user_id'])]
demo_df = demo_df[demo_df['user_id'].isin(sequence_df['user_id'])]

df.to_csv("C:/Users/user/Downloads/archive/export_filtered.csv", index=False)
demo_df.to_csv("pattern_mining/data/flaredown/user_demographics.csv", index=False)
sequence_df.to_pickle("pattern_mining/data/flaredown/sequences.pkl")
