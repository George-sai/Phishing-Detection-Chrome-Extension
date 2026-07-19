// PhishLens Background Service Worker
// Integrates with Flask API backend for XGBoost + Llama 3.2 predictions

const API_URL = "http://localhost:5000/predict"; // Your Flask API endpoint
const CACHE_TTL = 1000 * 60 * 5; // 5 minutes cache

// In-memory cache
const cache = {};

// Extract domain from URL
function domainFromUrl(url) {
  try {
    const u = new URL(url);
    return u.hostname;
  } catch (e) { 
    return null; 
  }
}

// Call Flask API for prediction + Llama explanation
async function checkUrl(url) {
  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data;
    
  } catch (error) {
    console.error("PhishLens API error:", error);
    return {
      error: error.message,
      prediction: "unknown"
    };
  }
}

// Monitor navigation and auto-check URLs
chrome.webNavigation.onCommitted.addListener(async (details) => {
  // Only check top-level frames
  if (details.frameId !== 0) return;
  
  const url = details.url;
  
  // Skip non-HTTP(S) URLs
  if (!url || !url.startsWith("http")) return;

  const domain = domainFromUrl(url);
  if (!domain) return;

  // Check cache first
  const now = Date.now();
  if (cache[domain] && (now - cache[domain].timestamp < CACHE_TTL)) {
    handleDecision(details.tabId, url, cache[domain]);
    return;
  }

  // Call API
  const result = await checkUrl(url);
  
  // Cache the result
  cache[domain] = {
    ...result,
    timestamp: Date.now()
  };
  
  // Persist to storage
  chrome.storage.local.set({ phish_cache: cache });
  
  // Handle the decision
  handleDecision(details.tabId, url, result);
  
}, { url: [{ schemes: ["http", "https"] }] });

// Restore cache on startup
chrome.runtime.onStartup.addListener(() => {
  chrome.storage.local.get(["phish_cache"], (items) => {
    if (items.phish_cache) {
      Object.assign(cache, items.phish_cache);
    }
  });
});

// Handle prediction and show warnings
function handleDecision(tabId, url, data) {
  const isPhishing = data.prediction === "phishing";
  const confidence = data.confidence || data.phishing_probability || 0;
  
  // High-confidence phishing detection
  if (isPhishing && confidence >= 0.75) {
    // Show notification
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icon.png",
      title: "⚠️ PhishLens Warning",
      message: `Suspicious site detected (${(confidence * 100).toFixed(0)}% confidence)`,
      priority: 2
    });

    // Inject warning overlay with Llama explanation
    injectWarningOverlay(tabId, url, data);
  }
  
  // Update badge
  updateBadge(tabId, isPhishing, confidence);
}

