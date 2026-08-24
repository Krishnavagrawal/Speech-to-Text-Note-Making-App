function BottomNav({ currentPage, onHome, onNotes, onRecord, onAI }) {
  if (currentPage === "voice" || currentPage === "editor") return null;

  return (
    <nav className="reference-bottom-nav" aria-label="Primary navigation">
      <button className={currentPage === "home" ? "bottom-item active" : "bottom-item"} onClick={onHome}>
        <span>⌂</span><small>Home</small>
      </button>
      <button className={currentPage === "notes" ? "bottom-item active" : "bottom-item"} onClick={onNotes}>
        <span>▤</span><small>Notes</small>
      </button>
      <button className="main-plus" onClick={onRecord} aria-label="Record voice note">+</button>
      <button className="bottom-item" onClick={onAI}>
        <span>✦</span><small>AI</small>
      </button>
      <button className="bottom-item" type="button">
        <span>⚙</span><small>Settings</small>
      </button>
    </nav>
  );
}

export default BottomNav;
