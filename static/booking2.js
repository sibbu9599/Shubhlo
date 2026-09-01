// Object to store prices of selected services
const selectedPrices = {
  venue: 0,
  catering: 0,
  dj: 0,
  decoration: 0,
  transport: 0,
  photography: 0,
  shahi_sawari: 0,
  invitation_card: 0,
  security_guard: 0,
  makeup: 0,
  mehendi: 0,
  dhol_band: 0,
  choreographer: 0,
  anchor: 0,
  fireworks: 0
};

// Select a vendor card
function selectVendor(category, name, price, cardElement) {
  const hiddenInput = document.getElementById(category);
  const currentSelected = hiddenInput.value;

  // Toggle selection
  if (currentSelected === name) {
    hiddenInput.value = "";
    cardElement.classList.remove("selected");
    cardElement.querySelector(".badge").textContent = "Select";
    selectedPrices[category] = 0;
    updateSummary(category, "Not Selected", 0);
  } else {
    // Remove selection from all cards in the same category
    const siblingCards = cardElement.parentElement.querySelectorAll(".vendor-card");
    siblingCards.forEach(card => {
      card.classList.remove("selected");
      card.querySelector(".badge").textContent = "Select";
    });

    // Select the clicked card
    hiddenInput.value = name;
    cardElement.classList.add("selected");
    cardElement.querySelector(".badge").textContent = "✓ Selected";
    selectedPrices[category] = price;

    // Get location metadata
    const state = cardElement.getAttribute("data-state") || "";
    const district = cardElement.getAttribute("data-district") || "";
    const tehsil = cardElement.getAttribute("data-tehsil") || "";

    updateSummary(category, name, price, state, district, tehsil);
  }

  // Update total price display
  updateTotal();
}

// Update the booking summary panel details
function updateSummary(category, name, price, state, district, tehsil) {
  const summaryItem = document.getElementById(`summary-${category}`);
  if (summaryItem) {
    const valueSpan = summaryItem.querySelector(".item-value");
    if (name === "Not Selected") {
      valueSpan.innerHTML = `Not Selected`;
      valueSpan.style.color = "#7f8c8d";
    } else {
      let locHtml = "";
      if (tehsil) {
        locHtml = `<br><span style="font-size: 11px; color: #8e44ad; font-weight: 500; display: inline-flex; align-items: center; gap: 3px; margin-top: 3px;">📍 ${tehsil}, ${district}</span>`;
      }
      valueSpan.innerHTML = `<strong style="color: #2c3e50;">${name}</strong> <span style="color: #27ae60; font-weight: 600;">(Token: ₹5,118)</span>${locHtml}`;
    }
  }
}

// Calculate and display Token Advance & Estimated Full Event Cost vs Target Budget
function updateTotal() {
  const selectedCount = Object.values(selectedPrices).filter(p => p > 0).length;
  const tokenAdvance = selectedCount * 5118;
  const totalDisplay = document.getElementById("total-price-display");
  if (totalDisplay) {
    totalDisplay.textContent = `₹${tokenAdvance.toLocaleString()}`;
  }

  // Calculate total full cost of selected services
  const estFullCost = Object.values(selectedPrices).reduce((sum, val) => sum + val, 0);
  const estCostDisplay = document.getElementById("est-total-cost");
  if (estCostDisplay) {
    estCostDisplay.textContent = `₹${estFullCost.toLocaleString()}`;
  }

  // Budget warning check
  const budgetContainer = document.getElementById("target-budget-container");
  const warningBox = document.getElementById("budget-warning-box");

  if (budgetContainer && warningBox) {
    const targetBudget = parseFloat(budgetContainer.getAttribute("data-target-budget") || 0);

    if (targetBudget > 0 && estFullCost > 0) {
      if (estFullCost > targetBudget) {
        const diff = estFullCost - targetBudget;
        warningBox.style.display = "block";
        warningBox.style.background = "#fff3cd";
        warningBox.style.border = "1px solid #ffe8a1";
        warningBox.style.color = "#856404";
        warningBox.innerHTML = `
          <strong>⚠️ Budget Notice / बजट सूचना:</strong><br>
          Selected total (₹${estFullCost.toLocaleString()}) is <strong>₹${diff.toLocaleString()} above</strong> your target budget (₹${targetBudget.toLocaleString()}).<br>
          <span style="font-size: 11px; margin-top: 4px; display: inline-block;">
            💡 <em>Don't worry! Your vendors can send custom proposals to adjust package costs for you. / चिंता न करें! वेंडर आपके बजट अनुसार कस्टम पैकेज ऑफर दे सकते हैं।</em>
          </span>
        `;
      } else {
        warningBox.style.display = "block";
        warningBox.style.background = "#d4edda";
        warningBox.style.border = "1px solid #c3e6cb";
        warningBox.style.color = "#155724";
        warningBox.innerHTML = `
          <strong>✅ Fits Your Budget / बजट के अंदर:</strong><br>
          Selected services (₹${estFullCost.toLocaleString()}) are within your ₹${targetBudget.toLocaleString()} target budget! / आपकी चुनी गई सेवाएं आपके बजट में हैं।
        `;
      }
    } else {
      warningBox.style.display = "none";
    }
  }
}

