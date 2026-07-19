document.addEventListener("DOMContentLoaded", async () => {
  const statusBadge = document.getElementById("statusBadge");
  const urlDisplay = document.getElementById("urlDisplay");
  const scoreNumber = document.getElementById("scoreNumber");
  const meterFill = document.getElementById("meterFill");
  const confidenceBadge = document.getElementById("confidenceBadge");
  const explanationText = document.getElementById("explanationText");
  const featuresList = document.getElementById("featuresList");

  try {
    // Get active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab.url;

    // Display URL
    urlDisplay.textContent = url;

    // Show scanning state
    statusBadge.innerHTML = '<div class="status-dot"></div><span>Analyzing</span>';

    // Request analysis from background script
    chrome.runtime.sendMessage({ action: "check_url", url }, (response) => {
      if (!response || response.error) {
        // Error state
        statusBadge.innerHTML = '<div class="status-dot"></div><span style="color: #f59e0b;">Error</span>';
        scoreNumber.textContent = "—";
        explanationText.textContent = `Unable to analyze URL: ${response?.error || "Connection failed"}. Please ensure the Flask API server is running on http://localhost:5000`;
        featuresList.innerHTML = '<li>⚠️ API connection failed</li>';
        return;
      }

      const isPhishing = response.prediction === "phishing";
      const confidence = (response.confidence || response.phishing_probability || 0);
      const riskScore = isPhishing ? Math.round(confidence * 100) : Math.round((1 - confidence) * 100);

      // Update status badge
      if (isPhishing) {
        statusBadge.innerHTML = '<div class="status-dot" style="background: #ef4444;"></div><span class="status-danger">⚠️ Phishing</span>';
      } else {
        statusBadge.innerHTML = '<div class="status-dot" style="background: #22c55e;"></div><span class="status-safe">✓ Safe</span>';
      }

      // Update score display
      scoreNumber.textContent = riskScore;
      if (riskScore > 75) {
        scoreNumber.style.background = "linear-gradient(135deg, #ef4444, #dc2626)";
        scoreNumber.style.webkitBackgroundClip = "text";
        scoreNumber.style.webkitTextFillColor = "transparent";
      } else if (riskScore > 50) {
        scoreNumber.style.background = "linear-gradient(135deg, #f59e0b, #d97706)";
        scoreNumber.style.webkitBackgroundClip = "text";
        scoreNumber.style.webkitTextFillColor = "transparent";
      } else {
        scoreNumber.style.background = "linear-gradient(135deg, #22c55e, #16a34a)";
        scoreNumber.style.webkitBackgroundClip = "text";
        scoreNumber.style.webkitTextFillColor = "transparent";
      }

      // Animate meter fill
      setTimeout(() => {
        meterFill.style.width = `${riskScore}%`;
      }, 100);

      // Update confidence badge
      const confidencePercent = (confidence * 100).toFixed(1);
      const confidenceLevel = confidence > 0.9 ? "Very High" :
                            confidence > 0.75 ? "High" :
                            confidence > 0.6 ? "Medium" : "Low";
      confidenceBadge.textContent = `Confidence: ${confidencePercent}% (${confidenceLevel})`;

      // Display Llama 3.2 explanation with typing effect
      if (response.llama_explanation) {
        typeWriter(explanationText, response.llama_explanation, 20);
      } else {
        explanationText.textContent = "No explanation available from the AI model.";
      }

      // Display top features
      if (response.top_features && response.top_features.length > 0) {
        featuresList.innerHTML = response.top_features
          .map(feature => `<li>${feature}</li>`)
          .join('');
      } else {
        featuresList.innerHTML = '<li>No feature data available</li>';
      }

      // Store result for export
      window.lastAnalysis = {
        ...response,
        url,
        timestamp: new Date().toISOString(),
        risk_score: riskScore
      };
    });

  } catch (error) {
    console.error("Popup error:", error);
    statusBadge.innerHTML = '<div class="status-dot"></div><span style="color: #ef4444;">Error</span>';
    scoreNumber.textContent = "!";
    explanationText.textContent = `Error: ${error.message}`;
  }
});

// Typewriter effect for explanation
function typeWriter(element, text, speed = 30) {
  element.textContent = "";
  let i = 0;
  
  function type() {
    if (i < text.length) {
      element.textContent += text.charAt(i);
      i++;
      setTimeout(type, speed);
    }
  }
  
  type();
}

// Refresh button
document.getElementById("refreshBtn")?.addEventListener("click", () => {
  location.reload();
});

// Export button
document.getElementById("exportBtn")?.addEventListener("click", () => {
  if (!window.lastAnalysis) {
    alert("No analysis data to export");
    return;
  }

  const data = JSON.stringify(window.lastAnalysis, null, 2);
  const blob = new Blob([data], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement("a");
  a.href = url;
  a.download = `phishlens-analysis-${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  
  URL.revokeObjectURL(url);

  // Visual feedback
  const btn = document.getElementById("exportBtn");
  const originalText = btn.textContent;
  btn.textContent = "✓ Exported";
  setTimeout(() => {
    btn.textContent = originalText;
  }, 2000);
});

// Keyboard shortcuts
document.addEventListener("keydown", (e) => {
  if (e.key === "r" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    location.reload();
  }
  if (e.key === "e" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    document.getElementById("exportBtn")?.click();
  }
});
