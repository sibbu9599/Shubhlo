// Shubhlo Booking Step 2 - Interactive Vendor Selection & Live Summary Engine
const ALL_CATEGORIES = [
  'venue', 'catering', 'dj', 'decoration', 'transport', 'photography',
  'shahi_sawari', 'invitation_card', 'security_guard', 'makeup', 'mehendi',
  'dhol_band', 'pandit', 'choreographer', 'wedding_planner', 'anchor',
  'fireworks', 'mocktail', 'safa'
];

// Object to store prices of selected services
const selectedPrices = {};
ALL_CATEGORIES.forEach(cat => { selectedPrices[cat] = 0; });

// Select or unselect a vendor card
function selectVendor(category, name, price, cardElement) {
  if (!cardElement) return;

  // Prevent selecting blocked vendors
  if (cardElement.classList.contains("blocked-vendor-card") || cardElement.getAttribute("data-blocked") === "true") {
    alert("यह वेंडर इस तारीख को पहले से बुक या व्यस्त है। कृपया कोई अन्य वेंडर चुनें। / This vendor is already booked/busy on the selected date. Please choose another vendor.");
    return;
  }

  const hiddenInput = document.getElementById(category);
  if (!hiddenInput) return;
  const currentSelected = hiddenInput.value;

  // Toggle selection
  if (currentSelected === name) {
    hiddenInput.value = "";
    cardElement.classList.remove("selected");
    const badge = cardElement.querySelector(".badge");
    if (badge) badge.textContent = "Select";
    selectedPrices[category] = 0;
    updateSummary(category, "Not Selected", 0);
  } else {
    // Remove selection from all sibling cards in the same category block
    const parentGrid = cardElement.closest(".cards-grid");
    if (parentGrid) {
      parentGrid.querySelectorAll(".vendor-card").forEach(card => {
        card.classList.remove("selected");
        const b = card.querySelector(".badge");
        if (b) b.textContent = "Select";
      });
    }

    // Select the clicked card
    hiddenInput.value = name;
    cardElement.classList.add("selected");
    const badge = cardElement.querySelector(".badge");
    if (badge) badge.textContent = "✓ Selected";
    selectedPrices[category] = parseFloat(price) || 0;

    // Get location metadata
    const state = cardElement.getAttribute("data-state") || "";
    const district = cardElement.getAttribute("data-district") || "";
    const tehsil = cardElement.getAttribute("data-tehsil") || "";

    updateSummary(category, name, price, state, district, tehsil);
  }

  // Update total price display and counter
  updateTotal();
}

// Remove a selection directly from the summary sidebar
function removeSelectionFromSummary(category) {
  const hiddenInput = document.getElementById(category);
  if (hiddenInput) {
    hiddenInput.value = "";
  }
  selectedPrices[category] = 0;

  // Deselect matching card in catalog
  const section = document.getElementById(`category-${category}-section`);
  if (section) {
    section.querySelectorAll(".vendor-card.selected").forEach(card => {
      card.classList.remove("selected");
      const b = card.querySelector(".badge");
      if (b) b.textContent = "Select";
    });
  }

  updateSummary(category, "Not Selected", 0);
  updateTotal();
}

// Update the booking summary panel details
function updateSummary(category, name, price, state, district, tehsil) {
  const summaryItem = document.getElementById(`summary-${category}`);
  if (!summaryItem) return;

  const valueSpan = summaryItem.querySelector(".item-value");
  if (!valueSpan) return;

  if (name === "Not Selected") {
    summaryItem.classList.remove("item-has-selection");
    valueSpan.innerHTML = `<span class="unselected-text">Not Selected</span>`;
  } else {
    summaryItem.classList.add("item-has-selection");
    let locHtml = "";
    if (tehsil) {
      locHtml = `<span class="summary-loc-tag">📍 ${tehsil}</span>`;
    }
    valueSpan.innerHTML = `
      <div class="summary-chosen-wrap">
        <span class="chosen-name">✓ ${name}</span>
        ${locHtml}
        <button type="button" class="btn-remove-item" onclick="removeSelectionFromSummary('${category}')" title="Remove choice">✕</button>
      </div>
    `;
  }
}

