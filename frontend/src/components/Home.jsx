import { useEffect, useState } from "react";

const API_URL = `${window.location.protocol}//${window.location.hostname}:8001`;

function Home({ onVoiceNote, onTextNote, onAINote, onUpload, onNotes, onOpenNote }) {
  const [notes, setNotes] = useState([]);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");

  useEffect(() => {
    fetch(`${API_URL}/notes`)
      .then((response) => (response.ok ? response.json() : []))
      .then(setNotes)
      .catch(() => setNotes([]));
  }, []);

  const filteredNotes = notes.filter((note) => {
    const query = search.trim().toLowerCase();
    const searchableText = [note.title, note.english_transcript, note.original_transcript, note.summary, note.key_points]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const matchesSearch = !query || searchableText.includes(query);
    const matchesFilter = activeFilter === "all"
      || (activeFilter === "important" && Boolean(note.summary || note.key_points))
      || (activeFilter === "lectures" && /lecture|lesson|class|study|course|learning/.test(searchableText));
    return matchesSearch && matchesFilter;
  });

  return (
    <main className="home-screen">
      <header className="home-header">
        <h1 className="big-title">My<br />Notes</h1>
        <button className="dots-button" type="button" aria-label="More options">•<br />•<br />•</button>
      </header>

      <div className="filter-row">
        <button className={activeFilter === "all" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("all")}>All <span>{notes.length}</span></button>
        <button className={activeFilter === "important" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("important")}>Important</button>
        <button className={activeFilter === "lectures" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("lectures")}>Lectures</button>
      </div>

      <div className="minimal-search">
        <span aria-hidden="true">⌕</span>
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search notes..." aria-label="Search notes" />
        <button type="button" onClick={onVoiceNote} aria-label="Record voice">🎙</button>
      </div>

      <section className="note-grid" aria-label="Create note">
        <button className="design-card orange-card" onClick={onVoiceNote}><div className="card-top"><span className="card-icon">🎙</span><span className="heart">♡</span></div><div className="card-bottom"><h2>Voice<br />Notes</h2><p>Record speech and create notes</p></div></button>
        <button className="design-card yellow-card" onClick={onAINote}><div className="card-top"><span className="card-icon">✦</span><span className="heart">♡</span></div><div className="card-bottom"><h2>AI<br />Notes</h2><p>Summarize and organize notes</p></div></button>
        <button className="design-card green-card" onClick={onTextNote}><div className="card-top"><span className="card-icon">Aa</span></div><div className="card-bottom"><h2>Text<br />Note</h2><p>Write your thoughts</p></div></button>
        <button className="design-card upload-card" onClick={onUpload}><div className="card-top"><span className="card-icon">↑</span></div><div className="card-bottom"><h2>Upload<br />Audio</h2><p>Convert a recording into notes</p></div></button>
      </section>

      <section className="recent-area">
        <div className="recent-heading"><div><span className="small-label">YOUR NOTES</span><h2>Recent Notes</h2></div><button className="see-all" type="button" onClick={onNotes}>See all →</button></div>
        <div className="recent-list">
          {filteredNotes.length === 0 ? (
            <div className="empty-design-card"><button type="button" className="empty-circle" onClick={onUpload} aria-label="Upload an audio file">+</button><h3>Start your first note</h3><p>Record a lecture, meeting or idea.</p><div className="empty-note-actions"><button onClick={onVoiceNote} className="black-button">Start Recording</button><button onClick={onUpload} className="upload-empty-button" type="button">Upload Audio</button></div></div>
          ) : filteredNotes.slice(0, 5).map((note) => (
            <button className={`recent-design-card ${note.id % 3 === 0 ? "recent-cream" : note.id % 3 === 1 ? "recent-lime" : "recent-lavender"}`} key={note.id} onClick={() => onOpenNote(note)}>
              <div><span className="note-number">NOTE {note.id}</span><h3>{note.title}</h3><p>{note.english_transcript}</p></div><span className="arrow-circle">↗</span>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}

export default Home;
