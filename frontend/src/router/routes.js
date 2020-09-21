import DashboardLayout from "@/layout/dashboard/DashboardLayout";

// Pages outside of Dashboard
import Login from "@/pages/Login";
import Register from "@/pages/Register";

// GeneralViews
import NotFound from "@/pages/NotFoundPage";

// Application Views
import Overview from "@/views/Overview";
import History from "@/views/History";
import Market from "@/views/Market";
import Exchange from "@/views/Exchange";
import Stores from "@/views/Stores";

// Everything else
import store from "@/store/index";


const requireAuthenticated = (to, from, next) => {
  store.dispatch("auth/initialize")
    .then(() => {
      if (!store.getters["auth/isAuthenticated"]) {
        next("/login");
      } else {
        next();
      }
    });
};

const requireAnonymous = (to, from, next) => {
  store.dispatch("auth/initialize")
    .then(() => {
      if (store.getters["auth/isAuthenticated"]) {
        next("/");
      } else {
        next();
      }
    });
};

const redirectLogout = (to, from, next) => {
  store.dispatch("auth/logout")
    .then(() => next("/login"));
};


const routes = [
  {
    path: "/",
    name: "dashboard",
    component: DashboardLayout,
    beforeEnter: requireAuthenticated,
    children: [
      {
        path: "",
        name: "home",
        component: Overview
      },
      {
        path: "history",
        name: "history",
        component: History
      },
      {
        path: "market",
        name: "market",
        component: Market
      },
      {
        path: "exchange",
        name: "exchange",
        component: Exchange
      },
      {
        path: "stores",
        name: "stores",
        component: Stores
      }
    ]
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