// Calculate and display Token Advance & Estimated Full Event Cost vs Target Budget
function updateTotal() {
  const selectedKeys = Object.keys(selectedPrices).filter(k => {
    const el = document.getElementById(k);
    return el && el.value && el.value.trim() !== "";
  });

  const selectedCount = selectedKeys.length;
  const tokenAdvance = selectedCount * 5118;

  // Update total display
  const totalDisplay = document.getElementById("total-price-display");
  if (totalDisplay) {
    totalDisplay.textContent = `₹${tokenAdvance.toLocaleString('en-IN')}`;
  }

  // Update counter badge
  const counterBadge = document.getElementById("selected-counter-badge");
  if (counterBadge) {
    counterBadge.textContent = `${selectedCount} / ${ALL_CATEGORIES.length} Selected`;
    if (selectedCount > 0) {
      counterBadge.classList.add("active-count");
    } else {
      counterBadge.classList.remove("active-count");
    }
  }

  // Update sidebar button pulse
  const sidebarBtn = document.getElementById("sidebarSubmitBtn");
  if (sidebarBtn) {
    if (selectedCount > 0) {
      sidebarBtn.classList.add("btn-ready");
      sidebarBtn.innerHTML = `<span>Proceed to Confirm & Pay (${selectedCount}) ➔</span>`;
    } else {
      sidebarBtn.classList.remove("btn-ready");
      sidebarBtn.innerHTML = `<span>Confirm Choices & Pay ➔</span>`;
    }
  }

  // Calculate total full cost of selected services
  const estFullCost = selectedKeys.reduce((sum, key) => sum + (selectedPrices[key] || 0), 0);
  const estCostDisplay = document.getElementById("est-total-cost");
  if (estCostDisplay) {
    estCostDisplay.textContent = `₹${estFullCost.toLocaleString('en-IN')}`;
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
        warningBox.style.border = "1.5px solid #ffe8a1";
        warningBox.style.color = "#856404";
        warningBox.innerHTML = `
          <strong>⚠️ Budget Notice / बजट सूचना:</strong><br>
          Selected total (₹${estFullCost.toLocaleString('en-IN')}) is <strong>₹${diff.toLocaleString('en-IN')} above</strong> your target budget (₹${targetBudget.toLocaleString('en-IN')}).<br>
          <span style="font-size: 11.5px; margin-top: 4px; display: inline-block;">
            💡 <em>Don't worry! Your vendors can send custom proposals to adjust package costs for you.</em>
          </span>
        `;
      } else {
        warningBox.style.display = "block";
        warningBox.style.background = "#d4edda";
        warningBox.style.border = "1.5px solid #c3e6cb";
        warningBox.style.color = "#155724";
        warningBox.innerHTML = `
          <strong>✅ Fits Your Budget / बजट के अंदर:</strong><br>
          Selected services (₹${estFullCost.toLocaleString('en-IN')}) are within your ₹${targetBudget.toLocaleString('en-IN')} target budget!
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
      let minOrderStr = minOrder > 0 ? ` | Min: ₹${minOrder.toLocaleString('en-IN')}` : '';
      if (price > 0) {
        fullPriceTag.textContent = `Rate: ₹${price.toLocaleString('en-IN')}${minOrderStr}`;
      } else {
        fullPriceTag.textContent = `Rate: Negotiable / बातचीत योग्य${minOrderStr}`;
      }
    }

    if (badgeContainer) {
      let badgesHtml = '';
      if (minOrder > 0 && targetBudget > 0 && targetBudget < minOrder) {
        badgesHtml += `<span style="background: #fdf2e9; color: #e67e22; border: 1px solid #f39c12; font-size: 10.5px; padding: 2px 7px; border-radius: 12px; font-weight: bold; display: inline-block; margin-right: 4px;">🏷️ Below Min Order (₹${minOrder.toLocaleString('en-IN')})</span>`;
      }

      if (targetBudget > 0) {
        if (price > 0 && price <= targetBudget) {
          badgesHtml += `<span style="background: #eafaf1; color: #27ae60; border: 1px solid #2ecc71; font-size: 10.5px; padding: 2px 7px; border-radius: 12px; font-weight: bold; display: inline-block;">🟢 Fits Budget</span>`;
        } else if (price > targetBudget) {
          const over = price - targetBudget;
          badgesHtml += `<span style="background: #fef9e7; color: #d68910; border: 1px solid #f1c40f; font-size: 10.5px; padding: 2px 7px; border-radius: 12px; font-weight: bold; display: inline-block;">⚠️ +₹${over.toLocaleString('en-IN')} Over Budget</span>`;
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
  const inputEl = document.getElementById("vendorSearch");
  const query = (inputEl ? inputEl.value : "").toLowerCase().trim();
  const clearBtn = document.getElementById("searchClearBtn");

  if (clearBtn) {
    clearBtn.style.display = query.length > 0 ? "inline-flex" : "none";
  }

  const budgetFilterCheckbox = document.getElementById("budgetOnlyFilter");
  const isBudgetOnly = budgetFilterCheckbox ? budgetFilterCheckbox.checked : false;

  const budgetContainer = document.getElementById("target-budget-container");
  const targetBudget = budgetContainer ? parseFloat(budgetContainer.getAttribute("data-target-budget") || 0) : 0;

  const cards = document.querySelectorAll(".vendor-card");

  cards.forEach(card => {
    const name = (card.getAttribute("data-name") || "").toLowerCase();
    const desc = (card.getAttribute("data-description") || "").toLowerCase();
    const price = parseFloat(card.getAttribute("data-price") || 0);

    const matchesQuery = !query || name.includes(query) || desc.includes(query);
    const matchesBudget = !isBudgetOnly || (targetBudget > 0 && price <= targetBudget);

    if (matchesQuery && matchesBudget) {
      card.style.display = "flex";
    } else {
      card.style.display = "none";
    }
  });

  // Dynamically hide category section headers if all cards inside them are hidden
  ALL_CATEGORIES.forEach(cat => {
    const section = document.getElementById(`category-${cat}-section`);
    if (section) {
      const allCards = section.querySelectorAll(`.vendor-card`);
      let visibleCount = 0;
      allCards.forEach(c => {
        if (c.style.display !== "none") visibleCount++;
      });

      if (visibleCount === 0 && allCards.length > 0 && query.length > 0) {
        section.style.display = "none";
      } else {
        section.style.display = "block";
      }
    }
  });
}

// Clear vendor search input
function clearVendorSearch() {
  const inputEl = document.getElementById("vendorSearch");
  if (inputEl) {
    inputEl.value = "";
  }
  filterVendors();
}

// Smooth scroll to category from quick chips
function scrollToCategory(catId) {
  const el = document.getElementById(catId);
  if (el) {
    const offset = 85;
    const bodyRect = document.body.getBoundingClientRect().top;
    const elementRect = el.getBoundingClientRect().top;
    const elementPosition = elementRect - bodyRect;
    const offsetPosition = elementPosition - offset;

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
  }
}

// Form validation and budget init on load
document.addEventListener("DOMContentLoaded", function () {
  initVendorBudgetBadges();
  updateTotal();

  const form = document.getElementById("serviceForm");
  if (form) {
    form.addEventListener("submit", function (e) {
      let anySelected = false;
      for (const cat of ALL_CATEGORIES) {
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
