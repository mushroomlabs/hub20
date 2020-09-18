import DashboardLayout from '@/layout/dashboard/DashboardLayout';
// GeneralViews
import NotFound from '@/pages/NotFoundPage';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import store from '@/store/index';


const requireAuthenticated = (to, from, next) => {
  store.dispatch('auth/initialize')
    .then(() => {
      if (!store.getters['auth/isAuthenticated']) {
        next('/login');
      } else {
        next();
      }
    });
};

const requireAnonymous = (to, from, next) => {
  store.dispatch('auth/initialize')
    .then(() => {
      if (store.getters['auth/isAuthenticated']) {
        next('/');
      } else {
        next();
      }
    });
};

const redirectLogout = (to, from, next) => {
  store.dispatch('auth/logout')
    .then(() => next('/login'));
};


const routes = [
  {
    path: "/",
    name: "home",
    component: DashboardLayout,
    beforeEnter: requireAuthenticated
  },
  {
    path: "/login",
    name: "login",
    component: Login,
    beforeEnter: requireAnonymous
  },
  {
    path: "/logout",
    name: "logout",
    beforeEnter: redirectLogout
  },
  {
    path: "/register",
    name: "register",
    component: Register,
    beforeEnter: requireAnonymous
  },
  { path: "*", component: NotFound }
];

export default routes;
