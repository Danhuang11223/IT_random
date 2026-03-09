import { createRouter, createWebHistory } from "vue-router";
import ForgotPasswordView from "./views/ForgotPasswordView.vue";
// 👇 1. 引入新页面 👇
import ResetPasswordConfirmView from "./views/ResetPasswordConfirmView.vue";
import { getStoredToken } from "./api";
import AuthLayout from "./layouts/AuthLayout.vue";
import DashboardLayout from "./layouts/DashboardLayout.vue";
import DashboardView from "./views/DashboardView.vue";
import HistoryView from "./views/HistoryView.vue";
import LoginView from "./views/LoginView.vue";
import RegisterView from "./views/RegisterView.vue";
import SavedView from "./views/SavedView.vue";

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
      {
        path: "forgot-password",
        name: "forgotPassword",
        component: ForgotPasswordView,
      },
      // 👇 2. 新增带参数的重置密码确认路由 👇
      {
        path: "reset-password-confirm/:uid/:token",
        name: "resetPasswordConfirm",
        component: ResetPasswordConfirmView,
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
      {
        path: "saved",
        name: "saved",
        component: SavedView,
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