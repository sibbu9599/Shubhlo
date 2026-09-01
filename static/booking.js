// Location data: State → District → Tehsil → City
const locationData = {
  "Madhya Pradesh": {
    "Hoshangabad/Narmadapuram": {
      "Itarsi": ["Ward 1", "Ward 2"],
      "Sohagpur": ["Village A", "Village B"]
    },
    "Hoshangabad": {
      "Itarsi": ["Ward 1", "Ward 2"],
      "Sohagpur": ["Village A", "Village B"]
    },
    "Bhopal": {
      "Berasia": ["City Center", "Old Town"],
      "Kolar": ["Village X", "Village Y"]
    }
  },
  "Maharashtra": {
    "Pune": {
      "Haveli": ["Shivaji Nagar", "Kothrud"],
      "Mulshi": ["Village P", "Village Q"]
    },
    "Mumbai": {
      "Andheri": ["East", "West"],
      "Borivali": ["East", "West"]
    }
  }
};

// Tehsil → Services mapping
const serviceData = {
  "Itarsi": ["Venue", "Catering", "DJ"],
  "Sohagpur": ["Venue", "Camera", "Transport"],
  "Berasia": ["Venue", "Makeup", "Catering"],
  "Kolar": ["Venue", "DJ", "Camera"],
  "Haveli": ["Venue", "Catering", "Transport"],
  "Mulshi": ["Venue", "DJ", "Makeup"],
  "Andheri": ["Venue", "Catering", "DJ", "Camera"],
  "Borivali": ["Venue", "Transport", "Makeup"]
};

// State → District
document.getElementById("state").addEventListener("change", function() {
  let state = this.value;
  let districtSelect = document.getElementById("district");
  districtSelect.innerHTML = "<option value=''>Select District</option>";

  if(locationData[state]) {
    Object.keys(locationData[state]).forEach(district => {
      districtSelect.innerHTML += `<option>${district}</option>`;
    });
  }
});

// District → Tehsil
document.getElementById("district").addEventListener("change", function() {
  let state = document.getElementById("state").value;
  let district = this.value;
  let tehsilSelect = document.getElementById("subdistrict");
  tehsilSelect.innerHTML = "<option value=''>Select Sub-District</option>";

  if(locationData[state] && locationData[state][district]) {
    Object.keys(locationData[state][district]).forEach(tehsil => {
      tehsilSelect.innerHTML += `<option>${tehsil}</option>`;
    });
  }
});

// Tehsil → City + Services
document.getElementById("subdistrict").addEventListener("change", function() {
  let state = document.getElementById("state").value;
  let district = document.getElementById("district").value;
  let tehsil = this.value;

  // City dropdown
  let citySelect = document.getElementById("city");
  citySelect.innerHTML = "<option value=''>Select City/Village</option>";
  if(locationData[state] && locationData[state][district] && locationData[state][district][tehsil]) {
    locationData[state][district][tehsil].forEach(city => {
      citySelect.innerHTML += `<option>${city}</option>`;
    });
  }

  // Services dropdown
  let serviceSelect = document.getElementById("services");
  serviceSelect.innerHTML = "<option value=''>Select Service</option>";
  if(serviceData[tehsil]) {
    serviceData[tehsil].forEach(service => {
      serviceSelect.innerHTML += `<option value="${service}">${service}</option>`;
    });
  }
});