// Populate Full Price labels, Min Order Limits, and dynamic Budget Match Badges on all vendor cards
function initVendorBudgetBadges() {
  const budgetContainer = document.getElementById("target-budget-container");
  const targetBudget = budgetContainer ? parseFloat(budgetContainer.getAttribute("data-target-budget") || 0) : 0;
  
  const cards = document.querySelectorAll(".vendor-card");
  cards.forEach(card => {
    const price = parseFloat(card.getAttribute("data-price") || 0);
    const minOrder = parseFloat(card.getAttribute("data-min-order") || 0);
    const fullPriceTag = card.querySelector(".full-price-tag");
    const badgeContainer = card.querySelector(".budget-badge-container");

    if (fullPriceTag) {
      let minOrderStr = minOrder > 0 ? ` | Min: ₹${minOrder.toLocaleString()}` : '';
      if (price > 0) {
        fullPriceTag.textContent = `Rate: ₹${price.toLocaleString()}${minOrderStr}`;
      } else {
        fullPriceTag.textContent = `Rate: Negotiable / बातचीत योग्य${minOrderStr}`;
      }
    }

    if (badgeContainer) {
      let badgesHtml = '';
      if (minOrder > 0 && targetBudget > 0 && targetBudget < minOrder) {
        badgesHtml += `<span style="background: #fdf2e9; color: #e67e22; border: 1px solid #f39c12; font-size: 10.5px; padding: 2px 7px; border-radius: 12px; font-weight: bold; display: inline-block; margin-right: 4px;">🏷️ Below Min Order (₹${minOrder.toLocaleString()})</span>`;
      }
      
      if (targetBudget > 0) {
        if (price > 0 && price <= targetBudget) {
          badgesHtml += `<span style="background: #eafaf1; color: #27ae60; border: 1px solid #2ecc71; font-size: 10.5px; padding: 2px 7px; border-radius: 12px; font-weight: bold; display: inline-block;">🟢 Fits Budget</span>`;
        } else if (price > targetBudget) {
          const over = price - targetBudget;
          badgesHtml += `<span style="background: #fef9e7; color: #d68910; border: 1px solid #f1c40f; font-size: 10.5px; padding: 2px 7px; border-radius: 12px; font-weight: bold; display: inline-block;">⚠️ +₹${over.toLocaleString()} Over Budget</span>`;
        }
      }
      
      if (badgesHtml) {
        badgeContainer.innerHTML = badgesHtml;
      }
    }
  });
}

// Filter vendors dynamically by name, description, and budget checkbox
function filterVendors() {
  const query = document.getElementById("vendorSearch").value.toLowerCase();
  const budgetFilterCheckbox = document.getElementById("budgetOnlyFilter");
  const isBudgetOnly = budgetFilterCheckbox ? budgetFilterCheckbox.checked : false;

  const budgetContainer = document.getElementById("target-budget-container");
  const targetBudget = budgetContainer ? parseFloat(budgetContainer.getAttribute("data-target-budget") || 0) : 0;

  const cards = document.querySelectorAll(".vendor-card");

  cards.forEach(card => {
    const name = card.getAttribute("data-name").toLowerCase();
    const desc = card.getAttribute("data-description").toLowerCase();
    const price = parseFloat(card.getAttribute("data-price") || 0);

    const matchesQuery = name.includes(query) || desc.includes(query);
    const matchesBudget = !isBudgetOnly || (targetBudget > 0 && price <= targetBudget);

    if (matchesQuery && matchesBudget) {
      card.style.display = "flex";
    } else {
      card.style.display = "none";
    }
  });

  // Dynamically hide category section headers if all cards inside them are hidden
  const categories = ["venue", "catering", "dj", "decoration", "transport", "photography", "shahi_sawari", "invitation_card", "security_guard", "makeup", "mehendi", "dhol_band", "choreographer", "wedding_planner", "anchor", "fireworks"];
  categories.forEach(cat => {
    const section = document.getElementById(`category-${cat}-section`);
    if (section) {
      const allCards = section.querySelectorAll(`.vendor-card`);
      let visibleCount = 0;
      allCards.forEach(c => {
        if (c.style.display !== "none") visibleCount++;
      });

      if (visibleCount === 0 && allCards.length > 0) {
        section.style.display = "none";
      } else {
        section.style.display = "block";
      }
    }
  });
}

// Form validation and budget init on load
document.addEventListener("DOMContentLoaded", function () {
  initVendorBudgetBadges();

  const form = document.getElementById("serviceForm");
  if (form) {
    form.addEventListener("submit", function (e) {
      const categories = ['venue', 'catering', 'dj', 'decoration', 'transport', 'photography', 'shahi_sawari', 'invitation_card', 'security_guard', 'makeup', 'mehendi', 'dhol_band', 'choreographer', 'wedding_planner', 'anchor', 'fireworks'];
      let anySelected = false;
      for (const cat of categories) {
        const el = document.getElementById(cat);
        if (el && el.value && el.value.trim() !== "") {
          anySelected = true;
          break;
        }
      }
      if (!anySelected) {
        alert("❌ आगे बढ़ने के लिए कृपया कम से कम एक सेवा या वेंडर अवश्य चुनें! / Please select AT LEAST 1 service or vendor to proceed!");
        e.preventDefault();
        window.scrollTo({ top: 250, behavior: 'smooth' });
        return false;
      }
    });
  }
});
