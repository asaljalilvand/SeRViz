# SeRVis
##  An Interactive Visualization Framework for the Analysis of Sequential Rules and Frequent Itemsets
[![Generic badge](https://img.shields.io/badge/Python-3.7-green)](https://shields.io/) [![Generic badge](https://img.shields.io/badge/Flask-1.1.2-green)](https://shields.io/) [![Generic badge](https://img.shields.io/badge/networkx-2.5-green)](https://shields.io/) [![Generic badge](https://img.shields.io/badge/spmf-1.3-green)](https://shields.io/)
[![Code Quality Score](https://www.code-inspector.com/project/22661/score/svg)](https://frontend.code-inspector.com/public/project/22661/SeRVis/dashboard)
[![Code Grade](https://www.code-inspector.com/project/22661/status/svg)](https://frontend.code-inspector.com/public/project/22661/SeRVis/dashboard)

:school: This project is part of a Masters thesis in the Visual Analytics and Visualization (VAV) lab is part of the Faculty of Computer Science, Dalhousie University, Canada.<br>
:orange_book: [View on DalSpace library](https://dalspace.library.dal.ca/handle/10222/80445) <br>
:video_camera: [Video demo of a use case](https://youtu.be/snxpXPj1Vmg) <br>
:computer: [Live Demo on Heroku](https://servis-framework.herokuapp.com)<br>

## Description
### Objective
- Finding delay-related patterns affecting turnaround performance
- Reducing the cognitive load of exploration of the mined patterns by means of visual analytics

### Dataset
This project was originally developed using a log of ground handling operations at at Halifax Stanfield International Airport collected by [Assaia Apron AI](https://assaia.com).

For showing that the proposed framework can be used in other domains as well, we also used a dataset of chronic diseases. This dataset is collected by the [Flaredown](https://flaredown.com) application and is publicly available at [Kaggle](https://www.kaggle.com/flaredown/flaredown-autoimmune-symptom-tracker).

### Methodology
- Using data mining (sequential rules and frequent itemsets)
- Visualization of patterns with a novel matrix-based approach

<img src="https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/overview.PNG" height="600">

:seedling: The main contribution of this work is a novel approach for visualizing sequential rules w.r.t. to the partial order of antecedents and consequents.

<img src="https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/topol.PNG" height="230">

### Evaluation
1. Domain expert feedback on visual prototype
2. User test
      - Two sets of analytical tasks 
         - Similar questions 
         - Different tools
            - text vs. visual prototype

        <img src="https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/eval.PNG" height="120">
      - NASA-TLX for measuring workload of each set of tasks
        
        <img src="https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/nasabox.jpg" height="240">
      - Are difference in averages statistically significant?
        - Paired t-test
            - (alternative) hypothesis: the true mean difference between the paired samples is not equal to zero

        <img src="https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/eval2.PNG" height="200">

    - Analytical tasks to assess if the users can successfully use all features
      
      <img src="https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/eval3.PNG" height="120">

### Result
SeRVis is a novel visual analytics tool for mining and exploring frequent patterns. Based on our experiments it reduces the cognitive load of users for the said tasks compared to the popular off-the-shelf data mining tool, SPMF.

## Features
### Data filtering, pattern mining and pattern overview
![](https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/feature1.PNG)

:woman_teacher: Tutorial [SeRVis Mining, filtering and overview](https://youtu.be/8gvq5D--y2s)

### Sequential rules matrix
![](https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/feature2.PNG)

:woman_teacher: Tutorial [SeRVis Sequential rule matrix](https://youtu.be/AuurfjUJKxQ)

### Distribution analysis and detail-on-demand
![](https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/feature3.PNG)

:woman_teacher: Tutorial [SeRVis distribution analysis and breakdown](https://youtu.be/k7-hs1IhsjI)

### Frequent itemsets matrix
![](https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/feature4.PNG)

:woman_teacher: Tutorial [SeRVis frequent itemsets](https://youtu.be/qqVraljl4do)

## Run
`````
cd server
pip install -r requirements.txt
python main.py
`````
:point_right: Since this project uses [SPMF library](https://www.philippe-fournier-viger.com/spmf/), you need have Java installed.
An instance of SPMF v2.42c is located at server/pattern_mining/mining/thirdparty/spmf.jar (uploaded since it is required for live demo on Heroku).

### Dash
[![Generic badge](https://img.shields.io/badge/dash-1.18.1-green)](https://shields.io/) [![Generic badge](https://img.shields.io/badge/dash_core_components-1.14.1-green)](https://shields.io/) [![Generic badge](https://img.shields.io/badge/plotly-4.13.0-green)](https://shields.io/)

We developed a low-fidelity prototype in early stages of visual design using dash. The dashboard is located at server/mining/quick_dashboard.py.

<img src="https://raw.githubusercontent.com/AsalJalilvand/SeRVis/master/images/dash.png" height="250">

## Acknowledgment
This research was enabled in part by support provided by and [DeepSense :ocean:](https://deepsense.ca) and Halifax Stanfield International Airport:airplane:.

## Citation
Asal Jalilvand. SeRViz: an Interactive Visualization Framework for the Analysis of Sequential Rules and Frequent Itemsets. Master's thesis, Dalhousie University, Halifax, NS, Canada, 2021.


## License
:balance_scale: [GPL-3.0 License](https://github.com/AsalJalilvand/SeRVis/blob/master/LICENSE)
