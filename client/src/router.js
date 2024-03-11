import Vue from 'vue';
import Router from 'vue-router';
import SPM from "./components/SPM";
import Flaredown from "./components/Flaredown";
import Ping from './components/Ping.vue';
import Home from "@/components/Home";

Vue.use(Router);

export default new Router({
    mode: 'history',
    base: process.env.BASE_URL,
    routes: [
        {
            path: '/',
            name: 'Home',
            component: Home,
        },
        {
            path: '/airport',
            name: 'SPM',
            component: SPM,
        },
        {
            path: '/flaredown',
            name: 'Flaredown',
            component: Flaredown,
        },
        {
            path: '/ping',
            name: 'Ping',
            component: Ping,
        }
    ],
});
