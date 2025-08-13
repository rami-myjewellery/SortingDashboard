import { createRouter, createWebHistory } from 'vue-router'
import Sorting from '../views/Sorting.vue'
// Import each view directly
import GeekPicking from '../views/GeekPicking.vue'
import GeekInbound from '../views/GeekInbound.vue'
import ErrorLanes from '../views/ErrorLanes.vue'
import InboundAndBulk from '../views/InboundAndBulk.vue'
import Returns from '../views/Returns.vue'
import Picking from "@/views/Picking.vue";
import Replenishment from "@/views/Replenishment.vue";

const routes = [
    { path: '/GeekPicking',            component: GeekPicking },
    { path: '/GeekPicking/userKPI',    component: GeekPicking },

    { path: '/GeekInbound',            component: GeekInbound },
    { path: '/GeekInbound/userKPI',    component: GeekInbound },

    { path: '/ErrorLanes',             component: ErrorLanes },
    { path: '/ErrorLanes/userKPI',     component: ErrorLanes },

    { path: '/Replenishment',                    component: Replenishment },
    { path: '/Replenishment/userKPI',            component: Replenishment },

    { path: '/Sorting',                component: Sorting },
    { path: '/Sorting/userKPI',        component: Sorting },

    { path: '/Picking',            component: Picking },
    { path: '/Picking/userKPI',    component: Picking },

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
