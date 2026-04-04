// ── BACKEND URL ──
const BACKEND_WS_URL = "wss://jarvis-claude.onrender.com/ws";

// ── WEBSOCKET ──
let ws = null;
let wsConnected = false;
let audioContext = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

// ── SILENCE DETECTION VARIABLES ──
let silenceTimeout = null;
let volumeCheckInterval = null;

function connectWebSocket() {
  ws = new WebSocket(BACKEND_WS_URL);

  ws.onopen = () => {
    wsConnected = true;
    $("#connection-status").text("Connected").css("color", "#00ff88");
    console.log("WebSocket connected");

    // keepalive ping every 20 seconds to prevent Render timeout
    setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 20000);
  };

  ws.onclose = () => {
    wsConnected = false;
    $("#connection-status").text("Disconnected — retrying...").css("color", "#ff4444");
    setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = (err) => {
    console.error("WebSocket error:", err);
    $("#connection-status").text("Connection error").css("color", "#ff4444");
  };

  ws.onmessage = async (event) => {
    // audio bytes — play directly
    if (event.data instanceof Blob) {
      await playAudioResponse(event.data);
      return;
    }
    // JSON messages
    try {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    } catch (e) {
      console.error("Failed to parse message:", e);
    }
  };
}

function handleServerMessage(data) {
  switch (data.type) {
    case "transcript":
      // show user's transcribed speech in chat — stays permanently
      senderText(data.text);
      setStatusText("Processing...");
      break;

    case "response":
      // show agent response in chat — stays permanently
      receiverText(data.text);
      // just update the small status label, NOT the chat
      setStatusText("Response received.");
      // go back to idle orb — mic does NOT auto-start
      ShowHood();
      break;

    case "error":
      receiverText("Sorry, something went wrong. Please try again.");
      ShowHood();
      break;

    case "ready":
      ShowHood();
      break;

    default:
      console.log("Unknown message type:", data.type);
  }
}

// ── AUDIO PLAYBACK ──
async function playAudioResponse(audioBlob) {
  try {
    if (!audioContext) audioContext = new AudioContext();
    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    source.start(0);

    // show wave while Jarvis is speaking
    $("#Oval").attr("hidden", true);
    $("#SiriWave").attr("hidden", false);
    setStatusText("Speaking...");

    // when Jarvis finishes speaking — go back to idle, do NOT auto-start mic
    source.onended = () => {
      ShowHood();
      setStatusText("Ask me anything...");
    };

  } catch (e) {
    console.error("Audio playback error:", e);
    ShowHood();
  }
}

// ── STATUS TEXT (small label only — does NOT affect chat) ──
function setStatusText(msg) {
  $("#connection-status").text(msg);
}

// ── VOICE CAPTURE & SILENCE DETECTION ──
async function startRecording() {
  if (isRecording) return; // prevent double trigger
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new AudioContext();
    mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
    audioChunks = [];
    isRecording = true;

    // silence detection
    const analyser = audioContext.createAnalyser();
    const micSource = audioContext.createMediaStreamSource(stream);
    micSource.connect(analyser);
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const resetSilenceTimer = () => {
      clearTimeout(silenceTimeout);
      silenceTimeout = setTimeout(() => {
        if (isRecording) {
          console.log("5 seconds silence — auto stopping.");
          stopRecording();
        }
      }, 5000);
    };

    volumeCheckInterval = setInterval(() => {
      analyser.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
      if (sum / bufferLength > 10) resetSilenceTimer();
    }, 200);

    resetSilenceTimer();

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      const arrayBuffer = await audioBlob.arrayBuffer();
      if (wsConnected && ws) {
        ws.send(arrayBuffer);
      } else {
        receiverText("Not connected to backend. Please wait...");
        ShowHood();
      }
      isRecording = false;
    };

    mediaRecorder.start();
    $("#Oval").attr("hidden", true);
    $("#SiriWave").attr("hidden", false);
    $("#StopMicBtn").removeAttr("hidden");
    $("#MicBtn").addClass("recording");
    setStatusText("Listening...");

  } catch (err) {
    console.error("Mic error:", err);
    isRecording = false;
    alert("Microphone access denied. Please allow microphone access.");
  }
}

