import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const loading = ref(false)

  async function fetchTasks(projectId) {
    loading.value = true
    try {
      const { data } = await api.get(`/tasks/${projectId}`)
      tasks.value = data
    } finally {
      loading.value = false
    }
  }

  async function createTask(payload) {
    const { data } = await api.post('/tasks', payload)
    tasks.value.push(data)
    return data
  }

  async function updateTask(taskId, payload) {
    const { data } = await api.put(`/tasks/${taskId}`, payload)
    const idx = tasks.value.findIndex(t => t.id === taskId)
    if (idx >= 0) tasks.value[idx] = data
    return data
  }

  async function deleteTask(taskId) {
    await api.delete(`/tasks/${taskId}`)
    tasks.value = tasks.value.filter(t => t.id !== taskId)
  }

  return { tasks, loading, fetchTasks, createTask, updateTask, deleteTask }
})
