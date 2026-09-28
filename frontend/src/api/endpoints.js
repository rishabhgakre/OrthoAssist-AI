import api from './client'

// ---- Auth ----
export const signup = (data) => api.post('/auth/signup', data)

export const login = (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}

export const getMe = () => api.get('/auth/me')

// ---- Patients ----
export const createPatient = (data) => api.post('/patients/', data)
export const listPatients = () => api.get('/patients/')
export const getPatient = (id) => api.get(`/patients/${id}`)

// ---- Structural AI (X-ray) ----
export const analyzeXray = (formData, onUploadProgress) =>
  api.post('/xray/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  })
export const listXrayRecords = (patientId) => api.get(`/xray/patient/${patientId}`)

// ---- Functional AI (Gait) ----
export const analyzeGait = (formData, onUploadProgress) =>
  api.post('/gait/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  })
export const listGaitRecords = (patientId) => api.get(`/gait/patient/${patientId}`)

// ---- CORI ----
export const computeCori = (data) => api.post('/cori/compute', data)
export const listCoriRecords = (patientId) => api.get(`/cori/patient/${patientId}`)
export const explainCori = (coriId) => api.get(`/cori/${coriId}/explain`)

// ---- Reports ----
export const generateReport = (coriId) => api.post(`/reports/${coriId}/generate`)
export const downloadReport = (coriId) =>
  api.get(`/reports/${coriId}/download`, { responseType: 'blob' })
