import { createRouter, createWebHistory } from 'vue-router'
import LayoutFrame from '../layout/LayoutFrame.vue'
import SVCView from "../views/SVCView.vue";
import HomeView from "../views/HomeView.vue";
import RMView from "../views/RMView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: LayoutFrame,
      children: [
        { path: '', component: HomeView },
        { path: 'svc', name:'svc', component: SVCView},
        { path: 'rm', name: 'rm', component: RMView },
      ]
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue')
    }
  ]
})

export default router
