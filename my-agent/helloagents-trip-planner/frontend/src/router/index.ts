import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Result from '@/views/Result.vue'
import TravelAgentPanel from '@/components/TravelAgentPanel.vue'
import ChatAgentPanel from '@/components/ChatAgentPanel.vue'
import AgentTemplateTwo from '@/components/AgentTemplateTwo.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/agents/travel'
    },
    {
      path: '/agents',
      component: Home,
      children: [
        {
          path: '',
          redirect: '/agents/travel'
        },
        {
          path: 'travel',
          name: 'TravelAgent',
          component: TravelAgentPanel
        },
        {
          path: 'chat',
          name: 'ChatAgent',
          component: ChatAgentPanel
        },
        {
          path: 'template-2',
          name: 'AgentTemplateTwo',
          component: AgentTemplateTwo
        }
      ]
    },
    {
      path: '/result',
      name: 'Result',
      component: Result
    }
  ]
})

export default router
