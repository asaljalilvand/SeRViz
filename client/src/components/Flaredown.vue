<style>
@import "../assets/css/style.css";
</style>

<template>
  <div>
    <v-navigation-drawer v-model="drawer" class="yellow lighten-4" app>
      <div style="margin: 15px;">
        <v-select
            v-model="age_filter_values"
            :items="age_filter_items"
            label="Age Group"
            multiple
            @change="filtered = true"
        ></v-select>

        <v-select
            v-model="sex_filter_values"
            :items="sex_filter_items"
            label="Sex"
            multiple
            @change="filtered = true"
        ></v-select>

        <v-autocomplete v-model="country_filters_selection"
                        :items="country_filters"
                        label="Country"
                        clearable
                        dense
                        persistent-hint
                        multiple
                        @change="filtered = true">
          <template v-slot:prepend-item>
            <v-list-item
                ripple
                @click="toggle"
            >
              <v-list-item-action>
                <v-icon :color="country_filters_selection.length > 0 ? 'indigo darken-4' : ''">
                  {{ icon }}
                </v-icon>
              </v-list-item-action>
              <v-list-item-content>
                <v-list-item-title>
                  Select All
                </v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            <v-divider class="mt-2"></v-divider>
          </template>
        </v-autocomplete>

        <v-text-field
            v-model="event_filter"
            @change="filtered=true"
            label="Events (Separate by ;)">
        </v-text-field>

      </div>
    </v-navigation-drawer>
    <v-container fluid>
      <v-tabs
          background-color="indigo lighten-5"
          color="blue-grey darken-3"
          height="30px"
          centered
          fixed-tabs
          v-model="mode"
          @change="tabSwitch"
      >
        <v-btn to="/" color="indigo lighten-5" depressed>
          <v-icon small light>fas fa-home</v-icon>
        </v-btn>
        <v-tab style="font-size: x-small;text-transform: none">Sequential Rules</v-tab>
        <v-tab style="font-size: x-small;text-transform: none">Frequent Itemsets</v-tab>
      </v-tabs>

      <v-row class="m-1 p-1" no-gutters>
        <v-col class="border rounded ml-auto" md="3">
          <v-toolbar height="15px" color="indigo darken-4" dark flat>
            <v-toolbar-title>Pattern Mining Configuration</v-toolbar-title>
          </v-toolbar>
          <div style="margin-left: 20px;">
            <v-slider
                dense
                light
                ticks
                height="25"
                v-model="rule_options.support"
                color="#616161"
                track-color="#EEEEEE"
                thumb-label
                :thumb-size="20"
                max="100"
                min="1"
                step="0.5"
                label="Min. support(%)"
            ></v-slider>
            <v-slider
                v-show="mode === 0"
                dense
                light
                height="25"
                ticks
                v-model="rule_options.confidence"
                color="#616161"
                track-color="#EEEEEE"
                thumb-label
                :thumb-size="20"
                max="100"
                min="5"
                step="5"
                label="Min. confidence(%)"
            ></v-slider>
            <v-slider
                v-show="mode === 0"
                dense
                light
                ticks
                height="25"
                v-model="rule_options.window"
                color="#616161"
                track-color="#EEEEEE"
                thumb-label
                :thumb-size="20"
                max="20"
                min="1"
                step="1"
                label="Window"
            ></v-slider>
          </div>

          <div>
            <v-layout align-center justify-center>
              <div class="text-xs-center">
                <v-btn x-small color="yellow lighten-3" @click.stop="drawer = !drawer">
                  Advanced filtering (before mining)
                </v-btn>
                <v-btn x-small color="indigo lighten-4" @click="mineClicked">
                  Mine
                </v-btn>
                <v-dialog v-model="mine_dialog" width="500">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn icon color="amber" x-small v-bind="attrs" v-on="on">
                      <v-icon>mdi-lightbulb-on</v-icon>
                    </v-btn>
                  </template>

                  <v-card>
                    <v-card-title class="headline grey lighten-2">
                      Pattern Mining
                    </v-card-title>
                    <v-card-text>
                      <b>Support:</b> The support of a rule X -> Y is how many sequences contains
                      the items from X followed by the items from Y.<br/>
                      <b>Confidence:</b> The confidence of a rule X -> Y is the support of the rule
                      divided by the number of sequences containing the items from X. <br/>It can
                      be understood as the conditional probability P(Y|X).<br/>
                      <b>Window:</b> The rule X -> Y, contains all items of X before all items from
                      Y in the window defined by window size. So window is the number of consecutive
                      events to look for pattern within them.
                    </v-card-text>
                    <v-card-subtitle>
                      Descriptions are taken from https://data-mining.philippe-fournier-viger.com,
                      and SPMF library documentation.
                    </v-card-subtitle>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="green" text @click="mine_dialog = false">
                        Close
                      </v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
              </div>
            </v-layout>
          </div>

          <div style="justify-content: center;text-align: center;">
            <div class="overview-title mt-1">
              #Sequences:{{ count.s }}
              <br/>
              #Patterns:{{ count.r }}
            </div>
            <p style="font-size: small">Mining might take a few minutes due to high number of records.</p>
          </div>


          <div class="mt-2" v-show="mode === 0">
            <v-toolbar height="15px" color="indigo darken-4" dark flat>
              <v-toolbar-title>Overview</v-toolbar-title>
            </v-toolbar>
            <v-radio-group
                class="m-0 p-0"
                v-model="color_choice"
                row
                hide-details
                dense
                max="1"
                @change="colourOverview"
            >
              <v-radio class="m-0" label="plain" value="none" color="pink darken-4"></v-radio>
              <v-radio
                  class="m-0"
                  label="frequency"
                  value="frequency"
                  color="pink darken-4"
              ></v-radio>
              <v-radio label="centrality" value="centrality" color="pink darken-4"></v-radio>
              <v-checkbox
                  class="m-0"
                  color="pink darken-4"
                  label="labels"
                  hide-details
                  dense
                  v-model="showLables"
                  @change="toggleOverviewLableVisibility"
              >
              </v-checkbox>
            </v-radio-group>
            <v-dialog v-model="graph_dialog" width="500">
              <template v-slot:activator="{ on, attrs }">
                <v-btn icon color="amber" x-small v-bind="attrs" v-on="on">
                  <v-icon>mdi-lightbulb-on</v-icon>
                </v-btn>
              </template>

              <v-card>
                <v-card-title class="headline grey lighten-2">
                  Overview Graph
                </v-card-title>
                <v-card-text>
                  <b>Nodes:</b> Unique items found in rules.<br/>
                  <b>Edges:</b> A directed edge x->y means there is at least one rule X -> Y, where
                  x is in the X set and y in the Y set.<br/>
                  <b>Frequency:</b> The frequency of a unique item in all the mined patterns.<br/>
                  <b>Centrality:</b> The betweenness centrality of the node. A node with high
                  centrality has high influence over information passing in the graph, and removing
                  them may disconnect the graph.
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn color="green" text @click="graph_dialog = false">
                    Close
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
            <div id="dag" class="m-0 p-0"></div>

          </div>
        </v-col>
        <v-col class="border rounded ml-auto overflow-auto" md="9">
          <v-toolbar height="15px" color="indigo darken-4" dark flat>
            <v-toolbar-title>{{
                mode === 0 ? "Sequential Rules Matrix" : "Frequent Itemset Matrix"
              }}
            </v-toolbar-title>
          </v-toolbar>
          <v-row>
            <v-col>
              <div id="table_legend">
                <table class="table-legend" v-show="mode === 0">
                  <thead>
                  <tr>
                    <th>Antecedent</th>
                    <th>Consequent</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr>
                    <td>
                      <svg width="20" height="20">
                        <circle cx="10" cy="10" r="10" fill="#29B6F6"/>
                      </svg>
                    </td>
                    <td>
                      <svg width="20" height="20">
                        <circle cx="10" cy="10" r="10" fill="#FF8A65"/>
                      </svg>
                    </td>
                  </tr>
                  </tbody>
                </table>
                <table class="table-legend" v-show="mode === 1">
                  <thead>
                  <tr>
                    <th>Trackable</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr>
                    <td>
                      <svg width="20" height="20">
                        <circle cx="10" cy="10" r="10" fill="#BA68C8"/>
                      </svg>
                    </td>
                  </tr>
                  </tbody>
                </table>
              </div>
            </v-col>
            <v-col sm="2">
              <v-switch
                  v-model="grouped"
                  inset
                  color="#a3ef7b"
                  :label="mode === 0 ? 'Group by Consequent' : 'Group by Similarity'"
                  @change="groupHandler"
              ></v-switch>
            </v-col>
            <v-col sm="1">
              <v-dialog v-model="matrix_dialog" width="500">
                <template v-slot:activator="{ on, attrs }">
                  <v-btn class="mt-3" icon color="amber" x-small v-bind="attrs" v-on="on">
                    <v-icon>mdi-lightbulb-on</v-icon>
                  </v-btn>
                </template>

                <v-card>
                  <v-card-title class="headline grey lighten-2">
                    Pattern Matrix
                  </v-card-title>
                  <v-card-text>
                    <h5>Sequential Rules</h5>
                    <b>Columns:</b> Trackables (more information found <a
                      href="https://dalspace.library.dal.ca/handle/10222/80445">here</a>)<br/>
                    <b>Rows:</b> patterns.<br/>
                    <b>Circles:</b> event in the pattern, color represents role of event in the pattern (antecedent or
                    consequent).<br/>
                    * In each row, we can see a group of antecedents (blue-themed circles) leading
                    to a consequent (orange-themed circle).
                    <br/>
                    * The <b>support</b> and <b>confidence</b> columns are displayed in <b>fractions</b>.
                    <br/>
                    <h5>Frequent itemsets</h5>
                    <b>Columns:</b> Trackables (more information found <a
                      href="https://dalspace.library.dal.ca/handle/10222/80445">here</a>)<br/>
                    <b>Rows:</b> patterns.<br/>
                    <b>Circles:</b> items in the pattern<br/>

                  </v-card-text>
                  <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="green" text @click="matrix_dialog = false">
                      Close
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>
            </v-col>
          </v-row>
          <v-row justify="center" class="pb-2 mb-2">
            <div class="rule_container  rounded ml-3">
              <div id="rule_table" class="rule-table "></div>
            </div>
          </v-row>
        </v-col>
      </v-row>
      <v-row class="border rounded m-1 p-1" dense>
        <v-toolbar height="15px" color="indigo darken-4" dark min-width="100%" flat>
          <v-toolbar-title>Distribution Analysis</v-toolbar-title>
        </v-toolbar>
        <v-col md="4">
          <Plotly
              :data="sunburst_data"
              :layout="sunburst_layout"
              :display-mode-bar="false"
          ></Plotly>
        </v-col>
        <v-col md="8">
          <Plotly
              :data="map_series"
              :layout="map_options"
              :display-mode-bar="false"
          ></Plotly>
        </v-col>
      </v-row>
    </v-container>

    <v-overlay :value="overlay">
      <v-row>
        <v-progress-circular indeterminate size="64"></v-progress-circular>
      </v-row>
      <v-row>
        <v-card color="transparent" flat dark>
          <v-card-text>
            <p v-html="overlay_message"></p>
          </v-card-text>
        </v-card>
      </v-row>
    </v-overlay>
  </div>
