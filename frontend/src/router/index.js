import { createRouter, createWebHistory } from "vue-router"

import Home from "../views/Home.vue"
import About from "../views/About.vue"
import Login from "../views/Login.vue"
import Register from "../views/Register.vue"
import Groups from "../views/Groups.vue"
import GroupDetails from "../views/GroupDetails.vue"
import Settings from "../views/Settings.vue"
import GroupStats from "../views/GroupStats.vue"
import CategoryStats from "../views/CategoryStats.vue"
import { useAuth } from "../composables/useAuth"

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home
  },
  {
    path: "/about",
    name: "About",
    component: About
  },
  {
    path: "/login",
    name: "Login",
    component: Login
  },
  {
    path: "/register",
    name: "Register",
    component: Register
  },
  {
    path: "/groups",
    name: "Groups",
    component: Groups,
    meta: { requiresAuth: true }
  },
  {
    path: "/groups/:id",
    name: "GroupDetails",
    component: GroupDetails,
    meta: { requiresAuth: true }
  },
  {
    path: "/groups/:id/stats",
    name: "GroupStats",
    component: GroupStats,
    meta: { requiresAuth: true }
  },
  {
    path: "/settings",
    name: "Settings",
    component: Settings,
    meta: { requiresAuth: true }
  },
  {
    path: "/groups/:id/categories/:categoryId",
    name: "CategoryStats",
    component: CategoryStats,
    meta: { requiresAuth: true },
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const auth = useAuth()

router.beforeEach(async (to, from, next) => {
  if (!auth.authLoaded.value) {
    await auth.fetchCurrentUser()
  }

  if (to.meta.requiresAuth && !auth.currentUser.value) {
    next({ name: "Login", query: { redirect: to.fullPath } })
    return
  }

  next()
})

export default router
