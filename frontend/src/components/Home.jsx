import { useEffect, useRef, useState } from "react";

const API_URL = `${window.location.protocol}//${window.location.hostname}:8001`;

function Home({ onVoiceNote, onTextNote, onAINote, onUpload, onNotes, onOpenNote, onLogout }) {
  const [notes, setNotes] = useState([]);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [showSettings, setShowSettings] = useState(false);
  const [showMore, setShowMore] = useState(false);
  const [loadingNotes, setLoadingNotes] = useState(false);
  const searchInputRef = useRef(null);
  const user = JSON.parse(localStorage.getItem("smartNotesUser") || "null");

  const loadNotes = () => {
    const token = localStorage.getItem("smartNotesAuthToken");
    setLoadingNotes(true);
    fetch(`${API_URL}/notes`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((response) => (response.ok ? response.json() : []))
      .then(setNotes)
      .catch(() => setNotes([]))
      .finally(() => setLoadingNotes(false));
  };

  useEffect(() => { loadNotes(); }, []);

  const filteredNotes = notes.filter((note) => {
    const query = search.trim().toLowerCase();
    const matchesTitle = (note.title || "").toLowerCase().includes(query);
    const searchableText = [note.title, note.english_transcript, note.original_transcript, note.summary, note.key_points]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const matchesSearch = !query || matchesTitle || searchableText.includes(query);
    const matchesFilter = activeFilter === "all"
      || (activeFilter === "important" && Boolean(note.summary || note.key_points))
      || (activeFilter === "lectures" && /lecture|lesson|class|study|course|learning/.test(searchableText));
    return matchesSearch && matchesFilter;
  });

  const openSearchResult = () => {
    const query = search.trim().toLowerCase();
    if (!query) {
      searchInputRef.current?.focus();
      return;
    }
    const exactTitleMatch = notes.find((note) => (note.title || "").trim().toLowerCase() === query);
    const partialMatch = notes.find((note) => (note.title || "").toLowerCase().includes(query))
      || filteredNotes[0];
    const match = exactTitleMatch || partialMatch;
    if (match) onOpenNote(match);
  };

  return (
    <main className="home-screen">
      <header className="home-header">
        <h1 className="big-title">My Notes</h1>
        <div className="header-actions">
          <button className="settings-button" type="button" onClick={() => setShowSettings((visible) => !visible)} aria-label="Open account settings">⚙</button>
          <button className="dots-button" type="button" onClick={() => setShowMore((visible) => !visible)} aria-label="More options" aria-expanded={showMore}>•<br />•<br />•</button>
        </div>
        {showSettings && (
          <aside className="settings-panel" aria-label="Account settings">
            <span className="small-label">ACCOUNT</span>
            <h2>{user?.name || "Smart Notes user"}</h2>
            <p>{user?.email || "No email available"}</p>
            <button className="text-button secondary" type="button" onClick={onLogout}>Log out</button>
          </aside>
        )}
        {showMore && (
          <div className="more-menu" role="menu" aria-label="More options">
            <button type="button" role="menuitem" onClick={() => { loadNotes(); setShowMore(false); }}>{loadingNotes ? "Refreshing..." : "Refresh notes"}</button>
            <button type="button" role="menuitem" onClick={() => { onNotes(); setShowMore(false); }}>View all notes</button>
            <button type="button" role="menuitem" onClick={() => { onLogout(); setShowMore(false); }}>Log out</button>
          </div>
        )}
      </header>

      <div className="filter-row">
        <button className={activeFilter === "all" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("all")}>All <span>{notes.length}</span></button>
        <button className={activeFilter === "important" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("important")}>Important</button>
        <button className={activeFilter === "lectures" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("lectures")}>Lectures</button>
      </div>

      <div className="minimal-search">
        <span aria-hidden="true">⌕</span>
        <input ref={searchInputRef} type="search" value={search} onChange={(event) => setSearch(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); openSearchResult(); } }} placeholder="Search notes by title..." aria-label="Search notes by title or content" />
        <button type="button" onClick={openSearchResult} aria-label="Search notes">⌕</button>
      </div>

      <section className="note-grid" aria-label="Create note">
        <button className="design-card orange-card" onClick={onVoiceNote}><div className="card-top"><span className="card-icon">🎙</span><span className="heart">♡</span></div><div className="card-bottom"><h2>Voice<br />Notes</h2><p>Record speech and create notes</p></div></button>
        <button className="design-card yellow-card" onClick={onAINote}><div className="card-top"><span className="card-icon">✦</span><span className="heart">♡</span></div><div className="card-bottom"><h2>AI<br />Notes</h2><p>Summarize and organize notes</p></div></button>
        <button className="design-card green-card" onClick={onTextNote}><div className="card-top"><span className="card-icon">Aa</span></div><div className="card-bottom"><h2>Text<br />Note</h2><p>Write your thoughts</p></div></button>
        <button className="design-card upload-card" onClick={onUpload}><div className="card-top"><span className="card-icon">↑</span></div><div className="card-bottom"><h2>Upload<br />Audio</h2><p>Convert a recording into notes</p></div></button>
      </section>

      <section className="recent-area">
        {search.trim() && <p className="search-result-count" aria-live="polite">{filteredNotes.length} {filteredNotes.length === 1 ? "note" : "notes"} found</p>}
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
