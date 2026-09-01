function validateLogin() {
  let user = document.getElementById("username").value;
  let pass = document.getElementById("password").value;

  if(user === "admin" && pass === "1234") {
    alert("Login Successful!");
    window.location.href = "/dashboard";  // Redirect to dashboard
    return false;
  } else {
    alert("Invalid Username or Password!");
    return false;
  }
}
