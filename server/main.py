# server
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from pathlib import Path

from pattern_mining.post_processing import utils

# configuration
DEBUG = True
# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/raw', methods=['GET'])
def get_raw():
    '''
    returns two pre-mined list of patterns. This function was developed for the purpose of user test
    '''
    req = request.args.get('p')
    if req is None or req not in ['fis', 'sr']:
        return render_template('index.html')
    script_path = str(Path(__file__).parent.absolute())
    raw_file = "{}/pattern_mining/data/spmf/raw_{}.txt".format(script_path, req)
    with open(raw_file, "r") as file:
        content = file.read().replace('\n', '<br/>')
        return content


# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')


@app.route('/fis', methods=['POST'])
def all_freq_itemsets():
    '''
    request must include mining configuration, and optionally transaction filtering criteria
    returns frequent itemsets and distribution for front-end in required format
    '''
    req = request.get_json()
    mining_config = utils.HDict(req['config']) if req['config'] is not None else None
    data = req['data']  # dataset identifier: airport or flaredown
    sequence_filters = None
    if 'filter' in req:
        sequence_filters = {}
        for key in req['filter'].keys():
            sequence_filters[key] = tuple(req['filter'][key])
        sequence_filters = utils.HDict(sequence_filters)
    try:
        fis, s_ids = utils.get_frequent_itemsets(mining_config, sequence_filters, data=data)
    except:
        return jsonify({'toomany': '1'})
    views_dict = utils.get_fis_matrix_views(tuple(fis), tuple(s_ids), data=data)
    return jsonify(views_dict)


@app.route('/rules', methods=['POST'])
def all_rules():
    '''
    request must include mining configuration, and optionally transaction filtering criteria
    returns sequential rules and distribution for front-end in required format
    '''
    sequence_filters = None
    req = request.get_json()
    data = req['data']  # dataset identifier: airport or flaredown
    mining_config = utils.HDict(req['config']) if req['config'] is not None else None
    if 'filter' in req:
        sequence_filters = {}
        for key in req['filter'].keys():
            sequence_filters[key] = tuple(req['filter'][key])
        sequence_filters = utils.HDict(sequence_filters)
    try:
        rules, s_ids = utils.get_sequential_rules(mining_config, sequence_filters, data=data)
    except:
        return jsonify({'toomany': '1'})

    if rules is None:
        # if the number of mined rules are too many, the post-processing will take too long
        # for the sake of user experience, high number of rules are not processed and rendered
        views_dict = {'toomany': '1'}
    else:
        views_dict = utils.get_rules_graph_matrix_views(tuple(rules), tuple(s_ids), data=data)
        views_dict.update({'toomany':'0'})
    return jsonify(views_dict)


@app.route('/distribution_data', methods=['POST'])
def get_distribution_data():
    req = request.get_json()
    mining_config = utils.HDict(req['config']) if req['config'] is not None else None
    sequence_filters = None
    selected_rule_ids = req['rids']
    if 'filter' in req:
        sequence_filters = {}
        for key in req['filter'].keys():
            sequence_filters[key] = tuple(req['filter'][key])
        sequence_filters = utils.HDict(sequence_filters)

    if int(req['mode']) == 0:
        patterns, s_ids = utils.get_sequential_rules(mining_config, sequence_filters)
        rule = True
    else:
        patterns, s_ids = utils.get_frequent_itemsets(mining_config, sequence_filters)
        rule = False

    sequence_ids, seq_ids_per_pattern, pattern_items = utils.get_sequences_by_pattern_id(tuple(patterns),
                                                                                         tuple(selected_rule_ids),
                                                                                         detailed=True,
                                                                                         rule=rule)
    sunburst, heatmap, pc = utils.get_views_by_sequence_ids(sequence_ids, seq_ids_per_pattern)
    result = {
        'heatmap': heatmap,
        'sunburst': sunburst,
        'pc': pc
    }
    result.update(utils.get_performance(sequence_ids, pattern_items, rule))
    return jsonify(result)


@app.route('/filter_options', methods=['GET'])
def get_filter_options():
    '''
    request may include dataset identifier (airport or flaredown) - by default airport dataset is used
    returns data filtering options
    '''
    if 'data' in request.args:
        dataset = request.args.get('data')
        return jsonify(utils.get_filter_options(dataset))
    return jsonify(utils.get_filter_options())


if __name__ == '__main__':
    app.run()
