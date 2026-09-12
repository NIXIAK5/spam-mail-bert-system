import request from '@/utils/request'

export function updateProfile(data) {
  return request.put('/users/profile', data)
}

export function changePassword(data) {
  return request.put('/users/password', data)
}

export function getUsers(params) {
  return request.get('/admin/users', { params })
}

export function updateUser(userId, data) {
  return request.put(`/admin/users/${userId}`, data)
}

export function deleteUser(userId) {
  return request.delete(`/admin/users/${userId}`)
}
