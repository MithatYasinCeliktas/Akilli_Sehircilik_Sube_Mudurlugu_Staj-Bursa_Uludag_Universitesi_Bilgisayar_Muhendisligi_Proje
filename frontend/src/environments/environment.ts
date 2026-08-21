export const environment = {
  production: false,
  get apiUrl() {
    return typeof window !== 'undefined' 
      ? 'http://' + window.location.hostname + ':8000/api/v1' 
      : 'http://localhost:8000/api/v1';
  },
  tokenKey: 'access_token'
};