/**
 * Stores the current customer user.
 * @type {Object}
 */
let currentCustomerUser;

/**
 * Initializes the customer profile page by setting the current user, setting the header,
 * loading the customer user, and rendering the customer details and reviews.
 * @async
 * @function initCProfile
 * @returns {Promise<void>}
 */
async function initCProfile() {
  let response = await setCurrentUser();
  setHeader();
  if (!response.ok) {
    window.location.href = "./login.html";
  } else {
    await loadCustomerUser();
    document.getElementById("customer_detail_section").innerHTML =
      getCustomerDetailTemplate();
    await setUsers();
    await loadRenderCustomerReviews();
  }
}

/**
 * Loads and renders the reviews for the customer user.
 * @async
 * @function loadRenderCustomerReviews
 * @returns {Promise<void>}
 */
async function loadRenderCustomerReviews() {
  await setReviewsForCustomerUser(currentCustomerUser.user);
  document.getElementById("customer_profile_review_list").innerHTML =
    getReviewWLinkTemplateList(currentReviews);
}

/**
 * Changes the review filter for the customer profile and reloads the reviews.
 * @async
 * @function changeReviewFilterCustomerProfile
 * @param {HTMLElement} element - The element containing the new review filter value.
 * @returns {Promise<void>}
 */
async function changeReviewFilterCustomerProfile(element) {
  currentReviewOrdering = element.value;
  loadRenderCustomerReviews();
}

/**
 * Loads the customer user based on the profile ID from the URL parameters.
 * If the profile ID is not found, redirects to the index page.
 * If the user type is not customer, redirects to the business profile page.
 * @async
 * @function loadCustomerUser
 * @returns {Promise<void>}
 */
async function loadCustomerUser() {
  const urlParams = new URLSearchParams(window.location.search);
  const profileId = urlParams.get("id");
  if (!profileId) {
    window.location.href = "index.html";
  } else {
    let resp = await getData(PROFILE_URL + profileId + "/");
    if (resp.ok) {
      if (resp.data.type == "customer") {
        currentCustomerUser = resp.data;
      } else {
        window.location.href = `business_profile.html?id=${resp.data.user}`;
      }
    } else {
      showToastMessage(true, extractErrorMessages(resp.data));
    }
  }
}
