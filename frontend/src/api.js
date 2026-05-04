// Automatically uses Railway in production, localhost in dev
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function sendMessage({ message, session_id, employee_id}){
  const res = await fetch(`${BASE}/chat`,{
    method :"POST",
    headers: { 'Content-Type': 'application/json'},
    body : JSON.stringify({message, session_id, employee_id}),

  });
  if(!res.ok){
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Server error');
  }
  return res.json(); // { response, session_id }
}
export async function resetSession(session_id) {
  const res = await fetch(`${BASE}/reset-session?session_id=${session_id}`, {
    method: 'POST',
  });
  return res.json(); // { session_id }
}
 
export async function healthCheck() {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}