</template>

<script>
import * as d3 from "d3";
import axios from "axios";
import {Plotly} from "vue-plotly";
import {BACKEND_URL} from "./backend";

export default {
  name: "Flaredown",
  components: {
    Plotly
  },
  data() {
    return {
      url: BACKEND_URL,
      mode: 0,
      count: {},
      drawer: false,
      filtered: false,
      matrix_dialog: false,
      mine_dialog: false,
      graph_dialog: false,
      mine_clicked:0,
      age_filter_items: [],
      age_filter_values: [],
      sex_filter_items: [],
      sex_filter_values: [],
      country_filters: [],
      country_filters_selection: [],
      event_filter: "",
      rule_options: {support: 1.5, confidence: 65, window: 20},
      overview: [],
      showLables: true,
      color_choice: "none",
      overview_attr_scale: null,
      grouped: true,
      current_matrix: 0,
      rule_matrices: [],
      matrices_columns: [],
      rule_table_sort_clicks: {},
      rule_table_sort_order: [],
      selected_patterns_from_dag: [],
      related_rule_ids: [],
      pt_show: false,
      maps_list: [],
      sunbursts_list: [],
      map_series: [
        {
          type: 'choropleth',
          locationmode: 'country names',
          locations: [],
          z: [],
          // autocolorscale: true,
          colorscale: 'Cividis',
          reversescale: true,
          showscale: true,
        }
      ],
      map_options: {
        margin: {r: 0, t: 20, b: 0, l: 0},
        template: "white",
        height: 200,
        width: 500,
        font: {
          family: "Arial",
          size: "10"
        },
        title: {
          text: "Geographical Distribution",
          font: {
            family: "Arial",
            size: "11"
          },
        },

      },
      sunburst_data: [
        {
          type: "sunburst",
          labels: [],
          parents: [],
          values: [],
          ids: [],
          leaf: {opacity: 0.4},
          marker: {line: {width: 2}}
        }
      ],
      sunburst_layout: {
        margin: {l: 0, r: 0, b: 0, t: 30},
        height: 200,
        sunburstcolorway: ["#f3cec9", "#e7a4b6", "#cd7eaf", "#a262a9"],
        title: {
          text: "Category distribution",
          font: {
            family: "Arial",
            size: "11"
          }
        }
      },
      overlay: false,
      overlay_message: ""
    };
  },
  computed: {
    icon() {
      if (this.country_filters.length === this.country_filters_selection.length)
        return 'mdi-close-box';
      else if (this.country_filters_selection.length > 0)
        return 'mdi-minus-box';
      return 'mdi-checkbox-blank-outline';
    },
  },

  methods: {
    toggle() {
      //github.com/vuetifyjs/vuetify/blob/master/packages/docs/src/examples/v-select/slot-append-and-prepend-item.vue
      this.$nextTick(() => {
        if (this.country_filters.length === this.country_filters_selection.length) {
          this.country_filters_selection = []
        } else {
          this.country_filters_selection = this.country_filters.slice()
        }
      })
    },
    refresh() {
      this.$router.push({name: "Flaredown"});
    },
    clearSelections() {
      this.selected_patterns_from_dag = [];
      this.related_rule_ids = [];
    },
    getRuleConfigRequest() {
      let request = {config: this.mine_clicked>0?this.rule_options:null, mode: this.mode, data: 'flaredown'};
      if (this.filtered === true) {
        request["filter"] = {
          age: this.age_filter_values,
          sex: this.sex_filter_values,
          countries: this.country_filters_selection,
          events: this.event_filter.toLowerCase().trim().split(";")
        };
      }
      return request;
    },
    getPatterns() {
      const path = this.mode === 0 ? this.url + "rules" : this.url + "fis";
      this.overlay = true;
      setTimeout(
          function () {
            this.overlay_message = this.overlay
                ? "System is processing mined patterns.</br>" +
                "You can try increasing support (and/or confidence)."
                : "";
          }.bind(this),
          5000
      );
      axios
          .post(path, this.getRuleConfigRequest())
          .then(res => {
            if (res.data.toomany === "0") {
              this.overview = res.data.overview;
              this.rule_matrices = res.data.rule_matrices;
              this.matrices_columns = res.data.matrices_columns;
              this.maps_list = res.data.maps;
              this.sunbursts_list = res.data.sunbursts;
              this.count = res.data.count;
              this.clearSelections();
              this.generateDashboard();
            } else if (res.data.toomany === "1"){
              window.alert("Oops! \n Either the SPMF exceeded Heroku memory quota OR Number of patterns too high to process :( \n Please try increasing the support\\confidence.")
            }
          })
          .catch(error => {
            console.error(error);
          })
          .finally(() => {
            this.overlay = false;
            this.overlay_message = "";
          });
    },
    generateDashboard() {
      this.resetViews();
      if (this.mode === 0) this.generateDAGOverview();
      else
        d3.select("#dag")
            .selectAll("*")
            .remove();
    },
    resetViews(matrix_index = 0, update_table = true) {
      if (update_table) {
        if (this.selected_patterns_from_dag.length !== 0) {
          this.updateRuleTable(
              this.matrices_columns[this.current_matrix],
              this.selected_patterns_from_dag
          );
        } else if (this.rule_matrices.length > matrix_index) {
          this.updateRuleTable(
              this.matrices_columns[matrix_index],
              this.rule_matrices[matrix_index]
          );
        } else {
          d3.select("#rule_table")
              .selectAll("*")
              .remove();
        }
      }
      //when matrix list is empty, the following will contain data about all sequences at index 0
      this.map_series[0].z = this.maps_list[matrix_index].z;
      this.map_series[0].locations = this.maps_list[matrix_index].locations;
      this.sunburst_data[0].labels = this.sunbursts_list[matrix_index].labels;
      this.sunburst_data[0].ids = this.sunbursts_list[matrix_index].ids;
      this.sunburst_data[0].values = this.sunbursts_list[matrix_index].values;
      this.sunburst_data[0].parents = this.sunbursts_list[matrix_index].parents;
    },
    toggleOverviewLableVisibility() {
      d3.select("#dag")
          .selectAll(".label")
          .style("visibility", this.showLables ? "visible" : "hidden");
    },
    generateDAGOverview() {
      let vm = this;
      let nodes = this.overview.nodes;
      let links = this.overview.edges;
      let width = 300,
          height = 250,
          radius = 5;
      d3.select("#dag")
          .selectAll("*")
          .remove();
      this.updateOverviewAttrScale();
      let tooltip = d3.select(".tooltip");
      let svg = d3
          .select("#dag")
          .append("svg")
          .attr("viewBox", [0, 0, width, height]);

      // build the arrow.
      svg
          .append("svg:defs")
          .selectAll("marker")
          .data([
            {id: "end-arrow", opacity: 1},
            {id: "end-arrow-fade", opacity: 0.1}
          ])
          .enter()
          .append("svg:marker")
          .attr("id", function (d) {
            return d.id;
          })
          .attr("viewBox", "0 -5 10 10")
          .attr("refX", 15)
          .attr("refY", -1.5)
          .attr("markerWidth", 6)
          .attr("markerHeight", 6)
          .attr("fill", "#cbcbcb")
          .attr("orient", "auto")
          .append("svg:path")
          .attr("d", "M0,-5L10,0L0,5")
          .style("opacity", function (d) {
            return d.opacity;
          });

      let link = svg
          .append("g")
          .attr("class", "links")
          .selectAll("line")
          .data(links)
          .enter()
          .append("line")
          .attr("marker-end", "url(#end-arrow)");

      //https://bl.ocks.org/almsuarez/4333a12d2531d6c1f6f22b74f2c57102
      const linkedByCode = {};
      links.forEach(d => {
        linkedByCode[`${d.source},${d.target}`] = 1;
      });

      let node = svg
          .append("g")
          .attr("class", "nodes")
          .selectAll("g")
          .data(nodes)
          .enter()
          .append("g")
          .call(
              d3
                  .drag()
                  .on("start", dragstarted)
                  .on("drag", dragged)
                  .on("end", dragended)
          );

      let circles = node
          .append("circle")
          .attr("class", "dagnode")
          .attr("r", function (d) {
            return vm.overviewRadius(radius, d);
          })
          .attr("fill", function (d) {
            return vm.overviewColor(d);
          })
          .attr("selected", 0)
          .on("mouseover.tooltip", function (event, d) {
            tooltip
                .transition()
                .duration(300)
                .style("opacity", 0.8);
            tooltip
                .html(d.name)
                .style("left", event.pageX + "px")
                .style("top", event.pageY + 10 + "px");
          })
          .on("mouseover.fade", function (event, d) {
            fade(d, 0.1);
          })
          .on("mouseout.tooltip", function () {
            tooltip
                .transition()
                .duration(100)
                .style("opacity", 0);
          })
          .on("mouseout.fade", function (event, d) {
            fade(d, 1);
          })
          .on("mousemove", function (event) {
            tooltip.style("left", event.pageX + "px").style("top", event.pageY + 10 + "px");
          })
          .on("click", nodeSelected);
      let labels = node
          .append("text")
          .attr("class", "label")
          .attr("text-anchor", "center")
          .attr("dominant-baseline", "hanging")
          .style("font-family", "Arial")
          .style("font-size", "8px")
          .style("visibility", "visible")
          .text(function (d) {
            return d.name;
          });

      let simulation = d3
          .forceSimulation(nodes)
          .force("charge", d3.forceManyBody().strength(-210))
          .force("x", d3.forceX(width / 2).strength(0.25))
          .force("y", d3.forceY(height / 2).strength(0.25))
          .force(
              "link",
              d3
                  .forceLink()
                  .links(links)
                  .id(function (d) {
                    return d.code;
                  })
          )
          .on("tick", ticked);

      function nodeSelected(event, d) {
        let selected_node = d3.select(this);
        vm.selected_patterns_from_dag = [];
        vm.related_rule_ids = [];
        if (selected_node.attr("selected") === "1") {
          //already selected, so unselect and reset views
          selected_node
              .style("fill", vm.overviewColor(d))
              .attr("selected", 0)
              .attr("r", vm.overviewRadius(radius, d));
          vm.resetViews(vm.current_matrix);
        } //new one is selected
        else {
          circles
              .style("fill", function (circle) {
                return circle === d ? "#ffda00" : vm.overviewColor(circle);
              })
              .attr("r", function (circle) {
                let r = vm.overviewRadius(radius, circle);
                return circle === d ? r * 1.1 : r;
              })
              .attr("selected", function (circle) {
                return circle === d ? 1 : 0;
              });

          let event = d.name;
          let dag_index = d.dag_index;
          let matrix_rows = vm.rule_matrices[dag_index];
          if (dag_index !== vm.current_matrix)//how can I make the performance even worse? oh I know!
            matrix_rows = vm.getGroupStat(vm.matrices_columns[dag_index], matrix_rows);

          for (let i = 0; i < matrix_rows.length; i++) {
            if (matrix_rows[i][event] !== "") {
              vm.selected_patterns_from_dag.push(matrix_rows[i]);
              if (matrix_rows[i]["level"] === 1) {
                vm.related_rule_ids.push(matrix_rows[i].rid);
              }
            }
          }
          vm.current_matrix = dag_index;
          vm.updateRuleTable(vm.matrices_columns[dag_index], vm.selected_patterns_from_dag);
        }
      }

      function updateLinks() {
        link
            .attr("x1", function (d) {
              return d.source.x;
            })
            .attr("y1", function (d) {
              return d.source.y;
            })
            .attr("x2", function (d) {
              return d.target.x;
            })
            .attr("y2", function (d) {
              return d.target.y;
            });
      }

      function updateNodes() {
        node.attr("transform", function (d) {
          let x = Math.max(radius, Math.min(width - radius, d.x));
          let y = Math.max(radius, Math.min(height - radius, d.y));
          return "translate(" + x + "," + y + ")";
        });
      }

      function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }

      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }

      function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }

      function isConnected(a, b) {
        return (
            linkedByCode[`${a.code},${b.code}`] ||
            linkedByCode[`${b.code},${a.code}`] ||
            a.code === b.code
        );
      }

      function fade(d, opacity) {
        node.style("stroke-opacity", function (o) {
          const thisOpacity = isConnected(d, o) ? 1 : opacity;
          this.setAttribute("fill-opacity", thisOpacity);
          return thisOpacity;
        });
        link.style("stroke-opacity", o => (o.source === d || o.target === d ? 1 : opacity));

        link.attr("marker-end", function (o) {
          return opacity === 1 || o.source === d || o.target === d
              ? "url(#end-arrow)"
              : "url(#end-arrow-fade)";
        });
      }

      function ticked() {
        updateLinks();
        updateNodes();
      }
    },

    getGroupStat(matrix_columns, matrix_rows) {
      matrix_rows.sort(function (a, b) {
        return d3.ascending(a["group"], b["group"]) || d3.descending(a["level"], b["level"]);
      });
      let stats = {};
      let g_count = 0;
      for (let i = 0; i < matrix_rows.length; i++) {
        if (matrix_rows[i].level === 0) {
          for (let j = 0; j < matrix_columns.length; j++) {
            if (matrix_columns[j] === "support" || matrix_columns[j] === "confidence")
              matrix_rows[i][matrix_columns[j]] = (stats[matrix_columns[j]] / g_count)
                  .toFixed(2)
                  .toString();
            //average
            else if (stats[matrix_columns[j]]) {
              for (let z = 0; z < stats[matrix_columns[j]].length; z++) {
                stats[matrix_columns[j]][z].count = stats[matrix_columns[j]][z].count / g_count;
              }
              matrix_rows[i][matrix_columns[j]] = stats[matrix_columns[j]];
            } else matrix_rows[i][matrix_columns[j]] = [];
          }
          stats = {};
          g_count = 0;
          continue;
        }

        for (let j = 0; j < matrix_columns.length; j++) {
          let val = matrix_rows[i][matrix_columns[j]];
          if (matrix_columns[j] === "support" || matrix_columns[j] === "confidence") {
            matrix_columns[j] in stats
                ? (stats[matrix_columns[j]] += +val)
                : (stats[matrix_columns[j]] = +val);
          } else if (val.length !== 0) {
            if (!(matrix_columns[j] in stats)) {
              if (val.includes("A"))
                stats[matrix_columns[j]] = [
                  {tag: "A.", count: 0},
                ];
              else if (this.mode === 0) {
                stats[matrix_columns[j]] = [
                  {tag: "C.", count: 0}
                ];
              } else {
                stats[matrix_columns[j]] = [
                  {tag: "I", count: 0}
                ];
              }
            }
            for (let z = 0; z < stats[matrix_columns[j]].length; z++) {
              if (val.length !== 0) {
                if ((this.mode === 0 && stats[matrix_columns[j]][z].tag === val.slice(0,2)) || this.mode === 1) {
                  stats[matrix_columns[j]][z].count++;
                  break;
                }
              }

            }
          }
        }
        g_count++;
      }
      matrix_rows.sort(function (a, b) {
        return d3.ascending(a["group"], b["group"]) || d3.ascending(a["level"], b["level"]);
      });
      return matrix_rows;
    },
    updateRuleTable(matrix_columns, matrix_rows) {
      let vm = this;
      let tooltip = d3.select(".tooltip");
      let cell_width = 30;
      let group_cell_height = 30;
      let xScale = d3
          .scaleBand()
          .domain([0])
          .range([0, cell_width])
          .paddingOuter(0.6);
      let yScale = d3
          .scaleLinear()
          .domain([0, 1])
          .range([0, group_cell_height - 2]);

      function itemCircle(selection) {
        let unit_radius = cell_width / 2 - 1;
        let center = cell_width / 2;
        let tooltip_dict = {
          "M": " (Treatment)", "S": " (Symptom)", "C": " (Condition)", "F": " (Food)",
          "T": " (Tag)","M.": " (Treatment)", "S.": " (Symptom)", "C.": " (Condition)", "F.": " (Food)",
          "T.": " (Tag)"
        }
        selection
            .append("svg")
            .attr("width", cell_width)
            .attr("height", cell_width)
            .append("circle")
            .attr("cx", center)
            .attr("cy", center)
            .attr("r", unit_radius)
            .style("fill", function (d) {
              return vm.colorPicker(d.v);

            })
            .on("mouseover", function (event, d) {
              tooltip
                  .transition()
                  .duration(200)
                  .style("opacity", 0.9);
              tooltip
                  .html(d.k + tooltip_dict[d.v.slice(-2)])
                  .style("left", event.pageX + "px")
                  .style("top", event.pageY - 28 + "px");
            })
            .on("mouseout", function () {
              tooltip
                  .transition()
                  .duration(500)
                  .style("opacity", 0);
            });
      }

      function percentageRect(selection, fill) {
        let svgs = selection
            .append("svg")
            .attr("width", 100)
            .attr("height", 14);
        svgs
            .append("rect")
            .style("fill", fill)
            .attr("rx", 5)
            .attr("height", 12)
            .attr("width", function (d) {
              return d.v * 100;
            });
        svgs
            .append("text")
            .attr("dx", 40)
            .attr("dy", 9)
            .attr("fill", "black")
            .text(function (d) {
              return d.v;
            });
      }

      function itemBarChart(selection) {
        selection
            .append("svg")
            .attr("width", cell_width)
            .attr("height", group_cell_height)
            .on("mouseover", function (event, d) {
              tooltip
                  .transition()
                  .duration(200)
                  .style("opacity", 0.9);
              tooltip
                  .html(d.k)
                  .style("left", event.pageX + "px")
                  .style("top", event.pageY - 28 + "px");
            })
            .on("mouseout", function () {
              tooltip.transition().style("opacity", 0);
            })
            .selectAll("rect")
            .data(function (d) {
              return d.v;
            })
            .enter()
            .append("rect")
            .attr("x", function (d, i) {
              return xScale(i);
            })
            .attr("y", function (d, i) {
              return group_cell_height - yScale(d.count);
            })
            .style("fill", function (d) {
              return vm.colorPicker(d.tag);
            })
            .attr("width", xScale.bandwidth())
            .attr("height", function (d) {
              return yScale(d.count);
            })
            .attr("rx", 2);
      }

      // clear previous table
      d3.select("#rule_table")
          .selectAll("*")
          .remove();
      this.rule_table_sort_clicks = {};
      this.rule_table_sort_order = [];

      // create a new table
      let table = d3.select("#rule_table").append("table");
      // headers-----
      let thead = table.append("thead").append("tr");

      let headers = thead
          .selectAll("th")
          .data(matrix_columns)
          .enter()
          .append("th")
          .style("width", function (d) {
            return d === "support" || d === "confidence" ? 100 : 30;
          });

      let header_text = headers.append('div')
          .text(function (d) {
            return d;
          });
      header_text.filter(function (d) {
        return d !== "support" && d !== "confidence";
      }).classed("rotate", true);

      headers
          .append("text")
          .classed("fa", true)
          .text("\uf0dc");

      headers.on("mouseover", function (event, d) {
        tooltip
            .transition()
            .duration(200)
            .style("opacity", 0.9);
        tooltip
            .html(d)
            .style("left", event.pageX + "px")
            .style("top", event.pageY - 40 + "px");
      })
          .on("mouseout", function () {
            tooltip
                .transition()
                .duration(500)
                .style("opacity", 0);
          });

      matrix_columns.forEach(function (column) {
        vm.rule_table_sort_clicks[column] = -1;//-1,0=des,1=asc
      });

      // body and rows -----
      if (this.grouped) {
        matrix_rows = this.getGroupStat(matrix_columns, matrix_rows);
      }

      let tbody = table.append("tbody");
      let rows = tbody
          .selectAll("tr")
          .data(
              this.grouped
                  ? matrix_rows
                  : matrix_rows.filter(function (row) {
                    return row.level === 1;
                  })
          )
          .enter()
          .append("tr");

      let rule_rows = rows.filter(function (d) {
        return d.level === 1;
      });
      let group_rows = rows.filter(function (d) {
        return d.level === 0 && d.support !== "NaN";
      });

      rule_rows.style("display", this.grouped ? "none" : "table-row");
      group_rows.classed("group-row", true).attr("collapsed", 0);

      group_rows.on("click", function (event, d) {
        let selected_group = d3.select(this);
        let children = rule_rows.filter(function (row) {
          return row.group === d.group;
        });
        if (selected_group.attr("collapsed") === "1") {
          children.style("display", "none");
          selected_group.attr("collapsed", 0);
        } else {
          children.style("display", "table-row");
          selected_group.attr("collapsed", 1);
        }
      });


      //row cells
      let rule_cells = rule_rows
          .selectAll("td")
          .data(function (d) {
            return matrix_columns.map(function (key) {
              return {v: d[key], k: key};
            });
          })
          .enter()
          .append("td");

      rule_cells
          .filter(function (d) {
            return typeof d.v == "number";
          })
          .call(percentageRect, "#C5E1A5");
      rule_cells
          .filter(function (d) {
            return (typeof d.v == "string") & (d.v.length !== 0);
          })
          .style("width", 100)
          .call(itemCircle);

      let group_cells = group_rows
          .selectAll("td")
          .data(function (d) {
            return matrix_columns.map(function (key) {
              return {v: d[key], k: key};
            });
          })
          .enter()
          .append("td");
      group_cells
          .filter(function (d) {
            return typeof d.v == "object" && d.v.length !== 0;
          })
          .call(itemBarChart);
      group_cells
          .filter(function (d) {
            return (typeof d.v == "string") & (d.length !== 0);
          })
          .style("width", 100)
          .call(percentageRect, "#65b72a")
          .on("mouseover", function (event, d) {
            tooltip
                .transition()
                .duration(200)
                .style("opacity", 0.9);
            tooltip
                .html("average in group")
                .style("left", event.pageX + "px")
                .style("top", event.pageY - 28 + "px");
          })
          .on("mouseout", function () {
            tooltip.transition().style("opacity", 0);
          });

      // sort by column
      headers.on("click", function (event, column) {
        let header = d3.select(this);
        let clicks = vm.rule_table_sort_clicks[column];
        let order = vm.rule_table_sort_order.indexOf(column)
        switch (clicks) {
          case -1:
            vm.rule_table_sort_clicks[column] = 0;
            header.classed("sort", true);
            header.select(".fa").text("\uf0dd");
            break;
          case 0:
            vm.rule_table_sort_clicks[column] = 1;
            header.classed("sort", true);
            header.select(".fa").text("\uf0de");
            break;
          case 1:
            vm.rule_table_sort_clicks[column] = -1;
            vm.rule_table_sort_order.splice(order, 1);
            header.classed("sort", false);
            header.select(".fa").text("\uf0dc");
            header.selectAll(".sort-circle").remove("*")
            //update numbers once something is removed
            d3.selectAll(".sort-circle").text(function (d) {
              return vm.rule_table_sort_order.indexOf(d) + 1
            })
            break;
        }
        if (order === -1) {
          vm.rule_table_sort_order.push(column)
          header.append("text")
              .classed("sort-circle", true)
              .text(vm.rule_table_sort_order.length)
              .style("transform", "translate(" + (column === 'support' || column === 'confidence' ? 45 : 10) + "px, 0px)");
        }

        rows.sort(function (a, b) {
          let sort_cond = 0
          if (vm.grouped) {
            sort_cond = d3.ascending(a["group"], b["group"]) ||
                d3.ascending(a["level"], b["level"])
          }
          vm.rule_table_sort_order.forEach(function (col) {
            clicks = vm.rule_table_sort_clicks[col]
            //columns in order list have either 0 or 1 in clicks dictionary
            sort_cond ||= (clicks === 0 ? d3.descending(a[col], b[col]) : d3.ascending(a[col], b[col]))
          });
          return sort_cond
        });
      });
    },
    groupHandler() {
      this.resetViews(this.current_matrix, true);
    },
    colorPicker(value) {
      if (value==='I' || !value.includes("."))
        return "#BA68C8";
      if (value.includes("A."))
        return "#29B6F6";
      return "#FF8A65";
    },
    setUpTooltip() {
      d3.select("body")
          .append("div")
          .attr("class", "tooltip")
          .style("opacity", 0);
    },
    updateOverviewAttrScale() {
      let min, max;
      if (this.color_choice === "frequency") {
        min = this.overview.min_f;
        max = this.overview.max_f;
      } else {
        min = this.overview.min_c;
        max = this.overview.max_c;
      }
      this.overview_attr_scale = {
        color: d3.scaleSequential(["#90A4AE", "#263238"]).domain([min, max]),
        radius: d3
            .scaleLinear()
            .domain([min, max])
            .range([1, 1.5])
      };
    },
    overviewRadius(unit_r, node) {
      if (
          this.overview_attr_scale === null ||
          this.color_choice === null ||
          this.color_choice === "none"
      )
        return unit_r;
      let radius_scale = this.overview_attr_scale["radius"];
      if (this.color_choice === "frequency") return radius_scale(node.f) * unit_r;
      if (this.color_choice === "centrality") return radius_scale(node.c) * unit_r;
    },
    overviewColor(node) {
      if (
          this.overview_attr_scale === null ||
          this.color_choice === null ||
          this.color_choice === "none"
      )
        return "#5b5b5b";
      let color_scale = this.overview_attr_scale["color"];
      if (this.color_choice === "frequency") return color_scale(node.f);
      if (this.color_choice === "centrality") return color_scale(node.c);
    },
    colourOverview() {
      this.updateOverviewAttrScale();
      let vm = this;
      d3.selectAll(".dagnode[selected='0']")
          .transition()
          .duration(500)
          .ease(d3.easeLinear)
          .style("fill", function (d) {
            return vm.overviewColor(d);
          })
          .attr("r", function (d) {
            return vm.overviewRadius(5, d);
          });
      d3.select(".dagnode[selected='1']").transition()
          .duration(500)
          .ease(d3.easeLinear)
          .attr("r", function (d) {
            return vm.overviewRadius(5, d);
          }).style("fill", "#ffda00")
    },
    setUpFilterForm() {
      const path = this.url + "filter_options";
      axios
          .get(path, {params: {data: 'flaredown'}})
          .then(res => {
            this.age_filter_items = res.data.age;
            this.age_filter_values = res.data.age;
            this.sex_filter_items = res.data.sex;
            this.sex_filter_values = res.data.sex;
            this.country_filters = res.data.country;
          })
          .catch(error => {
            console.error(error);
          });
    },
    mineClicked()
    {
      this.mine_clicked++;
      this.getPatterns();
    },
    tabSwitch() {
      if (this.mode === 1)
        this.rule_options.support = 20; //support of 1% generates over 20K patterns,exceeds heroku memory quota and takes too long
      else
        this.rule_options.support = 1.5;
      this.mine_clicked=0;
      this.getPatterns();
    }
  },
  created() {
    this.setUpTooltip();
    this.setUpFilterForm();
    this.getPatterns();
  }
};
</script>