// Inject warning overlay into page
function injectWarningOverlay(tabId, url, data) {
  const explanation = data.llama_explanation || "This URL has been flagged as potentially dangerous.";
  const confidence = ((data.confidence || 0) * 100).toFixed(0);
  const topFeatures = data.top_features || [];
  
  const overlayHtml = `
    <div id="phishlens-overlay" style="
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.85);
      z-index: 2147483647;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    ">
      <div style="
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        padding: 40px;
        border-radius: 16px;
        max-width: 600px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(255, 0, 0, 0.3);
        border: 2px solid #ff4444;
      ">
        <div style="text-align: center; margin-bottom: 30px;">
          <div style="
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #ff4444, #cc0000);
            border-radius: 50%;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            box-shadow: 0 10px 30px rgba(255, 68, 68, 0.3);
          ">⚠️</div>
          <h1 style="
            color: #ff4444;
            font-size: 28px;
            margin: 0 0 10px 0;
            font-weight: 700;
          ">Phishing Warning</h1>
          <p style="
            color: #ff6666;
            font-size: 14px;
            margin: 0;
            font-weight: 600;
          ">Confidence: ${confidence}%</p>
        </div>

        <div style="
          background: rgba(255, 68, 68, 0.1);
          border-left: 4px solid #ff4444;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 25px;
        ">
          <h3 style="
            color: #ffffff;
            font-size: 16px;
            margin: 0 0 15px 0;
            font-weight: 600;
          ">🤖 AI Analysis</h3>
          <p style="
            color: #cccccc;
            font-size: 14px;
            line-height: 1.6;
            margin: 0;
          ">${explanation}</p>
        </div>

        ${topFeatures.length > 0 ? `
        <div style="margin-bottom: 25px;">
          <h3 style="
            color: #ffffff;
            font-size: 14px;
            margin: 0 0 12px 0;
            font-weight: 600;
          ">🔍 Key Indicators:</h3>
          <ul style="
            color: #aaaaaa;
            font-size: 13px;
            margin: 0;
            padding-left: 20px;
            line-height: 1.8;
          ">
            ${topFeatures.map(f => `<li>${f}</li>`).join('')}
          </ul>
        </div>
        ` : ''}

        <div style="
          padding: 15px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          margin-bottom: 25px;
        ">
          <p style="
            color: #999999;
            font-size: 12px;
            margin: 0;
            word-break: break-all;
          "><strong style="color: #cccccc;">URL:</strong> ${url}</p>
        </div>

        <div style="display: flex; gap: 15px;">
          <button id="phishlens-close" style="
            flex: 1;
            background: #ff4444;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
          " onmouseover="this.style.background='#ff6666'" onmouseout="this.style.background='#ff4444'">
            🛡️ Close Tab (Recommended)
          </button>
          <button id="phishlens-continue" style="
            flex: 1;
            background: rgba(255, 255, 255, 0.1);
            color: #cccccc;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
          " onmouseover="this.style.background='rgba(255,255,255,0.15)'" onmouseout="this.style.background='rgba(255,255,255,0.1)'">
            Continue Anyway
          </button>
        </div>

        <p style="
          text-align: center;
          color: #666666;
          font-size: 11px;
          margin: 20px 0 0 0;
        ">Protected by PhishLens AI • Powered by Llama 3.2</p>
      </div>
    </div>
  `;

  try {
    chrome.scripting.executeScript({
      target: { tabId },
      func: (html) => {
        if (!document.getElementById('phishlens-overlay')) {
          const container = document.createElement('div');
          container.innerHTML = html;
          document.body.appendChild(container.firstElementChild);
          
          // Event listeners
          document.getElementById('phishlens-close').onclick = () => {
            chrome.runtime.sendMessage({ action: 'close_tab' });
          };
          
          document.getElementById('phishlens-continue').onclick = () => {
            document.getElementById('phishlens-overlay').remove();
          };
        }
      },
      args: [overlayHtml]
    }).catch(err => console.error("Failed to inject overlay:", err));
  } catch (error) {
    console.error("Injection error:", error);
  }
}

// Update extension badge
function updateBadge(tabId, isPhishing, confidence) {
  if (isPhishing) {
    chrome.action.setBadgeText({ text: "!", tabId });
    chrome.action.setBadgeBackgroundColor({ color: "#ff4444", tabId });
  } else {
    chrome.action.setBadgeText({ text: "✓", tabId });
    chrome.action.setBadgeBackgroundColor({ color: "#4CAF50", tabId });
  }
}

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'check_url') {
    const url = message.url;
    const domain = domainFromUrl(url);
    
    // Check cache first
    if (domain && cache[domain]) {
      sendResponse(cache[domain]);
    } else {
      // Fetch from API
      checkUrl(url).then(result => {
        if (domain) {
          cache[domain] = { ...result, timestamp: Date.now() };
          chrome.storage.local.set({ phish_cache: cache });
        }
        sendResponse(result);
      }).catch(error => {
        sendResponse({ error: error.message, prediction: "unknown" });
      });
      return true; // Keep channel open for async response
    }
  }
  
  if (message.action === 'close_tab' && sender.tab) {
    chrome.tabs.remove(sender.tab.id);
  }
});

console.log("✅ PhishLens background service worker loaded");
