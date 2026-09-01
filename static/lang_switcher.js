/* Shubhlo Bulletproof Multi-Language Engine */
(function() {
  const DICTIONARY = {
    'en': {
      'Home': 'Home',
      'Services': 'Services',
      'Book Now': 'Book Now',
      'Contact': 'Contact',
      'Vendor': 'Vendor',
      'About': 'About',
      'Terms': 'Terms',
      'Login': 'Login',
      'Logout': 'Logout',
      'Dashboard': 'Dashboard',
      'Our Services': 'Our Services',
      'Plan Your Perfect Event': 'Plan Your Perfect Event'
    },
    'hi': {
      'Home': 'मुख्य पृष्ठ (Home)',
      'Services': 'सेवाएं (Services)',
      'Book Now': 'बुकिंग करें',
      'Contact': 'संपर्क करें',
      'Vendor': 'वेंडर लॉगिन',
      'About': 'हमारे बारे में',
      'Terms': 'नियम व शर्तें',
      'Login': 'लॉगिन',
      'Logout': 'लॉगआउट',
      'Dashboard': 'डैशबोर्ड',
      'Our Services': 'हमारी सेवाएं',
      'Plan Your Perfect Event': 'अपने सपनों का इवेंट प्लान करें'
    },
    'mr': {
      'Home': 'मुख्यपृष्ठ',
      'Services': 'सेवा',
      'Book Now': 'बुक करा',
      'Contact': 'संपर्क',
      'Vendor': 'व्हेंडर',
      'About': 'आमच्याबद्दल',
      'Terms': 'अटी व शर्ती',
      'Login': 'लॉगिन',
      'Logout': 'लॉगआउट',
      'Dashboard': 'डॅशबोर्ड'
    },
    'gu': {
      'Home': 'હોમ',
      'Services': 'સેવાઓ',
      'Book Now': 'બુક કરો',
      'Contact': 'સંપર્ક',
      'Vendor': 'વેન્ડર',
      'About': 'અમારા વિશે',
      'Terms': 'નિયમો અને શરતો'
    },
    'pa': {
      'Home': 'ਹੋਮ',
      'Services': 'ਸੇਵਾਵਾਂ',
      'Book Now': 'ਬੁੱਕ ਕਰੋ',
      'Contact': 'ਸੰਪਰਕ',
      'Vendor': 'ਵੈਂਡਰ',
      'About': 'ਸਾਡੇ ਬਾਰੇ'
    },
    'bn': {
      'Home': 'হোম',
      'Services': 'সেবাসমূহ',
      'Book Now': 'বুক করুন',
      'Contact': 'যোগাযোগ',
      'About': 'আমাদের সম্পর্কে'
    },
    'ta': {
      'Home': 'முகப்பு',
      'Services': 'சேவைகள்',
      'Book Now': 'முன்பதிவு செய்ய',
      'Contact': 'தொடர்பு கொள்ள'
    },
    'te': {
      'Home': 'హోమ్',
      'Services': 'సేవలు',
      'Book Now': 'బుక్ చేయండి',
      'Contact': 'సంప్రదించండి'
    },
    'kn': {
      'Home': 'ಮುಖಪುಟ',
      'Services': 'ಸೇವೆಗಳು',
      'Book Now': 'ಬುಕ್ ಮಾಡಿ',
      'Contact': 'ಸಂಪರ್ಕಿಸಿ'
    },
    'ml': {
      'Home': 'ഹോം',
      'Services': 'സേവനങ്ങൾ',
      'Book Now': 'ബുക്ക് ചെയ്യുക',
      'Contact': 'ബന്ധപ്പെടുക'
    }
  };

  function initEngine() {
    const savedLang = localStorage.getItem('shubhlo_lang') || 'en';
    
    // Sync all language dropdown selectors on page
    const selectors = document.querySelectorAll('.lang-selector-select');
    selectors.forEach(s => s.value = savedLang);

    // Apply dictionary translations
    applyDictionary(savedLang);

    // Load Google Translate script safely in background
    if (!document.getElementById('google-translate-script')) {
      const gtScript = document.createElement('script');
      gtScript.id = 'google-translate-script';
      gtScript.src = 'https://translate.google.com/translate_a/element.js?cb=shubhloTranslateInit';
      gtScript.async = true;
      document.head.appendChild(gtScript);
    }

    if (!document.getElementById('google_translate_element')) {
      const div = document.createElement('div');
      div.id = 'google_translate_element';
      div.style.display = 'none';
      document.body.appendChild(div);
    }
  }

  window.shubhloTranslateInit = function() {
    try {
      new google.translate.TranslateElement({
        pageLanguage: 'en',
        includedLanguages: 'en,hi,mr,gu,pa,bn,ta,te,kn,ml',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false
      }, 'google_translate_element');

      const savedLang = localStorage.getItem('shubhlo_lang');
      if (savedLang && savedLang !== 'en') {
        setTimeout(() => triggerGoogleCombo(savedLang), 500);
      }
    } catch(e) {
      console.log('Google translate init fallback:', e);
    }
  };

  function triggerGoogleCombo(langCode) {
    const combo = document.querySelector('.goog-te-combo');
    if (combo) {
      combo.value = langCode;
      combo.dispatchEvent(new Event('change'));
    }
  }

  function applyDictionary(langCode) {
    if (langCode === 'en' || !DICTIONARY[langCode]) return;

    const dict = DICTIONARY[langCode];
    const walkTextNodes = function(node) {
      if (node.nodeType === 3) {
        let text = node.nodeValue.trim();
        if (dict[text]) {
          node.nodeValue = node.nodeValue.replace(text, dict[text]);
        }
      } else if (node.nodeType === 1 && node.tagName !== 'SCRIPT' && node.tagName !== 'STYLE' && node.tagName !== 'SELECT') {
        for (let i = 0; i < node.childNodes.length; i++) {
          walkTextNodes(node.childNodes[i]);
        }
      }
    };

    walkTextNodes(document.body);
  }

  window.changeShubhloLanguage = function(langCode) {
    localStorage.setItem('shubhlo_lang', langCode);
    const selectors = document.querySelectorAll('.lang-selector-select');
    selectors.forEach(s => s.value = langCode);

    const combo = document.querySelector('.goog-te-combo');
    if (combo) {
      combo.value = langCode;
      combo.dispatchEvent(new Event('change'));
    } else {
      // Direct cookie set for Google Translate
      document.cookie = `googtrans=/en/${langCode}; path=/; domain=${location.hostname}`;
      document.cookie = `googtrans=/en/${langCode}; path=/;`;
      window.location.reload();
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEngine);
  } else {
    initEngine();
  }
})();
