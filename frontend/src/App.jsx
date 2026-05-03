import { useState } from 'react';
import Login from './Login';
import Chat  from './Chat';
import './index.css';
 
export default function App() {
  const [employee, setEmployee] = useState(null);
 
  if (!employee) {
    return <Login onLogin={setEmployee} />;
  }
 
  return <Chat employee={employee} onLogout={() => setEmployee(null)} />;
}
 
