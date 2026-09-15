import { useEffect, useRef, useState } from "react";

const API_URL = `${window.location.protocol}//${window.location.hostname}:8001`;
const WS_URL = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.hostname}:8001/ws/transcribe`;

function getSupportedAudioMimeType() {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
  ];
  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || "";
}

function VoiceNote({ onBack, onUpload, onComplete }) {
  const [recording, setRecording] = useState(false);
  const [paused, setPaused] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [status, setStatus] = useState("Ready to record");
  const [liveTranscript, setLiveTranscript] = useState("");
  const [detectedLanguages, setDetectedLanguages] = useState([]);
  const [realtimeConnected, setRealtimeConnected] = useState(false);
  const [error, setError] = useState("");
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const socketRef = useRef(null);
  const mimeTypeRef = useRef("");

  useEffect(() => () => {
    socketRef.current?.close();
    streamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  useEffect(() => {
    if (!recording || paused) return undefined;
    const timer = setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, [recording, paused]);

  const formatTime = () => `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;

  const startRecording = async () => {
    try {
      setError("");
      setLiveTranscript("");
      setAudioBlob(null);
      setDetectedLanguages([]);
      setRealtimeConnected(false);

      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("This browser does not support microphone recording.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      const mimeType = getSupportedAudioMimeType();
      mimeTypeRef.current = mimeType;
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType, audioBitsPerSecond: 128000 })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      // The WebSocket is kept for connection/status testing. Final transcription
      // is performed from the complete recording through POST /transcribe.
      try {
        const socket = new WebSocket(WS_URL);
        socket.onopen = () => {
          socketRef.current = socket;
          setRealtimeConnected(true);
        };
        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "status" && data.message === "Audio received") {
              setStatus("Recording...");
            }
          } catch {
            // Ignore non-JSON websocket messages.
          }
        };
        socket.onerror = () => setRealtimeConnected(false);
        socket.onclose = () => {
          setRealtimeConnected(false);
          if (socketRef.current === socket) socketRef.current = null;
        };
      } catch {
        // A websocket failure must not prevent normal POST transcription.
      }

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
          if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(event.data);
          }
        }
      };

      recorder.onstop = () => {
        const finalType = recorder.mimeType || mimeTypeRef.current || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: finalType });
        setAudioBlob(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.onerror = () => {
        setError("The browser could not create the audio recording. Please try again.");
        setStatus("Error");
      };

      recorder.start(1000);
      setSeconds(0);
      setRecording(true);
      setPaused(false);
      setStatus("Recording...");
    } catch (recordingError) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      setError(recordingError.message || "Microphone permission is required.");
      setStatus("Error");
    }
  };

  const stopRecording = () => {
    if (!mediaRecorderRef.current) return;
    const recorder = mediaRecorderRef.current;
    if (recorder.state !== "inactive") recorder.stop();
    socketRef.current?.close();
    setRealtimeConnected(false);
    setRecording(false);
    setPaused(false);
    setStatus("Recording complete");
  };

  const transcribeAudio = async () => {
    if (!audioBlob || audioBlob.size === 0) {
      setError("No audio was recorded. Please record your voice again.");
      return;
    }

    setProcessing(true);
    setStatus("Converting speech to text...");
    setError("");
    const formData = new FormData();
    const extension = audioBlob.type.includes("ogg") ? "ogg" : "webm";
    formData.append("file", audioBlob, `recording.${extension}`);

    try {
      const response = await fetch(`${API_URL}/transcribe`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.success) {
        throw new Error(data.error || data.detail || "Transcription failed.");
      }

      const originalTranscript = data.original_transcription ?? data.originalTranscript ?? data.original_text ?? data.transcription ?? "";
      const englishTranscript = data.english_transcription ?? data.englishTranscript ?? data.english_text ?? data.transcription ?? "";
      const languages = data.detected_languages ?? data.detectedLanguages ?? [data.language].filter(Boolean);
      const transcriptionReport = data.transcription_report ?? null;

      if (!englishTranscript.trim()) {
        throw new Error("The recording was received, but no speech was detected. Please record again and speak clearly for at least 2 seconds.");
      }

      setDetectedLanguages(languages);
      setLiveTranscript(englishTranscript);
      setStatus("English transcript ready");
      onComplete({ originalTranscript, englishTranscript, detectedLanguages: languages, transcriptionReport });
    } catch (transcriptionError) {
      setError(transcriptionError.message || "Could not connect to the backend.");
      setStatus("Error");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <main className="voice-design-page">
      <header className="simple-header"><button className="circle-icon-button" onClick={onBack} aria-label="Back">←</button><span>Voice Note</span><button className="circle-icon-button" type="button" aria-label="Share">↗</button></header>
      <section className="voice-design-content">
        <div className="voice-language">🌐 {detectedLanguages.length ? detectedLanguages.join(" + ") : "Auto Detect"} <span>→</span> English</div>
        <div className="voice-title-area"><span className="small-label">SPEECH TO TEXT</span><h1>Speak naturally.</h1><p>Hindi, English or both.<br />Your English notes will be created automatically.</p><button className="upload-from-voice-button" type="button" onClick={onUpload}>Upload audio instead</button></div>
        <div className="live-transcript"><span>{status}{recording && (realtimeConnected ? " · Connection ready" : " · Final conversion")}</span><p>{liveTranscript || (recording ? "Recording... Speak clearly. The transcript will be created when you stop and convert." : "Press the microphone to start recording.")}</p></div>
        <div className="big-wave">{Array.from({ length: 35 }, (_, index) => <span className={recording ? "wave-bar active" : "wave-bar"} key={index} style={{ height: recording ? `${20 + ((index * 23) % 65)}px` : "8px" }} />)}</div>
        <div className="record-time">{formatTime()}</div>
        {!recording && !audioBlob && !processing && <button className="huge-record-button" onClick={startRecording} aria-label="Start recording">🎙</button>}
        {recording && <div className="voice-controls"><button className="round-control" onClick={() => { if (paused) { mediaRecorderRef.current.resume(); setPaused(false); setStatus("Recording..."); } else { mediaRecorderRef.current.pause(); setPaused(true); setStatus("Paused"); } }}>{paused ? "▶" : "Ⅱ"}</button><button className="huge-record-button recording-button" onClick={stopRecording}>■</button><button className="round-control cancel-control" onClick={onBack}>×</button></div>}
        {audioBlob && !processing && <div className="record-complete"><div><strong>Recording ready</strong><p>{(audioBlob.size / 1024).toFixed(0)} KB · Ready for Whisper</p></div><button className="black-button" onClick={transcribeAudio}>Convert →</button></div>}
        {processing && <div className="ai-processing"><span className="loading-dot" />Converting speech to text...</div>}
        {error && <div className="design-error">{error}</div>}
      </section>
    </main>
  );
}

export default VoiceNote;
