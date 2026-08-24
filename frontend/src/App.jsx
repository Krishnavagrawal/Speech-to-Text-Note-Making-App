import { useState } from "react";
import Home from "./components/Home";
import VoiceNote from "./components/VoiceNote";
import NoteEditor from "./components/NoteEditor";
import NotesPage from "./components/NotesPage";
import BottomNav from "./components/BottomNav";
import UploadAudio from "./components/UploadAudio";
import "./App.css";

const emptyNote = { title: "", originalTranscript: "", englishTranscript: "", detectedLanguages: [], tag: "", category: "General", isFavorite: false };

function App() {
  const [page, setPage] = useState("home");
  const [noteData, setNoteData] = useState(emptyNote);

  const openTextNote = () => { setNoteData(emptyNote); setPage("editor"); };
  const openAINote = () => { setNoteData(emptyNote); setPage("editor"); };
  const openUpload = () => setPage("upload");
  const handleTranscriptionComplete = (data) => { setNoteData({ ...emptyNote, ...data }); setPage("editor"); };
  const openExistingNote = (note) => {
    setNoteData({ id: note.id, title: note.title, originalTranscript: note.original_transcript, englishTranscript: note.english_transcript, detectedLanguages: note.detected_languages.split(",").filter(Boolean), summary: note.summary || "", keyPoints: note.key_points || "", tag: note.tag || "", category: note.category || "General", isFavorite: note.is_favorite || false });
    setPage("editor");
  };

  return (
    <div className="app-shell">
      {page === "home" && <Home onVoiceNote={() => setPage("voice")} onTextNote={openTextNote} onAINote={openAINote} onUpload={openUpload} onNotes={() => setPage("notes")} onOpenNote={openExistingNote} />}
      {page === "voice" && <VoiceNote onBack={() => setPage("home")} onUpload={openUpload} onComplete={handleTranscriptionComplete} />}
      {page === "upload" && <UploadAudio onBack={() => setPage("home")} onComplete={handleTranscriptionComplete} />}
      {page === "editor" && <NoteEditor noteData={noteData} onBack={() => setPage("home")} onSaved={() => setPage("notes")} />}
      {page === "notes" && <NotesPage onBack={() => setPage("home")} onOpenNote={openExistingNote} />}
      <BottomNav currentPage={page} onHome={() => setPage("home")} onNotes={() => setPage("notes")} onRecord={() => setPage("voice")} onAI={openAINote} />
    </div>
  );
}

export default App;
