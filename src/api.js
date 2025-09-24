export const API = process.env.REACT_APP_API_URL;

export const authHeaders = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`,
});


