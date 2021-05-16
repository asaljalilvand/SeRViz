import networkx as nx
from typing import List
from pattern_mining.post_processing.pattern_classes import FrequentItemSet
from pattern_mining.pre_processing.dictionary import AirportMapping, FlaredownMapping
import plotly.graph_objects as go
import pandas as pd
from networkx.drawing.nx_agraph import graphviz_layout
from plotly.subplots import make_subplots


class ItemsetGraph:
    '''
    This class is used to generate:
        1) A matrix of frequent itemset patterns, with patterns as rows and items as columns
            - used in final version of visual design

        2) A network of frequent itemsets with patterns as nodes and non-empty intersection of items as edges
            - used in dashboard with Dash
            - network was discarded for the final visual design due to low visual scalability
    '''

    def __init__(self, data='airport'):
        self.data = data
        self.mapping = AirportMapping() if self.data == 'airport' else FlaredownMapping()

    def get_full_graph_info(self, fis_list: List[FrequentItemSet]) -> dict:
        '''
        :param fis_list: list of FrequentItemSet objects
        :return: dictionary of graph nodes frequency (of item in patterns) and centrality information
        '''
        graph = self._create_graph(fis_list)
        frequencies = [f.support_percentage for f in fis_list]
        centrality = nx.betweenness_centrality(graph)
        min_c = min(centrality.values())
        max_c = max(centrality.values())
        nodes = [{'code': fis.id, 'items': [self.mapping.code_to_event[str(item)]['event'] for item in fis.items],
                  'f': fis.support_percentage, 'c': centrality[fis.id]} for fis in fis_list]
        edges = [{'source': edge[0], 'target': edge[1]} for edge in graph.edges]
        full_graph = {'nodes': nodes, 'edges': edges, 'min_f': min(frequencies), 'max_f': max(frequencies),
                      'min_c': min_c, 'max_c': max_c}
        return full_graph

    def create_matrix(self, fis_list: List[FrequentItemSet]) -> pd.DataFrame:
        '''
        groups similar itemsets by non-empty intersection of items.
        :param fis_list: list of FrequentItemSet objects
        :return: matrix of frequent itemsets. each row is an itemset or a group (aggregation of all the items in the group)
            itemset rows have level==1 and groups have level==0. columns include all the unique items found in patterns
            non-empty cells in rows indicate existence of that item in the pattern
        '''
        size = len(fis_list)
        rows = []
        similar_groups = []

        for i in range(size):
            fis_i = fis_list[i]
            belongs_to_sets = []
            set_i = set(fis_i.items)
            for j in range(len(similar_groups)):
                for pattern in similar_groups[j]:
                    if len(set(pattern.items).intersection(set_i)) != 0:
                        belongs_to_sets.append(j)
                        break

            if len(belongs_to_sets) == 0:
                similar_groups.append({fis_i})

            elif len(belongs_to_sets) == 1:
                similar_groups[belongs_to_sets[0]].add(fis_i)

            else:
                groups_to_merge = [similar_groups[j] for j in belongs_to_sets]
                group = {fis_i}
                for sm in groups_to_merge:
                    similar_groups.remove(sm)
                    group.update(sm)
                similar_groups.append(group)

        for i in range(len(similar_groups)):
            group = similar_groups[i]
            for pattern in group:
                row = {'support': pattern.support_percentage, 'rid': pattern.id, 'group': i, 'level': 1}
                for item in pattern.items:
                    item = str(item)
                    # for flaredown, we don't use tags in front-end glyphs, so it's all just "I" for Item
                    # row[self.mapping.code_to_event[item]['parent']] = "I" if self.data == 'flaredown' else \
                    #     self.mapping.code_to_event[item]['tag'][0].upper()
                    row[self.mapping.code_to_event[item]['parent']] = self.mapping.code_to_event[item]['tag'][0].upper()
                rows.append(row)
            rows.append({'group': i, 'level': 0})

        matrix = pd.DataFrame(rows)
        matrix.fillna('', inplace=True)
        return matrix.rename(
            columns={code: self.mapping.code_to_event[str(code)]['event'] for code in matrix.columns if code
                     not in ['support', 'rid', 'group', 'level']})

    def _create_graph(self, fis_list: List[FrequentItemSet]) -> nx.Graph:
        '''
        :param fis_list: list of FrequentItemSet objects
        :return: network graph, nodes= FrequentItemSet object ids, edges = non-empty intersection of itemsets
        '''
        graph = nx.Graph()

        graph.add_nodes_from([fis.id for fis in fis_list])
        size = len(fis_list)
        for i in range(size - 1):
            set_i = set(fis_list[i].items)
            for j in range(i + 1, size):
                intersect = set_i.intersection(set(fis_list[j].items))
                intersect_len = len(intersect)
                if intersect_len == 0:
                    continue
                # weight was added to use in network scatter plot for showing similar patterns closer
                graph.add_edge(fis_list[i].id, fis_list[j].id, weight=intersect_len)

        return graph

    def generate_plotly_figure(self, fis_list: List[FrequentItemSet]) -> go:
        '''
        :param fis_list: list of FrequentItemSet objects
        :return: plotly network scatter plot, nodes= frequent itemsets, edges = non-empty intersection of itemsets
            the network has a table legend showing "item number - delta" name mapping

        based on https://plotly.com/python/network-graphs/
        '''
        lattice = self._create_graph(fis_list)
        # dot layout takes forever with anonymous data for some reason, used spring instead
        node_positions = nx.spring_layout(lattice,k=3,scale=1000,seed=94,iterations=150)

        node_x = []
        node_y = []
        node_color = []
        node_text = []
        node_size = []
        node_fis_id = []
        unique_items = set()
        for fis in fis_list:
            x, y = node_positions[fis.id]
            node_x.append(x)
            node_y.append(y)
            node_color.append(fis.support_percentage)
            node_text.append(str(fis.items))
            node_size.append(fis.support_percentage * 70)
            node_fis_id.append(fis.id)
            unique_items.update(fis.items)

        node_trace = go.Scatter(
            x=node_x, y=node_y, text=node_text, customdata=node_fis_id,
            mode='markers+text',
            hovertemplate=
            'support: %{marker.color}' +
            '<br><br>' +
            '%{text}',
            textfont={'size': 8},
            marker=dict(
                showscale=True,
                colorscale='Magenta',
                color=node_color,
                size=node_size,
                colorbar=dict(
                    thickness=8,
                    title='Support',
                    xanchor='left'
                )))

        edge_x = []
        edge_y = []
        for edge in lattice.edges():
            x0, y0 = node_positions[edge[0]]
            x1, y1 = node_positions[edge[1]]
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        # Legend
        legend = go.Table(columnwidth=[0.3, 0.7],
                          header=dict(values=['Code', 'Name'], fill_color='lightgrey', font_size=9),
                          cells=dict(values=[list(unique_items), [self.mapping.code_to_event[str(item)]['event']
                                                                  for item in unique_items]], fill_color='white',
                                     font_size=9, align='left'))

        fig = make_subplots(
            rows=1, cols=2, shared_xaxes=True, specs=[[{"type": "table"}, {"type": "scatter", 'type': 'scatter'}]],
            column_widths=[0.2, 0.8]
        )
        fig.add_trace(legend, row=1, col=1)
        fig.add_trace(edge_trace, row=1, col=2)
        fig.add_trace(node_trace, row=1, col=2)
        fig.update_layout(
            showlegend=False, hovermode='closest', xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), template='none',
            margin=dict(l=0, r=0, b=0, t=0, pad=0))
        return fig
