from typing import List
from pattern_mining.post_processing.pattern_classes import Rule, FrequentItemSet
from pattern_mining.post_processing.itemset_graph import ItemsetGraph
import pandas as pd
import numpy as np


def parse_rules(rules_file: str) -> List[Rule]:
    '''
    :param rules_file: file path of the SPMF output
    :return: list of Rule objects
    '''
    f = open(rules_file, "r")
    rules = []
    while True:
        line = f.readline()
        if not line:
            break
        rule = line.split('==>')
        lhs = rule[0].split(',')
        lhs = np.array([int(item) for item in lhs])
        rule = rule[1].split()
        rhs = int(rule[0])
        sup = int(rule[2])
        conf = round(float(rule[4]), 2)
        rules.append(Rule(lhs, rhs, sup, conf))
    return rules


def parse_itemsets(itemset_file) -> List[FrequentItemSet]:
    '''
    :param rules_file: file path of the SPMF output
    :return: list of FrequentItemSet objects
    '''
    f = open(itemset_file, "r")
    itemsets = []
    while True:
        line = f.readline()
        if not line:
            break
        line = line.split('#SUP:')
        items = line[0].split()
        items = np.array([int(item) for item in items])
        support = int(line[1])
        itemsets.append(FrequentItemSet(items, support))
    return itemsets


def remove_redundant_rules(rules: List[Rule]) -> List[Rule]:
    '''
    Removes redundant rules based on the description of redundancy found here:
    http://www.philippe-fournier-viger.com/spmf/TopKNonRedundantAssociationRules.php
    An association rule ra: X → Y is redundant with respect to another rule rb : X1 → Y1 if and only if:
        conf(ra) = conf(rb)
        sup(ra) = sup(rb)
        X1 ⊆ X ∧ Y ⊆ Y1.
    :param rules: list of Rule objects
    :return: list of non-redundant rules in form of Rule objects
    '''
    redundant_ids = []
    for rule in rules:
        for rule1 in rules:

            if rule.id == rule1.id:
                continue

            if rule1.RHS == rule.RHS and np.sum(np.isin(rule.LHS, rule1.LHS)) == rule1.LHS.shape[-1] and \
                    rule1.support == rule.support and rule1.confidence == rule.confidence:
                redundant_ids.append(rule.id)

    return [rule for rule in rules if rule.id not in redundant_ids]


def get_sequences_per_rule(rules: List[Rule], sequences: pd.DataFrame, data='airport') -> List[Rule]:
    '''
    :param rules: list of Rule objects
    :param sequences: dataframe of sequences with event list stored in 'Sequence' column
    :param data: dataset identifier: airport or flaredown
    :return: list of Rule objects with their seq_is property is the list of Turnaround IDs corresponding to that rule

    This function will not work for complex sequences like flaredown where each item in list is a tuple of simultaneous
    events. The time complexity for finding the correct match for each pattern in a complex sequence will be too high and
    the SPMF library does not provide list of sequence ids for each pattern (mined with TRuleGrowth) as of May 2021.
    '''
    count_all_sequences = sequences.shape[0]
    for rule in rules:
        seq_ids = []
        if data == 'airport':
            for i, row in sequences.iterrows():
                events = row['Sequence']
                rhs_indx = np.where(np.array(events) == rule.RHS)[0]
                if (rule.RHS in events) and np.sum(np.isin(np.unique(events), rule.LHS)) == rule.LHS.shape[-1] \
                        and \
                        all((np.where(events == item)[0][0] < rhs_indx[0]) for item in
                            rule.LHS):
                    seq_ids.append(row['Turnaround ID'])
            rule.seq_ids = seq_ids
        rule.support_percentage = round(float(rule.support / count_all_sequences), 2)
    return rules


def get_sequences_per_fis(fis: List[FrequentItemSet], labeled_sequences: pd.DataFrame, data='airport') -> List[
    FrequentItemSet]:
    '''
    :param fis: list of FrequentItemSet objects
    :param labeled_sequences: dataframe of sequences with event list stored in 'Sequence' column
    :param data: dataset identifier: airport or flaredown
    :return: list of FrequentItemSet objects with their seq_is property is the list of Turnaround IDs corresponding to that pattern
    '''
    count_all_sequences = labeled_sequences.shape[0]
    for itemset in fis:
        seq_ids = []
        if data == 'airport':
            for i, row in labeled_sequences.iterrows():
                events = row['Sequence']
                if np.sum(np.isin(np.unique(events), itemset.items)) == itemset.items.shape[-1]:
                    seq_ids.append(row['Turnaround ID'])
            itemset.seq_ids = seq_ids
        itemset.support_percentage = round(float(itemset.support / count_all_sequences), 2)
    return fis

def get_pattern_by_id(patterns: list, id: str):
    '''
    returns class instance of Rule or FrequentItemSet with specific id from a list of objects
    '''
    for pattern in patterns:
        if str(pattern.id) == str(id):
            return pattern
    return None


if __name__ == "__main__":
    delta_labels_df = pd.read_pickle("pattern_mining/data/HIAA/labeled_deltas.pkl")
    freqitemsets = parse_itemsets("pattern_mining/data/spmf/FPGrowth_itemsets_out.txt")
    freqitemsets = get_sequences_per_fis(freqitemsets, delta_labels_df)
    lattice_fig = ItemsetGraph().generate_plotly_figure(freqitemsets)
    lattice_fig.show()
