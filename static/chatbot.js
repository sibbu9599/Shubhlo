/**
 * Shubhlo AI Assistant - Advanced Smart Chatbot Script
 * Supports Voice Input (Speech-to-Text), Live DB Query API, and Interactive Chips.
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Create Floating Chat Widget DOM elements dynamically if not already present
  if (!document.getElementById('shubhlo-chat-trigger')) {
    const triggerBtn = document.createElement('button');
    triggerBtn.id = 'shubhlo-chat-trigger';
    triggerBtn.className = 'shubhlo-chat-trigger';
    triggerBtn.setAttribute('aria-label', 'Open Shubhlo AI Assistant');
    triggerBtn.innerHTML = `
      <span class="chat-pulse"></span>
      <span class="chat-badge-notify">AI</span>
      👑
    `;
    document.body.appendChild(triggerBtn);

    const chatWin = document.createElement('div');
    chatWin.id = 'shubhlo-chat-window';
    chatWin.className = 'shubhlo-chat-window';
    chatWin.innerHTML = `
      <div class="chat-header">
        <div class="chat-header-info">
          <div class="chat-header-avatar">👑</div>
          <div class="chat-header-title">
            <h4>Shubhlo AI Assistant</h4>
            <span>Online • Smart Event Guide</span>
          </div>
        </div>
        <button class="chat-close-btn" id="shubhlo-chat-close" title="Close">✕</button>
      </div>

      <div class="chat-suggestions" id="chat-suggestions">
        <button class="suggestion-chip" data-query="hi">👋 Welcome / Help</button>
        <button class="suggestion-chip" data-query="marriage garden venue rate">🏰 Venues & Gardens</button>
        <button class="suggestion-chip" data-query="catering menu price">🍲 Catering & Food</button>
        <button class="suggestion-chip" data-query="dj sound price">🎵 DJ & Sound</button>
        <button class="suggestion-chip" data-query="photography cost">📸 Photography</button>
        <button class="suggestion-chip" data-query="how to book">📝 How to Book</button>
        <button class="suggestion-chip" data-query="chat on whatsapp with owner" style="background:#dcfce7;color:#15803d;border:1px solid #86efac;font-weight:bold;">💬 Chat on WhatsApp</button>
        <button class="suggestion-chip" data-query="contact support">📞 Contact Support</button>
      </div>

      <div class="chat-messages-container" id="chat-messages">
        <div class="chat-message bot">
          👋 <strong>Hello! I am your Shubhlo AI Assistant!</strong><br>
          I can help you find and compare the best verified venues, caterers, DJs, photographers, and event planners for your wedding or special celebration.<br><br>
          <em>Ask any question or click a suggestion below! ✨</em>
        </div>
      </div>

      <form class="chat-footer" id="chat-form">
        <input type="text" id="chat-input" placeholder="Type or click mic to ask AI..." autocomplete="off">
        <button type="button" class="chat-mic-btn" id="chat-mic" title="Voice Input (Speech-to-Text)">🎙️</button>
        <button type="submit" class="chat-send-btn" title="Send Message">➔</button>
      </form>
    `;
    document.body.appendChild(chatWin);
  }

  const trigger = document.getElementById('shubhlo-chat-trigger');
  const windowEl = document.getElementById('shubhlo-chat-window');
  const closeBtn = document.getElementById('shubhlo-chat-close');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const messagesContainer = document.getElementById('chat-messages');
  const micBtn = document.getElementById('chat-mic');
  const suggestionsContainer = document.getElementById('chat-suggestions');

  if (!trigger || !windowEl) return;

  // Toggle Chat Window
  trigger.addEventListener('click', function () {
    windowEl.classList.toggle('active');
    if (windowEl.classList.contains('active')) {
      input.focus();
    }
  });

  closeBtn.addEventListener('click', function () {
    windowEl.classList.remove('active');
  });

  // Suggestion Chips Click Handler
  if (suggestionsContainer) {
    suggestionsContainer.addEventListener('click', function (e) {
      if (e.target.classList.contains('suggestion-chip')) {
        const query = e.target.getAttribute('data-query');
        if (query) {
          sendQuery(query);
        }
      }
    });
  }

  // Voice Input (Speech-to-Text) Web Speech API
  let recognition = null;
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US'; // English (US) / International
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = function () {
      if (micBtn) micBtn.classList.add('recording');
      input.placeholder = 'Listening to your voice...';
    };

    recognition.onresult = function (event) {
      const transcript = event.results[0][0].transcript;
      input.value = transcript;
      sendQuery(transcript);
    };

    recognition.onerror = function () {
      if (micBtn) micBtn.classList.remove('recording');
      input.placeholder = 'Type or click mic to ask AI...';
    };

    recognition.onend = function () {
      if (micBtn) micBtn.classList.remove('recording');
      input.placeholder = 'Type or click mic to ask AI...';
    };
  }

  if (micBtn) {
    micBtn.addEventListener('click', function () {
      if (!recognition) {
        alert('Voice input is not supported in this browser. Please type your message!');
        return;
      }
      try {
        recognition.start();
      } catch (err) {
        recognition.stop();
      }
    });
  }

  // Form Submit Handler
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const query = input.value.trim();
    if (query) {
      sendQuery(query);
      input.value = '';
    }
  });

  // Send Query to AI
  function sendQuery(queryText) {
    appendUserMessage(queryText);
    showTypingIndicator();

    // Try fetching from Flask /api/assistant endpoint first
    fetch('/api/assistant', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: queryText })
    })
      .then(res => res.json())
      .then(data => {
        removeTypingIndicator();
        if (data && data.reply) {
          appendBotMessage(data.reply);
        } else {
          appendBotMessage(getLocalAIResponse(queryText));
        }
      })
      .catch(err => {
        removeTypingIndicator();
        // Fallback to local response if server offline
        appendBotMessage(getLocalAIResponse(queryText));
      });
  }

  function appendUserMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message user';
    msgDiv.textContent = text;
    messagesContainer.appendChild(msgDiv);
    scrollToBottom();
  }

  function appendBotMessage(htmlContent) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message bot';
    msgDiv.innerHTML = htmlContent;
    messagesContainer.appendChild(msgDiv);
    scrollToBottom();
  }

  function showTypingIndicator() {
    removeTypingIndicator();
    const typingDiv = document.createElement('div');
    typingDiv.id = 'chat-typing';
    typingDiv.className = 'chat-typing-indicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const typing = document.getElementById('chat-typing');
    if (typing) typing.remove();
  }

  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Local fallback response generator in English
  function getLocalAIResponse(query) {
    const q = query.toLowerCase().trim();

    if (q.includes("hi") || q.includes("hello") || q.includes("namaste") || q.includes("help") || q.includes("welcome")) {
      return "👑 <strong>Hello! I am your Shubhlo AI Assistant.</strong><br>I can assist you with verified venue listings, catering menus, DJ setups, photography packages, and event bookings.";
    }

    if (q.includes("venue") || q.includes("garden") || q.includes("lawn") || q.includes("place")) {
      return "🏰 <strong>Marriage Gardens & Venues:</strong><br>We have verified open lawns & air-conditioned marriage halls available.<br>👉 <a href='/services'>Explore All Venues ➔</a>";
    }

    if (q.includes("cater") || q.includes("food") || q.includes("khana") || q.includes("menu")) {
      return "🍲 <strong>Catering & Buffet:</strong><br>Multicuisine wedding food packages starting from ₹50,000.<br>👉 <a href='/services'>Explore Catering Services ➔</a>";
    }

    if (q.includes("book") || q.includes("step") || q.includes("how")) {
      return "📝 <strong>How to Book:</strong><br>1. Go to <a href='/booking1'>Book Now</a>.<br>2. Enter your event details & Tehsil location.<br>3. Select your preferred verified vendors.<br>4. Pay nominal token money of ₹5,118 to lock your date! (Remaining deal & package is decided directly between you and the vendor, with ₹5,000 deducted from your final bill).";
    }

    if (q.includes("price") || q.includes("rate") || q.includes("cost") || q.includes("token")) {
      return "💰 <strong>Direct Deal & Token Money Policy:</strong><br>Shubhlo par keval <strong>₹5,118 Token Money</strong> jama karke date lock karni hoti hai. Baki sabhi package rate, services aur bill customer aur vendor aapas mein decide karte hain. ₹5,000 aapke final bill se kam ho jayenge!";
    }

    if (q.includes("whatsapp") || q.includes("owner") || q.includes("chat") || q.includes("ऑनर") || q.includes("बात")) {
      return "💬 <strong>Direct WhatsApp Chat with Owner:</strong><br>Click below to chat 1-on-1 on WhatsApp with Shubhlo Owner (+91 7067883131):<br><br><a href='https://wa.me/917067883131?text=Namaste%20Shubhlo%20Owner!%20I%20have%20an%20inquiry%20regarding%20event%20services.' target='_blank' style='background:linear-gradient(135deg, #25d366, #128c7e);color:white;padding:8px 16px;border-radius:20px;font-weight:bold;text-decoration:none;display:inline-block;'>💬 Open WhatsApp Chat ➔</a>";
    }

    return "✨ <strong>Shubhlo AI Assistant:</strong><br>You asked about: '<em>" + query + "</em>'. Please feel free to call or <a href='https://wa.me/917067883131' target='_blank'>WhatsApp our Owner at +91 7067883131</a> or start a <a href='/booking1'>Direct Booking</a>!";
  }
});