import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const loading = ref(false)

  async function fetchProjects() {
    loading.value = true
    try {
      const { data } = await api.get('/projects')
      projects.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id) {
    const { data } = await api.get(`/projects/${id}`)
    currentProject.value = data
    return data
  }

  async function createProject(payload) {
    const { data } = await api.post('/projects', payload)
    projects.value.unshift(data)
    return data
  }

  async function updateProject(id, payload) {
    const { data } = await api.put(`/projects/${id}`, payload)
    const idx = projects.value.findIndex(p => p.id === id)
    if (idx >= 0) projects.value[idx] = data
    if (currentProject.value?.id === id) currentProject.value = data
    return data
  }

  async function deleteProject(id) {
    await api.delete(`/projects/${id}`)
    projects.value = projects.value.filter(p => p.id !== id)
    if (currentProject.value?.id === id) currentProject.value = null
  }

  return { projects, currentProject, loading, fetchProjects, fetchProject, createProject, updateProject, deleteProject }
})
