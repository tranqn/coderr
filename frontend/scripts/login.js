/**
 * Checks if the user is authenticated by verifying the presence of an auth token.
 * If authenticated, redirects to the index page. Otherwise, sets the header.
 * @function checkAuthLogin
 */
function checkAuthLogin() {
  if (getAuthToken()) {
    window.location.href = "./index.html";
  }
  setHeader();
}

/**
 * Handles the login form submission.
 * Prevents the default form submission behavior, retrieves form data, and calls the logIn function.
 * @function logInSubmit
 * @param {Event} event - The form submission event.
 */
function logInSubmit(event) {
  event.preventDefault();
  const data = getFormData(event.target);

  logIn(data);
}

/**
 * Logs in a guest user based on the specified type.
 * @function guestLogin
 * @param {string} type - The type of guest user to log in.
 */
function guestLogin(type) {
  logIn(GUEST_LOGINS[type]);
}
