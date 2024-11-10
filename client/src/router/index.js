import { createRouter, createWebHistory } from 'vue-router'
import HomeComponent from "@/components/HomeComponent.vue";
import GameQuiz from "@/components/GameQuiz.vue";
import AuthComponent from "@/components/AuthComponent.vue";
import LoginComponent from "@/components/LoginComponent.vue";
import RegisterComponent from "@/components/RegisterComponent.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeComponent
    },
    {
      path: '/game',
      name: 'game',
      component: GameQuiz
    },
    {
      path: '/auth',
      name: 'auth',
      component: AuthComponent,
      children: [
        {
          path: '/login',
          name: 'login',
          component: LoginComponent
        },
        {
          path: '/register',
          name: 'register',
          component: RegisterComponent
        },
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: { name: 'home' }
    }
  ]
})

export default router
