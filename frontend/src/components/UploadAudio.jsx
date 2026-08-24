import { useRef, useState } from "react";

const API_URL = `${window.location.protocol}//${window.location.hostname}:8001`;

function UploadAudio({ onBack, onComplete }) {
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState("");
  const [languageMode, setLanguageMode] = useState("auto");

  const handleFileSelect = (event) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;
    setError("");
    setFile(selectedFile);
  };

  const uploadAudio = async () => {
    if (!file) {
      setError("Please select an audio file.");
      return;
    }

    setProcessing(true);
    setError("");
    setProgress("Uploading audio...");
    const formData = new FormData();
    formData.append("file", file);

    try {
      setProgress(languageMode === "hindi" ? "Recognizing Hindi speech..." : "Converting speech to text...");
      const endpoint = languageMode === "hindi" ? "/transcribe-hindi" : "/transcribe";
      const response = await fetch(`${API_URL}${endpoint}`, { method: "POST", body: formData });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || data.detail || "Transcription failed.");
      setProgress("Creating your note...");
      const originalTranscript = data.original_transcription ?? data.originalTranscript ?? data.original_text ?? data.transcription ?? "";
      const englishTranscript = data.english_transcription ?? data.englishTranscript ?? data.english_text ?? data.transcription ?? "";
      const detectedLanguages = data.detected_languages ?? data.detectedLanguages ?? [data.language].filter(Boolean);
      onComplete({
        title: data.title || file.name.replace(/\.[^/.]+$/, ""),
        originalTranscript,
        englishTranscript,
        detectedLanguages,
      });
    } catch (uploadError) {
      setError(uploadError.message || "Could not process the audio.");
    } finally {
      setProcessing(false);
      setProgress("");
    }
  };

  return (
    <main className="upload-design-page">
      <header className="simple-header"><button className="circle-icon-button" onClick={onBack} aria-label="Back">←</button><span>Upload Recording</span><div /></header>
      <section className="upload-content">
        <span className="small-label">AUDIO TO NOTES</span>
        <h1>Turn a recording<br />into a note.</h1>
        <p className="upload-description">Choose a recording from your phone or computer. Hindi, English, or mixed speech is supported.</p>
        <label className="upload-language-label" htmlFor="upload-language">Input language</label>
        <select id="upload-language" className="upload-language-select" value={languageMode} onChange={(event) => setLanguageMode(event.target.value)}>
          <option value="auto">Auto Detect</option>
          <option value="english">English</option>
          <option value="hindi">Hindi</option>
        </select>
        <input ref={fileInputRef} type="file" accept="audio/*,.mp3,.wav,.m4a,.webm,.ogg,.aac" onChange={handleFileSelect} hidden />
        {!file && <button className="upload-drop-card" onClick={() => fileInputRef.current?.click()}><div className="upload-icon">↑</div><h2>Choose audio file</h2><p>From your phone or laptop</p><span>MP3 · WAV · M4A · WEBM · OGG</span></button>}
        {file && <div className="selected-file-card"><div className="selected-file-icon">🎵</div><div className="selected-file-info"><strong>{file.name}</strong><span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span></div><button className="remove-file" onClick={() => setFile(null)} aria-label="Remove selected file">×</button></div>}
        {file && !processing && <button className="process-upload-button" onClick={uploadAudio}>Convert to Notes →</button>}
        {processing && <div className="upload-processing"><div className="loading-dot" /><span>{progress}</span></div>}
        {error && <div className="design-error">{error}</div>}
        <div className="upload-info-grid"><div><strong>🌐 Languages</strong><p>Hindi + English</p></div><div><strong>✦ AI Notes</strong><p>Summary &amp; key points</p></div></div>
      </section>
    </main>
  );
}

export default UploadAudio;
