import DashboardLayout from '@/layout/dashboard/DashboardLayout'

// Pages outside of Dashboard
import Login from '@/pages/Login'
import Register from '@/pages/Register'

// GeneralViews
import NotFound from '@/pages/NotFoundPage'

// Application Views
import Overview from '@/views/Overview'
import History from '@/views/History'
import Funding from '@/views/Funding'
import Deposit from '@/views/Deposit'
import Transfer from '@/views/Transfer'
import Stores from '@/views/Stores'
import StoreDetail from '@/views/StoreDetail'

// Everything else
import store from '@/store/index'

const requireAuthenticated = (to, from, next) => {
  store.dispatch('initialize').then(() => {
    if (!store.getters['auth/isAuthenticated']) {
      next('/login')
    } else {
      next()
    }
  })
}

const requireAnonymous = (to, from, next) => {
  store.dispatch('initialize').then(() => {
    if (store.getters['auth/isAuthenticated']) {
      next('/')
    } else {
      next()
    }
  })
}

const redirectLogout = (to, from, next) => {
  store.dispatch('auth/logout').then(() => next('/login'))
}

const routes = [
  {
    path: '/',
    component: DashboardLayout,
    beforeEnter: requireAuthenticated,
    children: [
      {
        path: '',
        name: 'home',
        component: Overview
      },
      {
        path: 'history',
        name: 'history',
        component: History
      },
      {
        path: 'funding',
        name: 'funding',
        component: Funding
      },
      {
        path: 'receive/:token',
        name: 'payment-order',
        component: Deposit,
        meta: {
          viewTitle: 'Request Payment'
        }
      },
      {
        path: 'deposit/:token',
        name: 'deposit',
        component: Deposit
      },
      {
        path: 'send/:token',
        name: 'withdraw',
        component: Transfer,
        meta: {
          viewTitle: 'Send'
        }
      },
      {
        path: 'transfer/:token',
        name: 'transfer',
        component: Transfer,
        meta: {
          viewTitle: 'Send Payment'
        }
      },
      {
        path: 'stores',
        name: 'stores',
        component: Stores
      },
      {
        path: 'store/new',
        name: 'store-create',
        component: StoreDetail,
        meta: {
          viewTitle: 'Add Store'
        }
      },
      {
        path: 'store/:id',
        name: 'store',
        component: StoreDetail
      }
    ]
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
    beforeEnter: requireAnonymous
  },
  {
    path: '/logout',
    name: 'logout',
    beforeEnter: redirectLogout
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
    beforeEnter: requireAnonymous
  },
  {path: '*', component: NotFound}
]

export default routes
