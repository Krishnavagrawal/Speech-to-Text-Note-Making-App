import { useEffect, useState } from "react";

const API_URL = `${window.location.protocol}//${window.location.hostname}:8001`;

function NotesPage({ onBack, onOpenNote }) {
  const [notes, setNotes] = useState([]);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [category, setCategory] = useState("all");
  const [sort, setSort] = useState("newest");
  const [error, setError] = useState("");

  const loadNotes = async () => {
    try {
      const params = new URLSearchParams({ favorite: String(activeFilter === "favorite"), sort });
      if (category !== "all") params.set("category", category);
      const response = await fetch(`${API_URL}/notes?${params}`);
      if (!response.ok) throw new Error("Could not load notes.");
      setNotes(await response.json());
    } catch (loadError) { setError(loadError.message); }
  };

  useEffect(() => { loadNotes(); }, [activeFilter, category, sort]);

  const toggleFavorite = async (note) => {
    await fetch(`${API_URL}/notes/${note.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_favorite: !note.is_favorite }) });
    loadNotes();
  };

  const deleteNote = async (id) => {
    if (!window.confirm("Delete this note?")) return;
    try {
      const response = await fetch(`${API_URL}/notes/${id}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Could not delete note.");
      loadNotes();
    } catch (deleteError) { setError(deleteError.message); }
  };

  const query = search.trim().toLowerCase();
  const filteredNotes = notes.filter((note) => {
    const searchableText = [note.title, note.english_transcript, note.original_transcript, note.summary, note.key_points]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const matchesSearch = !query || searchableText.includes(query);
    const matchesFilter = activeFilter === "all"
      || (activeFilter === "important" && Boolean(note.summary || note.key_points))
      || (activeFilter === "todo" && /todo|to-do|action|follow up/.test(searchableText));
    return matchesSearch && matchesFilter;
  });

  return (
    <main className="notes-design-page">
      <header className="notes-big-header"><button className="circle-icon-button" onClick={onBack} aria-label="Back">←</button><h1>My<br />Notes</h1><button className="circle-icon-button" type="button" aria-label="More options">⋮</button></header>
      <div className="notes-content">
        <div className="filter-row"><button className={activeFilter === "all" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("all")}>All</button><button className={activeFilter === "favorite" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("favorite")}>Favorites</button><button className={activeFilter === "todo" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("todo")}>To-do</button><select className="filter-select" value={category} onChange={(event) => setCategory(event.target.value)}><option value="all">All categories</option><option>Lecture</option><option>College</option><option>Meeting</option><option>Project</option><option>Personal</option></select><select className="filter-select" value={sort} onChange={(event) => setSort(event.target.value)}><option value="newest">Newest</option><option value="updated">Recently updated</option><option value="oldest">Oldest</option><option value="title">Title A-Z</option></select></div>
        <div className="minimal-search notes-search"><span aria-hidden="true">⌕</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search notes..." aria-label="Search your notes" /></div>
        <section className="notes-card-list">
        {filteredNotes.length === 0 ? <div className="empty-design-card"><div className="empty-circle">+</div><h3>No notes yet</h3><p>Your saved notes will appear here.</p></div> : filteredNotes.map((note, index) => <article className={`large-note-card ${["note-yellow", "note-orange", "note-green", "note-blue"][index % 4]}`} key={note.id}><div className="large-note-top"><span className="note-count">{String(index + 1).padStart(2, "0")}</span><div><button className="heart-button" type="button" onClick={() => toggleFavorite(note)} aria-label={note.is_favorite ? "Remove favorite" : "Add favorite"}>{note.is_favorite ? "♥" : "♡"}</button><button className="heart-button" onClick={() => deleteNote(note.id)} aria-label={`Delete ${note.title}`}>⋮</button></div></div><button className="note-open-area" onClick={() => onOpenNote(note)}><span className="note-category">{note.category || note.detected_languages || "English"}</span><h2>{note.title}</h2><p>{note.english_transcript}</p></button><div className="large-note-footer"><span>{new Date(note.created_at).toLocaleDateString()}</span><span>Open ↗</span></div></article>)}
        </section>
        {error && <div className="error-box">{error}</div>}
      </div>
    </main>
  );
}

export default NotesPage;
