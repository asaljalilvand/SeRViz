import networkx as nx
from typing import List, Tuple
import pandas as pd
import numpy as np
from pattern_mining.post_processing.pattern_classes import Rule
from pattern_mining.pre_processing.dictionary import AirportMapping, FlaredownMapping
from sklearn_extra.cluster import KMedoids


class RuleDAG:
    '''
    This class generates (forest of) DAGs from Rule objects along with matrix of rules with patterns as rows and
    topological sort of DAG as columns. The goal is to show the partial order within sequential rule LHS and RHS in the
    matrix.
    '''

    def __init__(self, tagged=True, data='airport'):
        '''
        :param tagged: to use labelled events as DAG nodes and matrix columns, or use base events
        :param data: dataset identifier - 'airport' or 'flaredown'
        '''
        self.tagged = tagged
        self.mapping = AirportMapping() if data == 'airport' else FlaredownMapping()

    def _insert_rule_to_dag(self, dag: nx.DiGraph, rule: Rule) -> nx.DiGraph:
        '''
        inserts a sequential rule into a DAG with items as nodes and edges from LHS to RHS

        :param dag: a directed acyclic graph
        :param rule: sequential rule in form of a Rule object
        :return: a new DAG including the rule, None is returned if the rule caused a cycle in the DAG
        '''
        temp_graph = dag.copy()
        temp_graph.add_edges_from([(lhs, rule.RHS) if self.tagged
                                   else (self.mapping.code_to_event[str(lhs)]['parent'],
                                         self.mapping.code_to_event[str(rule.RHS)]['parent'])
                                   for lhs in rule.LHS])
        if nx.is_directed_acyclic_graph(temp_graph):
            return temp_graph
        return None

    def _create_dags(self, rules: List[Rule]) -> Tuple[List, dict]:
        '''
        :param rules: list of Rule objects
        :return: tuple of the following:
             - list directed acyclic graph(s) of sequential rules with items as nodes and edges from LHS to RHS
                each item in list is a dictionary of {'g':nx.DiGraph, 'rules':List[str]} where 'rules' is the list of
                ids of the rules that the DAG is generated from
             - dictionary with key=rule item, value= item frequency in the rules
        '''
        dags = []
        event_frequency = {}

        for rule in rules:
            inserted = False
            for dag in dags:
                g = self._insert_rule_to_dag(dag['g'], rule)
                if g is not None:
                    dag['g'] = g  # update dag with newly inserted rule
                    dag['rules'].append(rule.id)
                    inserted = True
                    break
            if not inserted:
                dag = self._insert_rule_to_dag(nx.DiGraph(), rule)
                dags.append({'g': dag, 'rules': [rule.id]})

            all_items = rule.LHS
            all_items = np.append(all_items, rule.RHS)
            for item in all_items:
                item = self.mapping.code_to_event[str(item)]['parent']
                if item in event_frequency:
                    event_frequency[item] = event_frequency[item] + 1
                else:
                    event_frequency[item] = 1

        return dags, event_frequency

    def _topol_sort_dags(self, dags: List[dict]):
        '''
        :param dags: list of dictionaries in form of {'g':nx.DiGraph, 'rules':List[str]}

        converts each DAG (value of key 'g') into topological sort of its nodes
        '''
        for dag in dags:
            dag['g'] = list(nx.algorithms.dag.topological_sort(dag['g']))  # replace graph with its topol sort list

    def _create_df(self, columns: list, rules: List[Rule]) -> pd.DataFrame:
        '''
        :param columns: column list of matrix derived from the topological sort of the DAG
        :param rules: list of Rule objects
        :return: matrix of sequential rules with rules as rows and items as columns
            - dataframe index is rule id.
            - support and confidence are added as columns.
            - group is used for the front-end sorting of the rule groups, is added as a column to DF.
                Each group is a group of rules sharing same consequent. The index of the consequent in columns param is
                the value of the group.
            - level indicates row is sequential rule (1 is rule and 0 is group)
        '''
        matrix_columns = columns.copy()
        matrix_columns.extend(["group", "level", "support", "confidence"])
        matrix = pd.DataFrame('', index=[rule.id for rule in rules], columns=matrix_columns)
        for rule in rules:
            for item in rule.LHS:
                col = item if self.tagged else self.mapping.code_to_event[str(item)]['parent']
                cell_val = 'A.' if self.tagged else 'A.' + self.mapping.code_to_event[str(item)]['tag'][0].upper() + "."
                matrix.loc[rule.id, col] = cell_val
            col = rule.RHS if self.tagged else self.mapping.code_to_event[str(rule.RHS)]['parent']
            cell_val = 'C.' if self.tagged else 'C.' + self.mapping.code_to_event[str(rule.RHS)]['tag'][0].upper() + "."
            matrix.loc[rule.id, col] = cell_val
            matrix.loc[rule.id, "group"] = columns.index(col)
            matrix.loc[rule.id, "level"] = 1
            matrix.loc[rule.id, "support"] = rule.support_percentage
            matrix.loc[rule.id, "confidence"] = rule.confidence

        return matrix.rename(columns={code: self.mapping.code_to_event[str(code)]['event'] for code in columns})

    def _cluster_matrix(self, matrix: pd.DataFrame, n_clusters=5) -> pd.DataFrame:
        '''
        clusters rule matrix (without support,confidence, group and level columns) with Jaccard distance
        :param matrix: rule matrix
        :param n_clusters: number of clusters
        :return: returns clustered matrix (without support,confidence, group and level columns) with rows in one cluster
            next to each other

        * clustering was not used in the final visual design
        '''
        tmp = matrix.copy()

        # remove redundant info for clustering
        for col in ['support', 'confidence', 'group', 'level']:
            if col in tmp.columns:
                tmp.drop(columns=col, inplace=True)

        # create a binary matrix
        df = np.where(matrix == ' ', False, True)

        # find clusters
        kmedoids_labels = KMedoids(n_clusters=n_clusters, random_state=0, metric='jaccard', init='k-medoids++') \
            .fit_predict(df)
        labels = pd.Series(kmedoids_labels, index=tmp.index)

        # sort rows by clusters
        tmp['labels'] = labels
        tmp.sort_values(by='labels', inplace=True)

        return tmp.drop(columns=['labels'])

    def create_matrices(self, rules: List[Rule], cluster=False, id_as_column=False) -> Tuple[List[pd.DataFrame], dict]:
        '''
        :param rules: list of Rule objects
        :param cluster: cluster rule rows or not
        :param id_as_column: use rule ids as a column (if False, the rule id is still accessible with index)
        :return: tupe of the following:
            - list of rule matrices (one matrix per DAG)
            - dictionary of the DAG (forest) information including frequency of nodes (items) in patterns and
                node centrality
        '''

        # first create dags
        dags, event_frequency = self._create_dags(rules)
        # min and max frequency and centrality are stored for node color and size range in front-end
        full_graph = {'nodes': [], 'edges': [], 'min_f': min(event_frequency.values(), default=0),
                      'max_f': max(event_frequency.values(), default=0), 'min_c': 0, 'max_c': 0}
        for i in range(len(dags)):
            g = dags[i]['g']
            dag_index = str(i)
            centrality = nx.betweenness_centrality(g)
            min_c = min(centrality.values())
            max_c = max(centrality.values())
            if min_c < full_graph['min_c']:
                full_graph['min_c'] = min_c
            if max_c > full_graph['max_c']:
                full_graph['max_c'] = max_c

            # the information stored for nodes and edges are for front-end use
            # dag_index is used to know which node and edge in DAG forest correspond to which matrix
            nodes = [{'code': str(node) + dag_index, 'name': self.mapping.code_to_event[str(node)]['event'],
                      'dag_index': dag_index, 'f': event_frequency[node], 'c': centrality[node]}
                     for node in g.nodes]
            edges = [{'source': str(edge[0]) + dag_index, 'target': str(edge[1]) + dag_index} for edge in g.edges]
            full_graph['edges'].extend(edges)
            full_graph['nodes'].extend(nodes)

        # get topol sort of each dag
        self._topol_sort_dags(dags)

        # create a dataframe per dag
        matrices = [self._create_df(dag['g'], [rule for rule in rules if rule.id in dag['rules']]) for dag in dags]

        if cluster:
            matrices = [self._cluster_matrix(m) for m in matrices]

        if id_as_column:
            for m in matrices:
                m['rid'] = m.index.astype(str)
        return matrices, full_graph
