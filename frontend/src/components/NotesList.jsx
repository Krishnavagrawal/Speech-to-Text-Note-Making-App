function NotesList({ notes, searchQuery, onSearch, onSelect, onDelete }) {
  const deleteNote = (note) => {
    if (window.confirm(`Are you sure you want to delete "${note.title}"?`)) {
      onDelete(note.id);
    }
  };

  return (
    <section className="notes-dashboard notes-list-card">
      <div className="notes-list-header">
        <div>
          <h3>My Notes</h3>
          <p>Your saved speech-to-text notes.</p>
        </div>
        <input
          className="search-input"
          value={searchQuery}
          onChange={(event) => onSearch(event.target.value)}
          placeholder="Search notes..."
          aria-label="Search notes"
        />
      </div>

      {notes.length ? (
        <div className="notes-list">
          {notes.map((note) => (
            <article className="note-row" key={note.id}>
              <button className="note-select" onClick={() => onSelect(note)}>
                <strong>{note.title}</strong>
                <span>
                  {note.english_transcript.slice(0, 180)}
                  {note.english_transcript.length > 180 ? "..." : ""}
                </span>
                <small>
                  {note.detected_languages} · {new Date(note.created_at).toLocaleDateString()}
                </small>
              </button>
              <div className="note-actions">
                <button className="note-action-button" onClick={() => onSelect(note)}>Open</button>
                <button className="note-action-button" onClick={() => onSelect(note)}>Edit</button>
                <button className="delete-button" onClick={() => deleteNote(note)}>Delete</button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="empty-notes">No notes found.</p>
      )}
    </section>
  );
}

export default NotesList;
