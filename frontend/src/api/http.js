import axios from 'axios'

function getCookie(name) {
  const m = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return m ? decodeURIComponent(m[2]) : ''
}

const http = axios.create({
  baseURL: '',
  withCredentials: true,
})

http.defaults.xsrfCookieName = 'csrftoken'
http.defaults.xsrfHeaderName = 'X-CSRFToken'

http.interceptors.request.use((config) => {
  const t = getCookie('csrftoken')
  if (t) config.headers['X-CSRFToken'] = t
  return config
})

export async function ensureCsrf() {
  await http.get('/api/users/csrf/')
}

export default http
