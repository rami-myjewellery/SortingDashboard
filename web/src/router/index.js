import { createRouter, createWebHistory } from 'vue-router'
import Sorting from '../views/Sorting.vue'
const routes = [
    { path: '/GeekPicking', component: Sorting },
    { path: '/GeekInbound', component: Sorting },
    { path: '/ErrorLanes', component: Sorting },
    { path: '/FMA', component: Sorting },
    { path: '/Sorting', component: Sorting },
    { path: '/MonoPicking', component: Sorting },
    { path: '/InboundAndBulk', component: Sorting },
    { path: '/Returns', component: Sorting },
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
