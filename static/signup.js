// script.js

// States → Districts → Subdistricts data
const locationData = {
    "Madhya Pradesh": {
        "Bhopal": ["Huzur", "Kolar", "Berasia"],
        "Raisen": ["Bareli", "Gairatganj", "Silwani"],
        "Indore": ["Sanwer", "Depalpur", "Mhow"]
    },
    "Maharashtra": {
        "Pune": ["Haveli", "Mulshi", "Baramati"],
        "Nagpur": ["Kamptee", "Umred", "Katol"]
    },
    "Uttar Pradesh": {
        "Lucknow": ["Malihabad", "Bakshi Ka Talab"],
        "Varanasi": ["Pindra", "Sevapuri"]
    }
};

// Dropdown elements
const stateSelect = document.getElementById("state");
const districtSelect = document.getElementById("district");
const subdistrictSelect = document.getElementById("subdistrict");

// State change → fill districts
stateSelect.addEventListener("change", function() {
  districtSelect.innerHTML = "<option value=''>--Select District--</option>";
  subdistrictSelect.innerHTML = "<option value=''>--Select Sub-District--</option>";

  if (this.value && locationData[this.value]) {
    Object.keys(locationData[this.value]).forEach(district => {
      let opt = document.createElement("option");
      opt.value = district;
      opt.textContent = district;
      districtSelect.appendChild(opt);
    });
  }
});

// District change → fill subdistricts
districtSelect.addEventListener("change", function() {
  subdistrictSelect.innerHTML = "<option value=''>--Select Sub-District--</option>";
  const state = stateSelect.value;
  const district = this.value;

  if (state && district && locationData[state][district]) {
    locationData[state][district].forEach(tehsil => {
      let opt = document.createElement("option");
      opt.value = tehsil;
      opt.textContent = tehsil;
      subdistrictSelect.appendChild(opt);
    });
  }
});

// Form Submit
document.querySelector("form").addEventListener("submit", function(e) {
  e.preventDefault();
  alert("Form Submitted Successfully!");
});
