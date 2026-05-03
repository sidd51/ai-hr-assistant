import styles from './Message.module.css';

export default function Message({ role, content, isLoading }) {
  const isUser = role === 'user';

  if (isLoading) {
    return (
      <div className={`${styles.row} ${styles.bot}`}>
        <div className={styles.iconBot}>HR</div>
        <div className={`${styles.bubble} ${styles.bubbleBot}`}>
          <span className={styles.dot} />
          <span className={styles.dot} />
          <span className={styles.dot} />
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.row} ${isUser ? styles.user : styles.bot}`}>
      {!isUser && <div className={styles.iconBot}>HR</div>}
      <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleBot}`}>
        {content.split('\n').map((line, i) => (
          <span key={i}>
            {line}
            {i < content.split('\n').length - 1 && <br />}
          </span>
        ))}
      </div>
      {isUser && <div className={styles.iconUser}>ME</div>}
    </div>
  );
}