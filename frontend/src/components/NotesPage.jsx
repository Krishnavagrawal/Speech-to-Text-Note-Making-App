import { useEffect, useState } from "react";
import { jsPDF } from "jspdf";

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
      const token = localStorage.getItem("smartNotesAuthToken");
      const params = new URLSearchParams({ favorite: String(activeFilter === "favorite"), sort });
      if (category !== "all") params.set("category", category);
      const response = await fetch(`${API_URL}/notes?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Could not load notes.");
      setNotes(await response.json());
    } catch (loadError) { setError(loadError.message); }
  };

  useEffect(() => { loadNotes(); }, [activeFilter, category, sort]);

  const toggleFavorite = async (note) => {
    const token = localStorage.getItem("smartNotesAuthToken");
    await fetch(`${API_URL}/notes/${note.id}`, { method: "PUT", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ is_favorite: !note.is_favorite }) });
    loadNotes();
  };

  const deleteNote = async (id) => {
    if (!window.confirm("Delete this note?")) return;
    try {
      const token = localStorage.getItem("smartNotesAuthToken");
      const response = await fetch(`${API_URL}/notes/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error("Could not delete note.");
      loadNotes();
    } catch (deleteError) { setError(deleteError.message); }
  };

  const downloadPdf = (note) => {
    const pdf = new jsPDF();
    const margin = 18;
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    let y = 22;
    const addText = (value, size, color, gap) => {
      pdf.setFontSize(size);
      pdf.setTextColor(...color);
      pdf.splitTextToSize(String(value || ""), pageWidth - margin * 2).forEach((line) => {
        if (y > pageHeight - margin) { pdf.addPage(); y = margin; }
        pdf.text(line, margin, y);
        y += gap;
      });
      y += 4;
    };

    addText(note.title || "Smart Notes", 22, [17, 17, 17], 9);
    addText(`${note.category || "General"} | ${new Date(note.created_at).toLocaleDateString()}`, 10, [100, 96, 88], 6);
    addText("Note", 14, [17, 17, 17], 7);
    addText(note.english_transcript, 11, [45, 45, 45], 6);
    if (note.summary) { addText("AI Summary", 14, [17, 17, 17], 7); addText(note.summary, 11, [45, 45, 45], 6); }
    if (note.key_points) { addText("Key Points", 14, [17, 17, 17], 7); addText(note.key_points, 11, [45, 45, 45], 6); }
    if (note.tag) addText(`Tag: ${note.tag}`, 10, [100, 96, 88], 6);

    const fileName = `${(note.title || "smart-note").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "") || "smart-note"}.pdf`;
    pdf.save(fileName);
  };

  const query = search.trim().toLowerCase();
  const filteredNotes = notes.filter((note) => {
    const title = (note.title || "").toLowerCase();
    const searchableText = [note.title, note.english_transcript, note.original_transcript, note.summary, note.key_points]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const matchesSearch = !query || title.includes(query) || searchableText.includes(query);
    const matchesFilter = activeFilter === "all"
      || (activeFilter === "important" && Boolean(note.summary || note.key_points))
      || (activeFilter === "todo" && /todo|to-do|action|follow up/.test(searchableText));
    return matchesSearch && matchesFilter;
  });

  return (
    <main className="notes-design-page">
      <header className="notes-big-header"><button className="circle-icon-button" onClick={onBack} aria-label="Back">←</button><h1>My<br />Notes</h1><button className="circle-icon-button" type="button" aria-label="More options">⋮</button></header>
      <div className="notes-content">
        <div className="filter-row"><button className={activeFilter === "all" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("all")}>All</button><button className={activeFilter === "favorite" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("favorite")}>Favorites</button><button className={activeFilter === "todo" ? "filter active" : "filter"} type="button" onClick={() => setActiveFilter("todo")}>To-do</button><label className="filter-select-wrap"><span className="sr-only">Category</span><select className="filter-select" value={category} onChange={(event) => setCategory(event.target.value)}><option value="all">All categories</option><option>Lecture</option><option>College</option><option>Meeting</option><option>Project</option><option>Personal</option></select></label><label className="filter-select-wrap"><span className="sr-only">Sort notes</span><select className="filter-select" value={sort} onChange={(event) => setSort(event.target.value)}><option value="newest">Newest</option><option value="updated">Recently updated</option><option value="oldest">Oldest</option><option value="title">Title A-Z</option></select></label></div>
        <div className="minimal-search notes-search"><span aria-hidden="true">⌕</span><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search notes by title..." aria-label="Search notes by title or content" /></div>
        {search.trim() && <p className="search-result-count notes-result-count" aria-live="polite">{filteredNotes.length} {filteredNotes.length === 1 ? "note" : "notes"} found</p>}
        <section className="notes-card-list">
        {filteredNotes.length === 0 ? <div className="empty-design-card"><div className="empty-circle">+</div><h3>No notes yet</h3><p>Your saved notes will appear here.</p></div> : filteredNotes.map((note, index) => <article className={`large-note-card ${["note-yellow", "note-orange", "note-green", "note-blue"][index % 4]}`} key={note.id}><div className="large-note-top"><span className="note-count">{String(index + 1).padStart(2, "0")}</span><div><button className="heart-button" type="button" onClick={() => toggleFavorite(note)} aria-label={note.is_favorite ? "Remove favorite" : "Add favorite"}>{note.is_favorite ? "♥" : "♡"}</button><button className="heart-button" onClick={() => deleteNote(note.id)} aria-label={`Delete ${note.title}`}>⋮</button></div></div><button className="note-open-area" onClick={() => onOpenNote(note)}><span className="note-category">{note.category || note.detected_languages || "English"}</span><h2>{note.title}</h2><p>{note.english_transcript}</p></button><div className="large-note-footer"><span>{new Date(note.created_at).toLocaleDateString()}</span><div className="note-footer-actions"><button type="button" className="download-note-button" onClick={() => downloadPdf(note)} aria-label={`Download ${note.title} as PDF`}>↓ PDF</button><button type="button" className="open-note-button" onClick={() => onOpenNote(note)}>Open ↗</button></div></div></article>)}
        </section>
        {error && <div className="error-box">{error}</div>}
      </div>
    </main>
  );
}

export default NotesPage;
