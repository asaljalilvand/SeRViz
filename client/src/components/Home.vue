<template>
  <div>
    <v-row class="m-lg-5" justify="center" style="color: #37474F;text-align: center">
      <h1>Welcome to SeRVis: an Interactive Visualization Framework for the Analysis of Sequential Rules and Frequent
        Itemsets</h1><br/>
    </v-row>


    <v-row justify="center">
      <h3 style="color: #37474F">Select a dataset to explore</h3>
    </v-row>

    <v-row class="m-1 p-1" justify="center">
      <v-col md="5">

        <v-card color="light-blue lighten-5"
                height="100%"
                hover
                disabled
                to="airport"

        >
          <v-img
              height="250"
              width="100%"
              src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Airbus_A380-800_of_Lufthansa_in_Frankfurt_Germany_-_Aircraft_ground_handling_at_FRA_EDDF.jpg/1920px-Airbus_A380-800_of_Lufthansa_in_Frankfurt_Germany_-_Aircraft_ground_handling_at_FRA_EDDF.jpg"
          ></v-img>

          <v-card-title>
            <span class="headline">Airport Ground Handling Log</span>
          </v-card-title>
          <v-card-subtitle style="color: red;font-weight: bold">
            Disabled until permission from airport granted for using anonymized data
          </v-card-subtitle>

           <v-list-item>
             <v-list-item-content>
               <v-list-item-title>Anonymized due to NDA restrictions</v-list-item-title>
             </v-list-item-content>
           </v-list-item>

           <v-list-item>
             <v-list-item-content two-line>
               <v-list-item-title>Mining disabled</v-list-item-title>
               <v-list-item-subtitle>Pattern exploration with a pre-minded set of patterns</v-list-item-subtitle>
             </v-list-item-content>
           </v-list-item>



          <v-card-actions>
            <v-spacer></v-spacer>
          </v-card-actions>
        </v-card>

      </v-col>

      <v-col md="5">
        <v-card color="lime lighten-5"
                height="100%"
                hover
                to="flaredown"
        >
          <v-img
              height="250"
              width="100%"
              src="https://lithub.com/wp-content/uploads/2019/03/pills.jpg"
          ></v-img>
          <v-card-title>
            <span class="headline">Flaredown Symptom Tracker</span>
          </v-card-title>

          <v-list-item two-line>
            <v-list-item-content>
              <v-list-item-title>Chronic illness: symptoms, treatments and triggers</v-list-item-title>
              <v-list-item-subtitle><a href="https://www.kaggle.com/flaredown/flaredown-autoimmune-symptom-tracker">
                Public dataset on Kaggle</a></v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>

          <v-list-item>
            <v-list-item-content two-line>
              <v-list-item-title>Detail-on-demand views disabled</v-list-item-title>
              <v-list-item-subtitle  class="text-wrap"><p>
                The time complexity for finding the correct match for each pattern in a sequence
                with complex events will be too high.<br>
                The SPMF library does not provide list of sequence ids for each pattern (mined with TRuleGrowth) as of
                May 2021.</p></v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>

          <v-card-actions>
            <v-spacer></v-spacer>
          </v-card-actions>
        </v-card>
      </v-col>

    </v-row>
    <v-row justify="center">

      <v-col sm="1"
             class="text-center"
      >
        <v-btn
            large
            icon
            fab
            depressed
            outlined
            href="https://github.com/AsalJalilvand/SeRVis"
        >
          <v-icon
              large
          >
            fab fa-github
          </v-icon>
        </v-btn>
      </v-col>
      <v-col sm="1"
             class="text-center"
      >
        <v-btn
            large
            icon
            fab
            depressed
            outlined
            href="https://dalspace.library.dal.ca/handle/10222/80445"
        >
          <v-icon
              large
          >
            fas fa-university
          </v-icon>
        </v-btn>
      </v-col>
      <v-col sm="1"
             class="text-center"
      >
        <v-btn
            large
            icon
            fab
            depressed
            outlined
            href="https://youtu.be/snxpXPj1Vmg"
        >
          <v-icon
              large
          >
            fab fa-youtube
          </v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </div>
</template>

<script>

export default {
  name: "Home",
}
</script>

<style scoped>
.v-btn::before {
  background-color: transparent !important;
}
</style>