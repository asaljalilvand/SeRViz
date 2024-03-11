import 'bootstrap/dist/css/bootstrap.css';
import Vue from 'vue';
import App from './App.vue';
import router from './router';
import vuetify from './plugins/vuetify';

Vue.config.productionTip = false;

// router.beforeEach((to, from, next) => {
//   let isAuthenticated = window.localStorage.getItem("authenticated");
//   if (to.name !== 'Login' && !isAuthenticated)
//     return next({name: 'Login'});
//   else if (to.name === 'Login' && isAuthenticated) {
//     return next({name: 'SPM'});
//   } else {
//     return next()
//   }
// })

new Vue({
  router,
  vuetify,
  render: h => h(App)
}).$mount('#app');
