/* ============================================================
   MedRetriv Web App Controller
   #9  — Voice Input (Web Speech API)
   #10 — Text-to-Speech robot voice (SpeechSynthesis)
   #13 — Lip-sync bridge: TTS speaking → robot animation pulse
   ============================================================ */
document.addEventListener('DOMContentLoaded', function () {

  var API_URL = window.location.origin.includes('8000') ? '/chat' : 'http://127.0.0.1:8000/chat';

  var chats = JSON.parse(localStorage.getItem('medretriv_chats')) || {
    'chat_1': { title: 'New Consultation', messages: [] }
  };
  var currentChatId = localStorage.getItem('medretriv_active_chat') || 'chat_1';
  var isGenerating = false;

  // ── Language Mode ('en' or 'ar') ───────────────────────
  var activeLang = localStorage.getItem('medretriv_lang') || 'en';

  var viewport          = document.getElementById('chat-viewport');
  var userInput         = document.getElementById('user-input');
  var sendBtn           = document.getElementById('send-btn');
  var starterContainer  = document.getElementById('starter-prompts-container');
  var newConsBtn        = document.getElementById('new-consultation-btn');
  var clearBtn          = document.getElementById('clear-history-btn');
  var exportBtn         = document.getElementById('export-chat-btn');
  var themeBtn          = document.getElementById('theme-toggle-btn');
  var consultList       = document.getElementById('consultation-list');
  var burgerBtn         = document.getElementById('burger-btn');
  var drawer            = document.getElementById('drawer');
  var drawerOverlay     = document.getElementById('drawer-overlay');
  var drawerCloseBtn    = document.getElementById('drawer-close-btn');
  var micBtn            = document.getElementById('mic-btn');
  var ttsDrawerBtn      = document.getElementById('tts-toggle-btn');
  var ttsHeaderBtn      = document.getElementById('tts-header-btn');
  var langToggleBtn     = document.getElementById('lang-toggle-btn');

  var DOC_NAMES = {
    "breast-cancer-screening-final-rec.pdf":                              "USPSTF Guideline",
    "breast-cancer-screening-final-evidence-review.pdf":                  "AHRQ Evidence Review",
    "Frntiers Breast Cancer pathogenesis, diagnosis and treatment (2026).pdf": "Frontiers in Oncology",
    "Nature Review Breast cancer pathogenesis and treatments (2025).pdf": "Nature STTT Review",
    "NCINIH – Breast Cancer Overview (Patient & Professional Versions).pdf": "NCI / NIH Overview"
  };

  // ── TTS State ──────────────────────────────────────────
  var ttsEnabled = localStorage.getItem('medretriv_tts') !== 'off';
  var ttsVoice   = null;
  var ttsSpeaking = false;

  function loadVoices() {
    var voices = window.speechSynthesis.getVoices();
    // English voices (preferred)
    var preferredEN = ['Google UK English Male', 'Microsoft David', 'Alex', 'Daniel'];
    for (var p = 0; p < preferredEN.length; p++) {
      for (var v = 0; v < voices.length; v++) {
        if (voices[v].name === preferredEN[p]) { ttsVoice = voices[v]; break; }
      }
      if (ttsVoice) break;
    }
    if (!ttsVoice) {
      ttsVoice = voices.find(function (v) { return v.lang.startsWith('en'); }) || voices[0] || null;
    }
  }

  if ('speechSynthesis' in window) {
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }

  function syncTtsUI() {
    var icon  = ttsEnabled ? '🔊' : '🔇';
    var label = ttsEnabled ? 'Voice: On' : 'Voice: Off';
    if (document.getElementById('tts-icon'))  document.getElementById('tts-icon').textContent  = icon;
    if (document.getElementById('tts-label')) document.getElementById('tts-label').textContent = label;
    if (ttsHeaderBtn) {
      ttsHeaderBtn.textContent = icon;
      ttsHeaderBtn.classList.toggle('active', ttsEnabled);
    }
    localStorage.setItem('medretriv_tts', ttsEnabled ? 'on' : 'off');
  }
  syncTtsUI();

  function toggleTts() {
    ttsEnabled = !ttsEnabled;
    if (!ttsEnabled && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      if (window.speechSynthesis.pause) window.speechSynthesis.pause();
      window.speechSynthesis.cancel();
    }
    ttsSpeaking = false;
    if (window.MedBot3D && window.MedBot3D.setLipSync) window.MedBot3D.setLipSync(false);
    syncTtsUI();
  }


  /* ── #10 Text-to-Speech + #13 Lip-Sync ──────────────── */
  function speakText(text, langOverride) {
    if (!ttsEnabled || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    var lang = langOverride || activeLang;

    // Pick the right voice for the language
    var voices = window.speechSynthesis.getVoices();
    var voice = ttsVoice; // default English
    if (lang === 'ar') {
      var arVoice = voices.find(function (v) {
        return v.lang.startsWith('ar');
      });
      if (arVoice) voice = arVoice;
    }

    // Strip markdown / HTML tags for cleaner speech
    var clean = text
      .replace(/<[^>]*>/g, '')
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/#{1,6}\s/g, '')
      .replace(/\[.*?\]/g, '')
      .trim();

    // Split into natural sentence chunks (max 200 chars each to avoid timeout)
    var sentences = clean.match(/[^.!?؟]+[.!?؟]+/g) || [clean];
    var chunks = [];
    var current = '';
    sentences.forEach(function (s) {
      if ((current + s).length > 200) { if (current) chunks.push(current.trim()); current = s; }
      else { current += s; }
    });
    if (current.trim()) chunks.push(current.trim());

    var idx = 0;
    function speakNext() {
      if (idx >= chunks.length) {
        ttsSpeaking = false;
        if (window.MedBot3D && window.MedBot3D.setLipSync) window.MedBot3D.setLipSync(false);
        return;
      }
      var utt = new SpeechSynthesisUtterance(chunks[idx++]);
      utt.voice  = voice;
      utt.rate   = lang === 'ar' ? 0.88 : 0.94;
      utt.pitch  = 0.88;
      utt.volume = 1.0;
      utt.lang   = lang === 'ar' ? 'ar-SA' : 'en-US';
      utt.onstart = function () {
        ttsSpeaking = true;
        if (window.MedBot3D && window.MedBot3D.setLipSync) window.MedBot3D.setLipSync(true);
      };
      utt.onend = speakNext;
      utt.onerror = speakNext;
      window.speechSynthesis.speak(utt);
    }
    speakNext();
  }

  // ── Translation Helper (MyMemory free API) ──────────────
  async function translate(text, fromLang, toLang) {
    try {
      var url = 'https://api.mymemory.translated.net/get?q=' +
        encodeURIComponent(text) + '&langpair=' + fromLang + '|' + toLang;
      var res = await fetch(url);
      var data = await res.json();
      if (data && data.responseData && data.responseData.translatedText) {
        return data.responseData.translatedText;
      }
    } catch (e) {
      console.warn('Translation failed, using original text:', e);
    }
    return text; // fallback: use original if translation fails
  }

  // ── Language Toggle ──────────────────────────────────────
  function syncLangUI() {
    var btn = document.getElementById('lang-toggle-btn');
    if (!btn) return;
    if (activeLang === 'ar') {
      btn.textContent = '🇸🇦';
      btn.title = 'Switch to English';
      btn.classList.add('active');
      userInput.setAttribute('placeholder', 'اسأل سؤالاً طبياً باللغة العربية... (أو اضغط 🎤)');
      userInput.setAttribute('dir', 'rtl');
    } else {
      btn.textContent = '🇬🇧';
      btn.title = 'Switch to Arabic / التبديل للعربية';
      btn.classList.remove('active');
      userInput.setAttribute('placeholder', 'Ask a clinical breast cancer or screening question... (or tap 🎤)');
      userInput.setAttribute('dir', 'ltr');
    }
    // Update speech recognition language
    if (recognition) recognition.lang = activeLang === 'ar' ? 'ar-SA' : 'en-US';
    localStorage.setItem('medretriv_lang', activeLang);
  }

  function toggleLang() {
    activeLang = activeLang === 'en' ? 'ar' : 'en';
    syncLangUI();
  }

  syncLangUI();

  // ── Voice Input (#9) ────────────────────────────────────
  var recognition = null;
  var micListening = false;

  function initSpeechRecognition() {
    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      if (micBtn) { micBtn.style.opacity = '0.35'; micBtn.title = 'Voice input not supported in this browser'; }
      return;
    }
    recognition = new SpeechRecognition();
    recognition.continuous    = false;
    recognition.interimResults = true;
    recognition.lang          = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = function () {
      micListening = true;
      if (micBtn) micBtn.classList.add('listening');
      if (window.MedBot3D) window.MedBot3D.setRobotState('surprised');
    };

    recognition.onresult = function (e) {
      var interim = '';
      var final   = '';
      for (var i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) final   += e.results[i][0].transcript;
        else                       interim += e.results[i][0].transcript;
      }
      userInput.value = final || interim;
      userInput.style.height = 'auto';
      userInput.style.height = Math.min(userInput.scrollHeight, 100) + 'px';
    };

    recognition.onend = function () {
      micListening = false;
      if (micBtn) micBtn.classList.remove('listening');
      if (window.MedBot3D) window.MedBot3D.setRobotState('idle');
      // Auto-send if something was captured
      if (userInput.value.trim()) handleSend();
    };

    recognition.onerror = function (e) {
      micListening = false;
      if (micBtn) micBtn.classList.remove('listening');
      console.warn('Speech recognition error:', e.error);
      if (window.MedBot3D) window.MedBot3D.setRobotState('caution');
    };
  }
  initSpeechRecognition();

  // ── App Init ────────────────────────────────────────────
  initApp();

  function initApp() {
    if (!chats[currentChatId]) currentChatId = Object.keys(chats)[0] || 'chat_1';
    renderMessages();
    renderConsultList();
    setupListeners();
  }

  function saveState() {
    localStorage.setItem('medretriv_chats', JSON.stringify(chats));
    localStorage.setItem('medretriv_active_chat', currentChatId);
  }

  // ── Drawer ──────────────────────────────────────────────
  function openDrawer()  { drawer.classList.add('open'); drawerOverlay.classList.add('active'); burgerBtn.classList.add('open'); }
  function closeDrawer() { drawer.classList.remove('open'); drawerOverlay.classList.remove('active'); burgerBtn.classList.remove('open'); }

  function setupListeners() {
    // Auto-resize textarea & trigger glowing magenta typing expression
    var typingTimeout = null;
    function triggerTypingState() {
      if (!isGenerating && window.MedBot3D) {
        window.MedBot3D.setRobotState('typing');
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(function () {
          if (!isGenerating && window.MedBot3D) window.MedBot3D.setRobotState('idle');
        }, 2200);
      }
    }

    userInput.addEventListener('input', function () {
      userInput.style.height = 'auto';
      userInput.style.height = Math.min(userInput.scrollHeight, 100) + 'px';
      if (userInput.value.trim().length > 0) triggerTypingState();
    });
    userInput.addEventListener('focus', function () {
      if (userInput.value.trim().length > 0) triggerTypingState();
    });
    userInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      } else {
        triggerTypingState();
      }
    });
    sendBtn.addEventListener('click', handleSend);


    // Mic button (#9)
    if (micBtn && recognition) {
      micBtn.addEventListener('click', function () {
        if (micListening) {
          recognition.stop();
        } else {
          // Cancel any ongoing TTS before listening
          if ('speechSynthesis' in window) window.speechSynthesis.cancel();
          recognition.start();
        }
      });
    }

    // TTS toggles (#10)
    if (ttsDrawerBtn) ttsDrawerBtn.addEventListener('click', function () { toggleTts(); });
    if (ttsHeaderBtn) ttsHeaderBtn.addEventListener('click', function () { toggleTts(); });

    // Language toggle (Arabic/English)
    var langBtn = document.getElementById('lang-toggle-btn');
    if (langBtn) langBtn.addEventListener('click', function () { toggleLang(); });

    // Starter cards
    document.querySelectorAll('.starter-card').forEach(function (card) {
      card.addEventListener('click', function () {
        var p = card.getAttribute('data-prompt');
        if (p && !isGenerating) { userInput.value = p; handleSend(); }
      });
    });

    // Burger / Drawer
    burgerBtn.addEventListener('click', function () {
      if (drawer.classList.contains('open')) closeDrawer(); else openDrawer();
    });
    drawerOverlay.addEventListener('click', closeDrawer);
    drawerCloseBtn.addEventListener('click', closeDrawer);

    // Theme toggle
    if (themeBtn) {
      themeBtn.addEventListener('click', function () {
        document.body.classList.toggle('light-theme');
        var isLight = document.body.classList.contains('light-theme');
        themeBtn.querySelector('.theme-icon').textContent = isLight ? '☀️' : '🌙';
        themeBtn.querySelector('.theme-label').textContent = isLight ? 'Light Theme' : 'Dark Theme';
      });
    }

    if (newConsBtn) newConsBtn.addEventListener('click', function () { createNew(); closeDrawer(); });

    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        if (confirm('Clear all consultation history?')) {
          chats = { 'chat_1': { title: 'New Consultation', messages: [] } };
          currentChatId = 'chat_1';
          saveState(); renderMessages(); renderConsultList();
          closeDrawer();
        }
      });
    }

    if (exportBtn) exportBtn.addEventListener('click', function () { exportTranscript(); closeDrawer(); });
  }

  function createNew() {
    var newId = 'chat_' + Date.now();
    chats[newId] = { title: 'New Consultation', messages: [] };
    currentChatId = newId;
    saveState(); renderMessages(); renderConsultList();
    if (window.MedBot3D) window.MedBot3D.setRobotState('idle');
  }

  function renderConsultList() {
    if (!consultList) return;
    consultList.innerHTML = '';
    Object.keys(chats).forEach(function (id) {
      var chat    = chats[id];
      var isActive = (id === currentChatId);
      var item    = document.createElement('div');
      item.className = 'consultation-item' + (isActive ? ' active' : '');
      item.innerHTML =
        '<span>' + (isActive ? '▶ ' : '') + escHtml(chat.title) + '</span>' +
        '<button class="consultation-delete-btn" title="Delete">×</button>';
      item.addEventListener('click', function (e) {
        if (!e.target.classList.contains('consultation-delete-btn')) {
          currentChatId = id; saveState(); renderMessages(); renderConsultList(); closeDrawer();
        }
      });
      item.querySelector('.consultation-delete-btn').addEventListener('click', function (e) {
        e.stopPropagation();
        if (Object.keys(chats).length <= 1) { createNew(); return; }
        delete chats[id];
        currentChatId = Object.keys(chats)[0];
        saveState(); renderMessages(); renderConsultList();
      });
      consultList.appendChild(item);
    });
  }

  function renderMessages() {
    var chat = chats[currentChatId];
    if (!chat) return;
    viewport.innerHTML = '';
    starterContainer.classList.toggle('hidden', chat.messages.length > 0);
    chat.messages.forEach(function (msg) { appendBubble(msg.role, msg); });
    viewport.scrollTop = viewport.scrollHeight;
  }

  function appendBubble(role, msgData) {
    var bubble  = document.createElement('div');
    bubble.className = 'chat-bubble ' + role;

    var avatar  = document.createElement('div');
    avatar.className = 'bubble-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🩺';

    var content = document.createElement('div');
    content.className = 'bubble-content';

    if (role === 'user') {
      content.textContent = msgData.content;
    } else {
      if (msgData.refused) {
        content.innerHTML =
          '<div class="refusal-card">' +
            '<div class="refusal-badge">⚠️ Insufficient Evidence / Out of Scope</div>' +
            '<div class="refusal-text">' + escHtml(msgData.content) + '</div>' +
            '<div class="refusal-caption">Score (' + ((msgData.top_score || 0).toFixed(3)) +
              ') below safety threshold (0.50). Pre-generation gating prevented hallucination.</div>' +
          '</div>';
      } else {
        var html = '';
        if (msgData.top_score > 0) {
          var hi = msgData.top_score >= 0.65;
          html += '<div class="confidence-tag ' + (hi ? 'high' : 'moderate') + '">' +
            (hi ? '🟢 High' : '🟡 Moderate') + ' Confidence (' + msgData.top_score.toFixed(2) + ')</div>';
        }
        if (msgData.query_changed && msgData.enhanced_query) {
          html += '<div class="query-enhanced-banner">✏️ Enhanced: <em>' + escHtml(msgData.enhanced_query) + '</em></div>';
        }
        html += '<div>' + parseMarkdown(msgData.content) + '</div>';
        if (msgData.citations && msgData.citations.length > 0) {
          html += '<div class="citation-container"><span class="citation-label">Sources:</span>';
          msgData.citations.forEach(function (b) { html += '<span class="citation-badge">📄 ' + escHtml(b) + '</span>'; });
          html += '</div>';
        }
        if (msgData.retrieved_chunks && msgData.retrieved_chunks.length > 0) {
          html += '<div class="evidence-inspector">' +
            '<div class="evidence-header" onclick="this.nextElementSibling.style.display=(this.nextElementSibling.style.display===\'none\'?\'flex\':\'none\')">' +
            '<span>🔍 View Evidence (' + msgData.retrieved_chunks.length + ' Chunks)</span><span>▼</span></div>' +
            '<div class="evidence-body" style="display:none;">';
          msgData.retrieved_chunks.forEach(function (ch, idx) {
            var src  = DOC_NAMES[ch.document] || ch.document || 'Document';
            var pS   = ch.page_start || '?', pE = ch.page_end || '?';
            var pStr = pS === pE ? 'p.' + pS : 'p.' + pS + '-' + pE;
            var sc   = ch.similarity_score || 0;
            var pct  = Math.min(100, Math.max(0, Math.round(sc * 100)));
            html += '<div class="evidence-chunk-item">' +
              '<div class="evidence-chunk-meta"><span>#' + (idx + 1) + ' ' + escHtml(src) + ' (' + pStr + ')</span>' +
              '<span style="color:var(--accent-cyan)">' + sc.toFixed(3) + '</span></div>' +
              '<div class="match-meter-bar"><div class="match-meter-fill" style="width:' + pct + '%"></div></div>' +
              '<div class="evidence-chunk-snippet">' + escHtml((ch.text || '').substring(0, 200)) + '...</div>' +
              '</div>';
          });
          html += '</div></div>';
        }
        content.innerHTML = html;
      }
    }

    bubble.appendChild(avatar);
    bubble.appendChild(content);
    viewport.appendChild(bubble);
  }

  async function handleSend() {
    var query = userInput.value.trim();
    if (!query || isGenerating) return;

    // Stop any ongoing TTS before sending new query
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    ttsSpeaking = false;
    if (window.MedBot3D && window.MedBot3D.setLipSync) window.MedBot3D.setLipSync(false);

    var chat = chats[currentChatId];

    // Store original query (in user's language) for display
    var displayQuery = query;
    var englishQuery = query;

    // If Arabic mode: translate to English before sending to backend
    if (activeLang === 'ar') {
      if (window.MedBot3D) window.MedBot3D.setRobotState('searching');
      englishQuery = await translate(query, 'ar', 'en');
    }

    chat.messages.push({ role: 'user', content: displayQuery, dir: activeLang === 'ar' ? 'rtl' : 'ltr' });
    if (chat.title === 'New Consultation')
      chat.title = displayQuery.length > 28 ? displayQuery.substring(0, 28) + '...' : displayQuery;

    userInput.value = ''; userInput.style.height = 'auto';
    isGenerating = true; sendBtn.disabled = true;
    saveState(); renderMessages(); renderConsultList();
    if (window.MedBot3D) window.MedBot3D.setRobotState('searching');

    var history = chat.messages.slice(0, -1).map(function (m) { return { role: m.role, content: m.content }; });

    try {
      var res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: englishQuery, history: history })
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      var data = await res.json();

      var prose  = data.answer || '';
      var badges = [];
      if (!data.refused && data.query_type !== 'conversational') {
        var parsed = parseCitations(prose);
        prose  = parsed.cleanProse;
        badges = parsed.badges;
      }

      // If Arabic mode: translate English response back to Arabic for display + TTS
      var displayProse = prose;
      if (activeLang === 'ar' && !data.refused) {
        displayProse = await translate(prose, 'en', 'ar');
      }

      chat.messages.push({
        role: 'assistant', content: displayProse, refused: data.refused || false,
        top_score: data.top_score || 0, citations: badges,
        retrieved_chunks: data.retrieved_chunks || [],
        query_changed: data.query_changed || false,
        enhanced_query: data.enhanced_query || null,
        dir: activeLang === 'ar' ? 'rtl' : 'ltr'
      });
      saveState(); renderMessages();

      if (window.MedBot3D) {
        if (data.refused) {
          window.MedBot3D.setRobotState('caution');
          var refusalMsg = activeLang === 'ar'
            ? 'لا تتوفر لديّ أدلة كافية للإجابة على هذا السؤال.'
            : "I don't have enough grounded evidence to answer that question.";
          speakText(refusalMsg, activeLang);
          setTimeout(function () { window.MedBot3D.setRobotState('idle'); }, 4000);
        } else {
          window.MedBot3D.setRobotState('happy');
          speakText(displayProse, activeLang);
          setTimeout(function () {
            if (!ttsSpeaking && window.MedBot3D) window.MedBot3D.setRobotState('idle');
          }, 4500);
        }
      }
    } catch (err) {
      chat.messages.push({
        role: 'assistant', content: 'Error: ' + err.message + '. Ensure the FastAPI server is running.',
        refused: true, top_score: 0
      });
      saveState(); renderMessages();
      if (window.MedBot3D) window.MedBot3D.setRobotState('caution');
    } finally {
      isGenerating = false; sendBtn.disabled = false;
    }
  }

  function parseCitations(raw) {
    var re     = /\[Source:\s*(.*?)(?:,\s*Section:\s*(.*?))?,\s*Page:\s*([^\]]+)\]/g;
    var badges = [], seen = new Set(), m;
    while ((m = re.exec(raw)) !== null) {
      var label = (DOC_NAMES[m[1].trim()] || m[1].trim()) + ' · p.' + m[3].trim();
      if (!seen.has(label)) { seen.add(label); badges.push(label); }
    }
    return {
      cleanProse: raw.replace(re, '').replace(/ +([.,;])/g, '$1').replace(/ +/g, ' ').trim(),
      badges: badges
    };
  }

  function exportTranscript() {
    var chat = chats[currentChatId];
    if (!chat || chat.messages.length === 0) { alert('No messages to export.'); return; }
    var text = '# MedRetriv Clinical Consultation\nTitle: ' + chat.title + '\nDate: ' + new Date().toLocaleString() + '\n\n';
    chat.messages.forEach(function (m) { text += '[' + m.role.toUpperCase() + ']:\n' + m.content + '\n\n'; });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'text/markdown' }));
    a.download = 'MedRetriv_' + Date.now() + '.md'; a.click();
  }

  function parseMarkdown(md) {
    return md
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^\s*-\s+(.*)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
      .replace(/\n\n/g, '<br><br>');
  }

  function escHtml(s) {
    return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
});
