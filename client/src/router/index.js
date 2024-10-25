import { createRouter, createWebHistory } from 'vue-router'
import HomeComponent from "@/components/HomeComponent.vue";
import GameQuiz from "@/components/GameQuiz.vue";

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
    }
  ]
})

export default router