function stopRecording() {
  if (!mediaRecorder || !isRecording) return;
  mediaRecorder.stop();
  mediaRecorder.stream.getTracks().forEach(t => t.stop());
  clearInterval(volumeCheckInterval);
  clearTimeout(silenceTimeout);
  setStatusText("Transcribing...");
  $("#MicBtn").removeClass("recording");
  $("#StopMicBtn").attr("hidden", true);
}

// ── SEND TEXT MESSAGE ──
function PlayAssistant(message) {
  if (message.trim() === "") return;
  senderText(message);
  $("#chatbox").val("");
  ShowHideButton("");
  $("#Oval").attr("hidden", true);
  $("#SiriWave").attr("hidden", false);
  setStatusText("Processing...");

  if (wsConnected && ws) {
    ws.send(JSON.stringify({ type: "text", text: message }));
  } else {
    receiverText("Not connected to backend. Retrying connection...");
    ShowHood();
  }
}

function ShowHideButton(message) {
  if (message.length === 0) {
    $("#MicBtn").attr("hidden", false);
    $("#SendBtn").attr("hidden", true);
  } else {
    $("#MicBtn").attr("hidden", true);
    $("#SendBtn").attr("hidden", false);
  }
}

// ── DOCUMENT READY ──
$(document).ready(function () {

  // init siri wave
  var siriWave = new SiriWave({
    container: document.getElementById("siri-container"),
    width: 940,
    style: "ios9",
    amplitude: "1",
    speed: "0.30",
    height: 200,
    autostart: true,
  });

  // connect WebSocket
  connectWebSocket();

  // boot sequence
  bootSequence();

  // ── MIC BUTTON — click to toggle ──
  $("#MicBtn").on("click", function (e) {
    e.preventDefault();
    if (!isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  });

  // ── STOP BUTTON ──
  $("#StopMicBtn").on("click", function () {
    if (isRecording) stopRecording();
  });

  // ── CLICK WAVE TO STOP ──
  $("#siri-container, #SiriWave").on("click", function () {
    if (isRecording) stopRecording();
  });

  // ── SEND BUTTON ──
  $("#SendBtn").on("click", function () {
    PlayAssistant($("#chatbox").val());
  });

  // ── CHATBOX INPUT ──
  $("#chatbox").on("keyup", function () {
    ShowHideButton($(this).val());
  });

  $("#chatbox").on("keypress", function (e) {
    if (e.which === 13) PlayAssistant($(this).val());
  });

  // ── CHAT TOGGLE ──
  $("#ChatBtn").on("click", function () {
    $("#chat-canvas").toggle();
  });

  // ── KEYBOARD SHORTCUT Ctrl+J / Cmd+J ──
  document.addEventListener("keyup", function (e) {
    if (e.key === "j" && (e.metaKey || e.ctrlKey)) {
      if (!isRecording) startRecording();
      else stopRecording();
    }
  });
});

// ── BOOT SEQUENCE ──
function bootSequence() {
  const steps = [
    { delay: 800,  msg: "Loading neural core..." },
    { delay: 1800, msg: "Connecting to HR systems..." },
    { delay: 2800, msg: "Syncing candidate database..." },
    { delay: 3800, msg: "Voice module ready..." },
    { delay: 4600, msg: "Welcome. I am Jarvis." },
  ];

  steps.forEach(s => {
    setTimeout(() => { $("#WishMessage").text(s.msg); }, s.delay);
  });

  setTimeout(() => { $("#HelloGreet").attr("hidden", false); }, 4800);
  setTimeout(() => { hideStart(); }, 6000);
}
