/**
 * Checks if the user is authenticated by verifying the presence of an auth token.
 * If authenticated, redirects to the index page.
 * @function checkAuth
 */
function checkAuth() {
  if (getAuthToken()) {
    window.location.href = "./index.html";
  }
}

/**
 * Handles the registration form submission.
 * Prevents the default form submission behavior, retrieves form data, and calls the registration function.
 * @function registerSubmit
 * @param {Event} event - The form submission event.
 */
function registerSubmit(event) {
  event.preventDefault();
  const data = getFormData(event.target);

  registration(data);
}
