import { useEffect, useState } from "react";

const API_URL = `${window.location.protocol}//${window.location.hostname}:8001`;

function NoteEditor({ noteData, onBack, onSaved }) {
  const [title, setTitle] = useState(noteData.title || "");
  const [englishText, setEnglishText] = useState(noteData.englishTranscript || "");
  const [originalText, setOriginalText] = useState(noteData.originalTranscript || "");
  const [tag, setTag] = useState(noteData.tag || "");
  const [category, setCategory] = useState(noteData.category || "General");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState(noteData.summary || "");
  const [keyPoints, setKeyPoints] = useState(noteData.keyPoints || "");
  const [bullets, setBullets] = useState("");
  const [aiResult, setAiResult] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiAction, setAiAction] = useState("");

  useEffect(() => {
    setTitle(noteData.title || "");
    setEnglishText(noteData.englishTranscript || "");
    setOriginalText(noteData.originalTranscript || "");
    setSummary(noteData.summary || "");
    setKeyPoints(noteData.keyPoints || "");
    setBullets(noteData.bullets || "");
    setTag(noteData.tag || "");
    setCategory(noteData.category || "General");
    setAiResult("");
  }, [noteData]);
  const transcriptionReport = noteData.transcriptionReport || null;
  const saveNote = async () => {
    if (!title.trim()) { setError("Please enter a title."); return; }
    if (!englishText.trim()) { setError("There is no English text to save."); return; }
    setSaving(true); setError("");
    try {
      const token = localStorage.getItem("smartNotesAuthToken");
      const response = await fetch(`${API_URL}/notes${noteData.id ? `/${noteData.id}` : ""}`, {
        method: noteData.id ? "PUT" : "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ title: title.trim(), original_transcript: originalText || "No original transcript", english_transcript: englishText, detected_languages: noteData.detectedLanguages.join(",") || "en", summary, key_points: Array.isArray(keyPoints) ? keyPoints.join("\n") : keyPoints, tag: tag.trim(), category, is_favorite: Boolean(noteData.isFavorite) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not save note.");
      onSaved(data);
    } catch (saveError) { setError(saveError.message); } finally { setSaving(false); }
  };

  const runAI = async (action) => {
    if (!englishText.trim()) { setError("There is no text for the AI to process."); return; }
    const endpoints = { summarize: "/ai/summarize", clean: "/ai/clean", keypoints: "/ai/key-points", title: "/ai/title", bullets: "/ai/bullets" };
    setAiLoading(true); setAiAction(action); setAiResult(""); setError("");
    try {
      const token = localStorage.getItem("smartNotesAuthToken");
      const response = await fetch(`${API_URL}${endpoints[action]}`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ text: englishText }) });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || "AI request failed.");
      setAiResult(data.result);
      if (action === "clean") setEnglishText(data.result);
      if (action === "title") setTitle(data.result);
      if (action === "summarize") setSummary(data.result);
      if (action === "keypoints") setKeyPoints(data.result);
      if (action === "bullets") setBullets(data.result);
    } catch (aiError) { setError(aiError.message || "AI service unavailable. Start Ollama and try again."); }
    finally { setAiLoading(false); setAiAction(""); }
  };

  const generateCompleteNote = async () => {
    if (!englishText.trim()) { setError("There is no text for the AI to process."); return; }
    setAiLoading(true); setAiAction("complete"); setAiResult(""); setError("");
    try {
      const token = localStorage.getItem("smartNotesAuthToken");
      const response = await fetch(`${API_URL}/ai/process-note`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ text: englishText }) });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || data.message || "AI request failed.");
      const result = data.data;
      setTitle(result.title || title);
      setSummary(result.summary || "");
      setKeyPoints(Array.isArray(result.key_points) ? result.key_points.join("\n") : result.key_points || "");
      setBullets(result.bullets || "");
      setAiResult("Complete AI note generated.");
    } catch (aiError) { setError(aiError.message || "AI service unavailable."); }
    finally { setAiLoading(false); setAiAction(""); }
  };

  return (
    <main className="editor-design-page">
      <header className="simple-header"><button className="circle-icon-button" onClick={onBack} aria-label="Back">←</button><span>{noteData.id ? "Edit Note" : "Create Note"}</span><button className="circle-icon-button" onClick={saveNote} disabled={saving} aria-label="Save note">↗</button></header>
      <section className="editor-design-content">
        <input className="big-note-title" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Give your note a title..." />
        <div className="note-info-row"><span>🌐 {noteData.detectedLanguages.length ? noteData.detectedLanguages.join(" + ") : "Auto"}</span><span>→</span><span>English</span></div>
        {transcriptionReport && <section className="transcription-report-card">
          <div className="transcription-report-head"><span className="small-label">TRANSCRIPTION REPORT</span><span className="report-score">{transcriptionReport.accuracy_percent ?? 0}%</span></div>
          <div className="report-stats">
            <span><strong>Accuracy</strong><small>{transcriptionReport.accuracy_percent ?? 0}%</small></span>
            <span><strong>Confidence</strong><small>{transcriptionReport.confidence_score ?? 0}</small></span>
            <span><strong>Words</strong><small>{transcriptionReport.word_count ?? 0}</small></span>
            <span><strong>Segments</strong><small>{transcriptionReport.segments_processed ?? 0}</small></span>
          </div>
        </section>}
        <div className="paper-editor"><div className="editor-toolbar"><button type="button">Aa</button><button type="button">○</button><button type="button">≡</button><span>16</span></div><textarea value={englishText} onChange={(event) => setEnglishText(event.target.value)} placeholder="Write your notes..." /></div>
        <details className="original-dropdown"><summary>Original Transcript</summary><textarea value={originalText} onChange={(event) => setOriginalText(event.target.value)} /></details>
        <div className="editor-tags"><label className="editor-tag">🏷 <input value={tag} onChange={(event) => setTag(event.target.value)} placeholder="Add tag" /></label><select value={category} onChange={(event) => setCategory(event.target.value)} className="editor-tag"><option>General</option><option>Lecture</option><option>College</option><option>Meeting</option><option>Project</option><option>Personal</option></select></div>
        <section className="ai-design-section"><div className="section-title-line"><div><span className="small-label">AI ASSIST</span><h2>Make your note smarter.</h2></div><span className="sparkle">✦</span></div><div className="ai-design-grid"><button onClick={() => runAI("summarize")} disabled={aiLoading}><span className="ai-big-icon">{aiLoading && aiAction === "summarize" ? "..." : "✨"}</span><strong>Summarize</strong><small>Get the main ideas</small></button><button onClick={() => runAI("clean")} disabled={aiLoading}><span className="ai-big-icon">{aiLoading && aiAction === "clean" ? "..." : "🧹"}</span><strong>Rewrite Clearly</strong><small>Improve clarity</small></button><button onClick={() => runAI("keypoints")} disabled={aiLoading}><span className="ai-big-icon">{aiLoading && aiAction === "keypoints" ? "..." : "📌"}</span><strong>Key Points</strong><small>Extract important ideas</small></button><button onClick={() => runAI("bullets")} disabled={aiLoading}><span className="ai-big-icon">{aiLoading && aiAction === "bullets" ? "..." : "•"}</span><strong>Convert to Bullets</strong><small>Structure the note</small></button><button onClick={() => runAI("title")} disabled={aiLoading}><span className="ai-big-icon">{aiLoading && aiAction === "title" ? "..." : "Aa"}</span><strong>Generate Title</strong><small>Find the perfect title</small></button><button onClick={generateCompleteNote} disabled={aiLoading}><span className="ai-big-icon">{aiLoading && aiAction === "complete" ? "..." : "✦"}</span><strong>Complete AI Note</strong><small>Generate everything</small></button></div>
          {aiLoading && <div className="ai-loading"><span className="loading-dot" />AI is working on your note...</div>}
          {aiResult && <div className="ai-result-design"><div className="ai-result-top"><strong>✦ AI Result</strong><button type="button" onClick={() => setAiResult("")}>×</button></div><p>{aiResult}</p></div>}
          {summary && <div className="saved-ai-card"><span>✨ AI Summary</span><p>{summary}</p></div>}
          {keyPoints && <div className="saved-ai-card"><span>📌 Key Points</span><p>{keyPoints}</p></div>}
          {bullets && <div className="saved-ai-card"><span>• Bullets</span><p>{bullets}</p></div>}
        </section>
        {error && <div className="error-box">{error}</div>}
        <button className="save-design-button" onClick={saveNote} disabled={saving}>{saving ? "Saving..." : noteData.id ? "Update Note" : "Save Note"}</button>
      </section>
    </main>
  );
}

export default NoteEditor;
