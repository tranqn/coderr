/**
 * Indicates if the offer page is loaded.
 * @type {boolean}
 */
let offerPageLoaded = true;

/**
 * Stores the current orders.
 * @type {Array}
 */
let currentOrders = [];

/**
 * Stores the current business offer list filter.
 * @type {Object}
 * @property {string|null} creator_id - The ID of the creator.
 * @property {number} page - The current page number.
 */
let currentBusinessOfferListFilter = {
  creator_id: null,
  page: 1,
};

/**
 * Initializes the profile page by setting the current user, rendering the page, and setting the header.
 * @async
 * @function init
 * @returns {Promise<void>}
 */
async function init() {
  let response = await setCurrentUser();

  if (!response.ok) {
    window.location.href = "./login.html";
  } else {
    await renderPage();
    setHeader();
  }
}

/**
 * Renders the profile page based on the user type.
 * @async
 * @function renderPage
 * @returns {Promise<void>}
 */
async function renderPage() {
  await getFullProfileData();

  let contentRef = document.getElementById("content");
  if (currentUser.type == "business") {
    currentBusinessOfferListFilter.creator_id = currentUser.user;
    await setOffers(currentBusinessOfferListFilter);
    contentRef.innerHTML = getBusinessProfilePageTemplate(
      currentUser,
      currentOrders,
      currentOffers,
      currentReviews
    );
  } else if (currentUser.type == "customer") {
    contentRef.innerHTML = getCustomerProfilePageTemplate();
  } else {
    showToastMessage();
  }
}

/**
 * Navigates to the specified offer page and updates the offer list filter.
 * @async
 * @function goToOfferPage
 * @param {number} pageNum - The page number to navigate to.
 * @returns {Promise<void>}
 */
async function goToOfferPage(pageNum) {
  if (pageNum && offerPageLoaded) {
    offerPageLoaded = false;
    currentBusinessOfferListFilter.page = pageNum;
  }
  await updateOfferListFilter();
  offerPageLoaded = true;
}

/**
 * Updates the offer list filter and renders the updated offer list.
 * @async
 * @function updateOfferListFilter
 * @returns {Promise<void>}
 */
async function updateOfferListFilter() {
  await setOffers(currentBusinessOfferListFilter);
  document.getElementById(
    "business_offer_list"
  ).innerHTML = `${getBusinessOfferTemplateList(currentOffers)}
    ${getOfferPagination(
      calculateNumPages(allOffersLength, PAGE_SIZE),
      currentBusinessOfferListFilter.page
    )}`;
}

/**
 * Retrieves the full profile data for the current user.
 * @async
 * @function getFullProfileData
 * @returns {Promise<void>}
 */
async function getFullProfileData() {
  if (currentUser.type == "business") {
    await setReviewsForBusinessUser(currentUser.user);
  } else if (currentUser.type == "customer") {
    await setReviewsForCustomerUser(currentUser.user);
  }

  let orderResp = await getData(ORDER_URL);
  if (orderResp.ok) {
    currentOrders = orderResp.data;
  }

  await setUsers();
}

/**
 * Changes the review filter for the profile and reloads the reviews.
 * @async
 * @function changeReviewFilterProfile
 * @param {HTMLElement} element - The element containing the new review filter value.
 * @returns {Promise<void>}
 */
async function changeReviewFilterProfile(element) {
  currentReviewOrdering = element.value;

  if (currentUser.type == "business") {
    await setReviewsForBusinessUser(currentUser.user);
    document.getElementById("business_review_list").innerHTML =
      getReviewWLinkTemplateList(currentReviews);
  } else if (currentUser.type == "customer") {
    await setReviewsForCustomerUser(currentUser.user);
    document.getElementById("edit_review_list").innerHTML =
      getReviewWLinkEditableTemplateList(currentReviews);
  }
}

/**
 * Changes the status of an order.
 * @async
 * @function changeOrderStatus
 * @param {string} status - The new status of the order.
 * @param {number} orderId - The ID of the order to update.
 * @returns {Promise<void>}
 */
async function changeOrderStatus(status, orderId) {
  let singleOrderIndex = currentOrders.findIndex((item) => item.id === orderId);
  if (
    singleOrderIndex >= 0 &&
    currentOrders[singleOrderIndex].status != status
  ) {
    let resp = await updateOrder(orderId, status);
    if (resp.ok) {
      currentOrders[singleOrderIndex].status = status;
      document.getElementById("business_order_list").innerHTML =
        getBusinessOrderTemplateList();
    }
  }
}

/**
 * Handles the business profile edit form submission.
 * Prevents the default form submission behavior, retrieves form data, and updates the business profile.
 * @async
 * @function businessEditOnsubmit
 * @param {Event} event - The form submission event.
 * @returns {Promise<void>}
 */
async function businessEditOnsubmit(event) {
  event.preventDefault();
  const data = getFormData(event.target);
  let formData = jsonToFormData(data);

  updateBusinessProfile(formData);
}

/**
 * Updates the business profile with the provided form data.
 * @async
 * @function updateBusinessProfile
 * @param {FormData} formData - The form data to update the business profile with.
 * @returns {Promise<void>}
 */
async function updateBusinessProfile(formData) {
  if (currentFile) {
    formData.append("file", currentFile);
  }

  let resp = await patchData(PROFILE_URL + currentUser.user + "/", formData);

  if (resp.ok) {
    let userResp = await getData(PROFILE_URL + resp.data.user + "/");
    currentUser = userResp.data;
    closeDialog("business_dialog");
    document.getElementById("business_profile").innerHTML =
      getBusinessProfileTemplate(currentUser);
    setHeader();
  } else {
    extractErrorMessages(resp.data);
    showToastMessage(true, extractErrorMessages(resp.data));
  }
}

/**
 * Aborts the customer profile edit and closes the dialog.
 * @function abboardCustomerEdit
 */
function abboardCustomerEdit() {
  document.getElementById("customer_dialog").innerHTML =
    getCustomerDialogFormTemplate();
  closeDialog("customer_dialog");
}

/**
 * Handles the customer profile edit form submission.
 * Prevents the default form submission behavior, retrieves form data, and updates the customer profile.
 * @async
 * @function customerEditOnsubmit
 * @param {Event} event - The form submission event.
 * @returns {Promise<void>}
 */
async function customerEditOnsubmit(event) {
  event.preventDefault();
  const data = getFormData(event.target);

  let formData = jsonToFormData(data);

  updateCustomerProfile(formData);
}

/**
 * Updates the customer profile with the provided form data.
 * @async
 * @function updateCustomerProfile
 * @param {FormData} formData - The form data to update the customer profile with.
 * @returns {Promise<void>}
 */
async function updateCustomerProfile(formData) {
  if (currentFile) {
    formData.append("file", currentFile);
  }

  let resp = await patchData(PROFILE_URL + currentUser.user + "/", formData);
  if (resp.ok) {
    let userResp = await getData(PROFILE_URL + resp.data.user + "/");
    currentUser = userResp.data;
    closeDialog("customer_dialog");
    document.getElementById("customer_profile").innerHTML =
      getCustomerProfileTemplate();
  } else {
    extractErrorMessages(resp.data);
    showToastMessage(true, extractErrorMessages(resp.data));
  }
}

/**
 * Aborts the business profile edit and closes the dialog.
 * @function abboardBusinessEdit
 */
function abboardBusinessEdit() {
  closeDialog("business_dialog");
  document.getElementById("business_dialog").innerHTML =
    getBusinessDialogFormTemplate();
}
