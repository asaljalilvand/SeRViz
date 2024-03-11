<template>
  <div class="container">
    <button type="button" class="btn btn-primary">{{ msg }}</button>
  </div>
</template>

<script>
import axios from "axios";
import { BACKEND_URL } from "./backend";

export default {
  name: "Ping",
  data() {
    return {
      url: BACKEND_URL,
      msg: "Pong!"
    };
  },
  methods: {
    getMessage() {
      const path = this.url + "ping";
      axios
        .get(path)
        .then(res => {
          this.msg = res.data;
        })
        .catch(error => {
          // eslint-disable-next-line
          console.error(error);
        });
    }
  },
  created() {
    this.getMessage();
  }
};
</script>
