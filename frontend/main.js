// ── BACKEND URL ──
// Change this to your Render backend URL after deployment
const BACKEND_WS_URL = "wss://jarvis-claude.onrender.com/ws";

// ── WEBSOCKET ──
let ws = null;
let wsConnected = false;
let audioContext = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

function connectWebSocket() {
  ws = new WebSocket(BACKEND_WS_URL);

  ws.onopen = () => {
    wsConnected = true;
    $("#connection-status").text("Connected").css("color", "#00ff88");
    console.log("WebSocket connected");
  };

  ws.onclose = () => {
    wsConnected = false;
    $("#connection-status").text("Disconnected — retrying...").css("color", "#ff4444");
    // auto reconnect after 3 seconds
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
      // user's speech transcribed — show in chat
      senderText(data.text);
      DisplayMessage("Processing...");
      break;

    case "response":
      // agent text response
      receiverText(data.text);
      DisplayMessage(data.text);
      break;

    case "agent_info":
      // which agent handled the request
      console.log("Agent used:", data.agent);
      break;

    case "error":
      receiverText("Sorry, something went wrong. Please try again.");
      ShowHood();
      break;

    case "ready":
      // backend signals it's ready after boot
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
    // show wave while speaking
    $("#Oval").attr("hidden", true);
    $("#SiriWave").attr("hidden", false);
    source.onended = () => {
      ShowHood();
    };
  } catch (e) {
    console.error("Audio playback error:", e);
    ShowHood();
  }
}

// ── VOICE CAPTURE ──
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new AudioContext();
    mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
    audioChunks = [];
    isRecording = true;

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      const arrayBuffer = await audioBlob.arrayBuffer();
      if (wsConnected && ws) {
        // send as binary
        ws.send(arrayBuffer);
      } else {
        receiverText("Not connected to backend. Please wait...");
      }
      isRecording = false;
    };

    mediaRecorder.start();
    $("#Oval").attr("hidden", true);
    $("#SiriWave").attr("hidden", false);
    DisplayMessage("Listening...");
    $("#MicBtn").css("color", "#ff4444");

  } catch (err) {
    console.error("Mic error:", err);
    alert("Microphone access denied. Please allow microphone access.");
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    // Turn off the microphone hardware
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
    
    // Change the screen text so you know it stopped
    DisplayMessage("Transcribing..."); 
    $("#MicBtn").css("color", "#ffffff");
  }
}

// ── SEND TEXT MESSAGE ──
function PlayAssistant(message) {
  if (message.trim() === "") return;
  senderText(message);
  $("#chatbox").val("");
  $("#MicBtn").attr("hidden", false);
  $("#SendBtn").attr("hidden", true);
  $("#Oval").attr("hidden", true);
  $("#SiriWave").attr("hidden", false);
  DisplayMessage("Processing...");

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

  // textillate on siri-message
  $(".siri-message").textillate({
    loop: true,
    sync: true,
    in: { effect: "fadeInUp", sync: true },
    out: { effect: "fadeOutUp", sync: true },
  });

  // connect WebSocket
  connectWebSocket();

  // boot sequence — replaces eel.init()
  bootSequence();

  // ── MIC BUTTON ── click to toggle
  $("#MicBtn").on("click", function (e) {
    e.preventDefault();
    if (!isRecording) {
      // First click: Start listening
      startRecording();
    } else {
      // Second click: Stop and send
      stopRecording();
    }
  });

  // ── SEND BUTTON ──
  $("#SendBtn").on("click", function () {
    const message = $("#chatbox").val();
    PlayAssistant(message);
  });

  // ── CHATBOX INPUT ──
  $("#chatbox").on("keyup", function () {
    ShowHideButton($(this).val());
  });

  $("#chatbox").on("keypress", function (e) {
    if (e.which === 13) {
      PlayAssistant($(this).val());
    }
  });

  // ── CHAT TOGGLE ──
  $("#ChatBtn").on("click", function () {
    const canvas = $("#chat-canvas");
    canvas.toggle();
  });

  // ── KEYBOARD SHORTCUT (Cmd+J) ──
  document.addEventListener("keyup", function (e) {
    if (e.key === "j" && e.metaKey) {
      startRecording();
      setTimeout(stopRecording, 4000); // auto stop after 4s
    }
  });
});

// ── BOOT SEQUENCE (replaces eel init flow) ──
function bootSequence() {
  const steps = [
    { delay: 800,  msg: "Loading neural core..." },
    { delay: 1800, msg: "Connecting to HR systems..." },
    { delay: 2800, msg: "Syncing candidate database..." },
    { delay: 3800, msg: "Voice module ready..." },
    { delay: 4600, msg: "Welcome. I am Jarvis." },
  ];

  steps.forEach(s => {
    setTimeout(() => {
      $("#WishMessage").text(s.msg);
    }, s.delay);
  });

  // after boot — show HelloGreet then transition to Oval
  setTimeout(() => {
    $("#HelloGreet").attr("hidden", false);
  }, 4800);

  setTimeout(() => {
    hideStart();
  }, 6000);
}
