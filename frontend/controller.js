// controller.js
// UI update functions — WebSocket driven, no eel

$(document).ready(function () {

  // ── INJECT CHAT PALETTE STYLES ──
  // Ensures chat box is scrollable and messages stay permanently
  $("<style>")
    .prop("type", "text/css")
    .html(`
      #chat-canvas {
        position: fixed;
        bottom: 120px;
        right: 24px;
        width: 380px;
        height: 420px;
        background: rgba(10, 10, 20, 0.92);
        border: 1px solid rgba(0, 170, 255, 0.3);
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        z-index: 999;
        backdrop-filter: blur(10px);
        box-shadow: 0 0 30px rgba(0, 170, 255, 0.1);
      }
      #chat-canvas-header {
        padding: 10px 16px;
        border-bottom: 1px solid rgba(0, 170, 255, 0.2);
        font-size: 11px;
        letter-spacing: 2px;
        color: rgba(0, 170, 255, 0.7);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-shrink: 0;
      }
      #chat-canvas-body {
        flex: 1;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 12px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        scroll-behavior: smooth;
      }
      #chat-canvas-body::-webkit-scrollbar {
        width: 4px;
      }
      #chat-canvas-body::-webkit-scrollbar-track {
        background: transparent;
      }
      #chat-canvas-body::-webkit-scrollbar-thumb {
        background: rgba(0, 170, 255, 0.3);
        border-radius: 2px;
      }
      .sender_message {
        padding: 8px 12px;
        border: 1px solid rgba(0, 69, 255, 0.6);
        border-radius: 16px 16px 0px 16px;
        color: white;
        background-color: rgba(0, 69, 255, 0.4);
        font-size: 13px;
        line-height: 1.5;
        word-break: break-word;
        max-width: 100%;
      }
      .receiver_message {
        padding: 8px 12px;
        border: 1px solid rgba(0, 200, 255, 0.4);
        border-radius: 0px 16px 16px 16px;
        color: #c8f0ff;
        background-color: rgba(0, 170, 255, 0.08);
        font-size: 13px;
        line-height: 1.5;
        word-break: break-word;
        max-width: 100%;
      }
      .msg-row {
        display: flex;
        width: 100%;
      }
      .msg-row.sent { justify-content: flex-end; }
      .msg-row.recv { justify-content: flex-start; }
      .msg-bubble { max-width: 88%; }
      #chat-close-btn {
        background: none;
        border: none;
        color: rgba(0,170,255,0.5);
        cursor: pointer;
        font-size: 16px;
        padding: 0;
        line-height: 1;
      }
      #chat-close-btn:hover { color: rgba(0,170,255,1); }
      #MicBtn.recording {
        color: #ff4444 !important;
        box-shadow: 0 0 12px rgba(255, 68, 68, 0.6);
      }
    `)
    .appendTo("head");

  // ── BUILD CHAT PALETTE HTML ──
  // Replace the plain div with a structured palette
  if ($("#chat-canvas").length) {
    $("#chat-canvas").html(`
      <div id="chat-canvas-header">
        <span>// CONVERSATION</span>
        <button id="chat-close-btn" title="Close">✕</button>
      </div>
      <div id="chat-canvas-body"></div>
    `);
    // start hidden — shows when first message arrives
    $("#chat-canvas").hide();
  }

  // close button
  $(document).on("click", "#chat-close-btn", function () {
    $("#chat-canvas").hide();
  });

  // ── DISPLAY MESSAGE — siri wave status text ONLY ──
  // This only updates the animated label under the wave
  // It does NOT touch the chat palette
  window.DisplayMessage = function (message) {
    // just set text directly — no textillate looping on this
    $(".siri-message").first().text(message);
  };

  // ── SHOW HOOD (orb / oval section) ──
  window.ShowHood = function () {
    $("#Oval").attr("hidden", false);
    $("#SiriWave").attr("hidden", true);
  };

  // ── SENDER TEXT — appends permanently to chat palette ──
  window.senderText = function (message) {
    if (!message || message.trim() === "") return;
    const chatBody = document.getElementById("chat-canvas-body");
    if (!chatBody) return;

    const row = document.createElement("div");
    row.className = "msg-row sent";
    row.innerHTML = `
      <div class="msg-bubble">
        <div class="sender_message">${escapeHtml(message)}</div>
      </div>`;
    chatBody.appendChild(row);
    chatBody.scrollTop = chatBody.scrollHeight;

    // show palette when first message arrives
    $("#chat-canvas").show();
  };

  // ── RECEIVER TEXT — appends permanently to chat palette ──
  window.receiverText = function (message) {
    if (!message || message.trim() === "") return;
    const chatBody = document.getElementById("chat-canvas-body");
    if (!chatBody) return;

    const row = document.createElement("div");
    row.className = "msg-row recv";
    row.innerHTML = `
      <div class="msg-bubble">
        <div class="receiver_message">${escapeHtml(message)}</div>
      </div>`;
    chatBody.appendChild(row);
    chatBody.scrollTop = chatBody.scrollHeight;

    $("#chat-canvas").show();
  };

  // ── HIDE START PAGE → SHOW OVAL ──
  window.hideStart = function () {
    $("#Start").attr("hidden", true);
    setTimeout(function () {
      $("#Oval").removeClass("animate__animated animate__zoomIn");
      void $("#Oval")[0].offsetWidth;
      $("#Oval").addClass("animate__animated animate__zoomIn");
      $("#Oval").attr("hidden", false);
    }, 500);
  };

  // ── HIDE HELLO GREET ──
  window.hideHelloGreet = function () {
    $("#HelloGreet").attr("hidden", true);
  };

  // ── HELPER ──
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
  }

});
