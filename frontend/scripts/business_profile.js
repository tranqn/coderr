/**
 * Indicates if the offer page is loaded.
 * @type {boolean}
 */
let offerPageLoaded = true;

/**
 * Stores the current business user.
 * @type {Object}
 */
let currentBusinessUser;

/**
 * Stores the current offer business profile filter.
 * @type {Object}
 * @property {number} page - The current page number.
 * @property {number} creator_id - The ID of the creator.
 */
let currentOfferBusinessProfileFilter = {
  page: 1,
  creator_id: 11,
};

/**
 * Loads and renders the offers for the business profile.
 * @async
 * @function loadRenderOffers
 * @returns {Promise<void>}
 */
async function loadRenderOffers() {
  currentOfferBusinessProfileFilter.creator_id = currentBusinessUser.user;
  await setOffersWODetails(currentOfferBusinessProfileFilter);
  document.getElementById("business_profile_offer_list").innerHTML =
    getOfferTemplateList(currentOffers) +
    getOfferPagination(
      calculateNumPages(allOffersLength, PAGE_SIZE),
      currentOfferBusinessProfileFilter.page
    );
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
    currentOfferBusinessProfileFilter.page = pageNum;
  }
  await loadRenderOffers();
  offerPageLoaded = true;
}

/**
 * Initializes the business profile page by setting the current user, setting the header,
 * loading the business user, and rendering the business details, reviews, offers, and base info.
 * @async
 * @function initBProfile
 * @returns {Promise<void>}
 */
async function initBProfile() {
  let response = await setCurrentUser();
  setHeader();
  if (!response.ok) {
    window.location.href = "./login.html";
  } else {
    await loadBusinessUser();
    currentOfferBusinessProfileFilter.creator_id = currentBusinessUser.user;
    document.getElementById("business_profile_personal_data").innerHTML =
      getBusinessProfileDataTmplate();
    await setUsers();
    await loadRenderBusinessReviews();
    await loadRenderOffers();
    await loadRenderBusinessBaseInfo();
    toggleReviewAddBtn();
  }
}

/**
 * Loads and renders the business base information.
 * @async
 * @function loadRenderBusinessBaseInfo
 * @returns {Promise<void>}
 */
async function loadRenderBusinessBaseInfo() {
  let resp = await setSingleOfferCompletedCount(currentBusinessUser.user);
  if (resp.ok) {
    document.getElementById("business_profile_project_count").innerText =
      resp.data.completed_order_count;
  }
  document.getElementById(
    "business_profile_avg_rating"
  ).innerHTML = `${meanValueReviews()}<img src="./assets/icons/kid_star.svg" alt="" srcset="">`;
  document.getElementById("business_profile_review_count").innerText =
    currentReviews.length;
  document.getElementById("business_profile_offer_count").innerText =
    currentOffers.length;
}

/**
 * Loads the business user based on the profile ID from the URL parameters.
 * If the profile ID is not found, redirects to the index page.
 * If the user type is not business, redirects to the customer profile page.
 * @async
 * @function loadBusinessUser
 * @returns {Promise<void>}
 */
async function loadBusinessUser() {
  const urlParams = new URLSearchParams(window.location.search);
  const profileId = urlParams.get("id");
  if (!profileId) {
    window.location.href = "index.html";
  } else {
    let resp = await getData(PROFILE_URL + profileId + "/");
    if (resp.ok) {
      if (resp.data.type == "business") {
        currentBusinessUser = resp.data;
      } else {
        window.location.href = `customer_profile.html?id=${resp.data.user}`;
      }
    } else {
      extractErrorMessages(resp.data);
      showToastMessage(true, extractErrorMessages(resp.data));
    }
  }
}

/**
 * Loads and renders the reviews for the business user.
 * @async
 * @function loadRenderBusinessReviews
 * @returns {Promise<void>}
 */
async function loadRenderBusinessReviews() {
  await setReviewsForBusinessUser(currentBusinessUser.user);
  document.getElementById("business_profile_review_list").innerHTML =
    getReviewWLinkTemplateList(currentReviews);
}

/**
 * Changes the review filter for the business profile and reloads the reviews.
 * @async
 * @function changeReviewFilterBusinessProfile
 * @param {HTMLElement} element - The element containing the new review filter value.
 * @returns {Promise<void>}
 */
async function changeReviewFilterBusinessProfile(element) {
  currentReviewOrdering = element.value;
  loadRenderBusinessReviews();
}

/**
 * Submits a new review for the business profile.
 * @async
 * @function onSubmitReviewBusinessProfile
 * @returns {Promise<void>}
 */
async function onSubmitReviewBusinessProfile() {
  let textInputRef = document.getElementById("review_description_input");
  if (textInputRef.value != "") {
    let data = {
      rating: countStars(),
      description: textInputRef.value,
      business_user: currentBusinessUser.user,
    };

    let resp = await createReview(data);
    if (resp.ok) {
      document.getElementById("business_profile_review_list").innerHTML =
        getReviewWLinkTemplateList(currentReviews);
      closeDialog("rating_dialog");
    }
  } else {
    showFormErrors(["review_text_error"]);
  }
}
