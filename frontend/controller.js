// controller.js
// All UI update functions — called by main.js WebSocket handlers
// No eel dependency — works purely on WebSocket messages from Render backend

$(document).ready(function () {

  // ── DISPLAY MESSAGE (siri wave text) ──
  window.DisplayMessage = function (message) {
    $(".siri-message li:first").text(message);
    try {
      $(".siri-message").textillate("start");
    } catch (e) {
      $(".siri-message").text(message);
    }
  };

  // ── SHOW HOOD (orb / oval section) ──
  window.ShowHood = function () {
    $("#Oval").attr("hidden", false);
    $("#SiriWave").attr("hidden", true);
  };

  // ── SENDER TEXT (user message bubble) ──
  window.senderText = function (message) {
    var chatBox = document.getElementById("chat-canvas-body");
    if (!chatBox || message.trim() === "") return;
    chatBox.innerHTML += `
      <div class="row justify-content-end mb-4">
        <div class="width-size">
          <div class="sender_message">${escapeHtml(message)}</div>
        </div>
      </div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
    // auto show chat canvas when messages arrive
    $("#chat-canvas").show();
  };

  // ── RECEIVER TEXT (agent response bubble) ──
  window.receiverText = function (message) {
    var chatBox = document.getElementById("chat-canvas-body");
    if (!chatBox || message.trim() === "") return;
    chatBox.innerHTML += `
      <div class="row justify-content-start mb-4">
        <div class="width-size">
          <div class="receiver_message">${escapeHtml(message)}</div>
        </div>
      </div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
    $("#chat-canvas").show();
  };

  // ── HIDE START PAGE → SHOW OVAL ──
  window.hideStart = function () {
    $("#Start").attr("hidden", true);
    setTimeout(function () {
      $("#Oval").removeClass("animate__animated animate__zoomIn");
      void $("#Oval")[0].offsetWidth; // reflow
      $("#Oval").addClass("animate__animated animate__zoomIn");
      $("#Oval").attr("hidden", false);
    }, 500);
  };

  // ── HIDE HELLO GREET ──
  window.hideHelloGreet = function () {
    $("#HelloGreet").attr("hidden", true);
  };

  // ── HELPER: escape HTML to prevent XSS ──
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
  }

});
