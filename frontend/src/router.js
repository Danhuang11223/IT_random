import { createRouter, createWebHistory } from "vue-router";

import { getStoredToken } from "./api";
import AuthLayout from "./layouts/AuthLayout.vue";
import DashboardLayout from "./layouts/DashboardLayout.vue";
import DashboardView from "./views/DashboardView.vue";
import HistoryView from "./views/HistoryView.vue";
import LoginView from "./views/LoginView.vue";
import RegisterView from "./views/RegisterView.vue";

const routes = [
  {
    path: "/",
    redirect: () => (getStoredToken() ? "/dashboard" : "/login"),
  },
  {
    path: "/",
    component: AuthLayout,
    meta: { guestOnly: true },
    children: [
      {
        path: "login",
        name: "login",
        component: LoginView,
      },
      {
        path: "register",
        name: "register",
        component: RegisterView,
      },
    ],
  },
  {
    path: "/",
    component: DashboardLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "dashboard",
        name: "dashboard",
        component: DashboardView,
      },
      {
        path: "history",
        name: "history",
        component: HistoryView,
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const hasToken = Boolean(getStoredToken());

  if (to.matched.some((record) => record.meta.requiresAuth) && !hasToken) {
    return { name: "login" };
  }

  if (to.matched.some((record) => record.meta.guestOnly) && hasToken) {
    return { name: "dashboard" };
  }

  return true;
});

export default router;
