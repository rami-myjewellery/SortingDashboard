import { createRouter, createWebHistory } from 'vue-router'
import Sorting from '../views/Sorting.vue'
// Import each view directly
import GeekPicking from '../views/GeekPicking.vue'
import GeekInbound from '../views/GeekInbound.vue'
import ErrorLanes from '../views/ErrorLanes.vue'
import FMA from '../views/FMA.vue'
import MonoPicking from '../views/MonoPicking.vue'
import InboundAndBulk from '../views/InboundAndBulk.vue'
import Returns from '../views/Returns.vue'

const routes = [
    { path: '/GeekPicking',            component: GeekPicking },
    { path: '/GeekPicking/userKPI',    component: GeekPicking },

    { path: '/GeekInbound',            component: GeekInbound },
    { path: '/GeekInbound/userKPI',    component: GeekInbound },

    { path: '/ErrorLanes',             component: ErrorLanes },
    { path: '/ErrorLanes/userKPI',     component: ErrorLanes },

    { path: '/FMA',                    component: FMA },
    { path: '/FMA/userKPI',            component: FMA },

    { path: '/Sorting',                component: Sorting },
    { path: '/Sorting/userKPI',        component: Sorting },

    { path: '/MonoPicking',            component: MonoPicking },
    { path: '/MonoPicking/userKPI',    component: MonoPicking },

    { path: '/InboundAndBulk',         component: InboundAndBulk },
    { path: '/InboundAndBulk/userKPI', component: InboundAndBulk },

    { path: '/Returns',                component: Returns },
    { path: '/Returns/userKPI',        component: Returns },
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
