import Vue from 'vue'
import VueRouter from 'vue-router'
import {default as routes, requireServerConnection} from './routes'
Vue.use(VueRouter)

const router = new VueRouter({
  routes,
  mode: 'history',
  linkActiveClass: 'active'
})

router.beforeEach(requireServerConnection)

export default router
