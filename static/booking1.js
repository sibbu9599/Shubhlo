document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("bookingForm");
  const stateSelect = document.getElementById("state");
  const districtSelect = document.getElementById("district");
  const tehsilSelect = document.getElementById("tehsil");

  // Fetch allowed locations dynamically from backend API
  let locationData = {};

  fetch('/api/allowed-locations')
    .then(response => response.json())
    .then(allowedData => {
      locationData = allowedData;
      
      // Populate States dynamically
      stateSelect.innerHTML = '<option value="">Select State</option>';
      Object.keys(locationData).sort().forEach(state => {
        const option = document.createElement("option");
        option.value = state;
        option.textContent = state;
        stateSelect.appendChild(option);
      });
    })
    .catch(err => {
      console.error("Error loading permitted locations, falling back:", err);
      locationData = window.locationData || {};
    });

  // Populate districts when State changes
  stateSelect.addEventListener("change", function () {
    const state = this.value;
    districtSelect.innerHTML = '<option value="">Select District</option>';
    tehsilSelect.innerHTML = '<option value="">Select Tehsil</option>';

    if (state && locationData[state]) {
      Object.keys(locationData[state]).sort().forEach(district => {
        const option = document.createElement("option");
        option.value = district;
        option.textContent = district;
        districtSelect.appendChild(option);
      });
    }
  });

  // Populate tehsils when District changes
  districtSelect.addEventListener("change", function () {
    const state = stateSelect.value;
    const district = this.value;
    tehsilSelect.innerHTML = '<option value="">Select Tehsil</option>';

    if (state && district && locationData[state][district]) {
      locationData[state][district].sort().forEach(tehsil => {
        const option = document.createElement("option");
        option.value = tehsil;
        option.textContent = tehsil;
        tehsilSelect.appendChild(option);
      });
    }
  });

  // Form submission validation
  form.addEventListener("submit", function (event) {
    const inputs = form.querySelectorAll("input, textarea, select");
    let valid = true;

    inputs.forEach(input => {
      if (!input.checkValidity()) {
        valid = false;
        input.classList.add("invalid");
        input.classList.remove("valid");
      } else {
        input.classList.add("valid");
        input.classList.remove("invalid");
      }
    });

    if (!valid) {
      event.preventDefault(); // stop form submit
      alert("❌ कृपया सभी विवरण सही भरें!");
    }
  });
});
