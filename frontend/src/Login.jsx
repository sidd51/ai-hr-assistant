import { useState } from 'react';
import styles from './Login.module.css';

const EMPLOYEES = [
  { id: 1, name: 'Alice Johnson',  role: 'Senior Engineer',  dept: 'Engineering' },
  { id: 2, name: 'Bob Smith',      role: 'Marketing Lead',   dept: 'Marketing'   },
  { id: 3, name: 'Carol White',    role: 'HR Manager',       dept: 'HR'          },
  { id: 4, name: 'David Lee',      role: 'Junior Engineer',  dept: 'Engineering' },
  { id: 5, name: 'Eva Brown',      role: 'Finance Analyst',  dept: 'Finance'     },
];

export default function Login({ onLogin }) {
  const [selected, setSelected] = useState(null);

  return (
    <div className={styles.wrap}>
      <div className={styles.panel}>

        <div className={styles.brand}>
          <div>
            <div className={styles.brandName}>HarborHR</div>
            <div className={styles.brandSub}>a safe port for all your HR needs</div>
          </div>
        </div>

        <div className={styles.divider} />

        <p className={styles.prompt}>Select your profile to continue</p>

        <div className={styles.list}>
          {EMPLOYEES.map(emp => (
            <button
              key={emp.id}
              className={`${styles.card} ${selected?.id === emp.id ? styles.active : ''}`}
              onClick={() => setSelected(emp)}
            >
              <div className={styles.avatar}>
                {emp.name.split(' ').map(n => n[0]).join('')}
              </div>
              <div className={styles.info}>
                <span className={styles.name}>{emp.name}</span>
                <span className={styles.meta}>{emp.role} · {emp.dept}</span>
              </div>
              {selected?.id === emp.id && (
                <span className={styles.check}>✓</span>
              )}
            </button>
          ))}
        </div>

        <button
          className={styles.enter}
          disabled={!selected}
          onClick={() => selected && onLogin(selected)}
        >
          Enter Portal
        </button>

      </div>

      <div className={styles.bg} aria-hidden />
    </div>
  );
}