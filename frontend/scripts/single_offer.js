/**
 * Stores the current single offer user.
 * @type {Object|null}
 */
let currentSingleOfferUser = null;

/**
 * Stores the current opened detail of the offer.
 * @type {Object}
 */
let currentOpenedDetail;

/**
 * Stores the current offer count.
 * @type {number}
 */
let currentOfferCount = 0;

/**
 * Initializes the single offer page by setting the current user, toggling the review add button,
 * loading and rendering the single offer, and setting the header.
 * @async
 * @function singleOfferInit
 * @returns {Promise<void>}
 */
async function singleOfferInit() {
  await setCurrentUser();
  toggleReviewAddBtn();
  await loadRenderSingleOffer();
  setHeader();
}

/**
 * Loads and renders the single offer based on the profile ID from the URL parameters.
 * If the profile ID is not found, redirects to the index page.
 * @async
 * @function loadRenderSingleOffer
 * @returns {Promise<void>}
 */
async function loadRenderSingleOffer() {
  const urlParams = new URLSearchParams(window.location.search);
  const profileId = urlParams.get("id");
  if (!profileId) {
    window.location.href = "index.html";
  } else {
    let offerResp = await setSingleOffer(profileId);
    if (offerResp.ok) {
      await loadSingleOfferUser(currentSingleOffer.user);
      await setSingleOfferCount(currentSingleOffer.user);
      await loadRenderSingleOfferReviews();
      document.getElementById("single_offer_header_section").innerHTML =
        getsingleOfferHeaderTemplate();
      renderSingleOfferDetail("basic");
    } else {
      showToastMessage(
        (error = true),
        (msg = ["Das Angebot konnte nicht gefunden werden"])
      );
    }
  }
}

/**
 * Renders the single offer detail based on the specified type.
 * If the detail type is not found, shows a toast message indicating the error.
 * @function renderSingleOfferDetail
 * @param {string} type - The type of the offer detail to render.
 */
function renderSingleOfferDetail(type) {
  if (currentOpenedDetail?.offer_type != type) {
    let foundDetail = currentSingleOffer.details.find(
      (item) => item.offer_type === type
    );
    if (foundDetail) {
      currentOpenedDetail = foundDetail;
    } else {
      showToastMessage(
        (error = true),
        (msg = ["Das Angebotsdetail konnte nicht gefunden werden"])
      );
    }
    document.getElementById("single_offer_detail_section").innerHTML =
      getSingleOfferDetailTemplate();
    document.getElementById("single_offe_order_dialog").innerHTML =
      getShowOrderDialogContentTemplate();
  }
}

/**
 * Activates the clicked button and deactivates all other buttons in the offer detail header.
 * @function activatedButton
 * @param {HTMLElement} element - The button element to activate.
 */
function activatedButton(element) {
  const header = document.getElementById("offer_detail_header");
  const buttons = header.querySelectorAll("button");

  buttons.forEach((button) => {
    button.classList.remove("active");
  });
  element.classList.add("active");
}

/**
 * Loads the single offer user data based on the profile ID.
 * @async
 * @function loadSingleOfferUser
 * @param {string} profileId - The profile ID of the user.
 * @returns {Promise<void>}
 */
async function loadSingleOfferUser(profileId) {
  let resp = await getData(PROFILE_URL + profileId + "/");
  if (resp.ok) {
    currentSingleOfferUser = resp.data;
  } else {
    extractErrorMessages(resp.data);
    showToastMessage(true, extractErrorMessages(resp.data));
  }
}

/**
 * Loads and renders the reviews for the single offer user.
 * @async
 * @function loadRenderSingleOfferReviews
 * @returns {Promise<void>}
 */
async function loadRenderSingleOfferReviews() {
  await setUsers();
  await setReviewsForBusinessUser(currentSingleOfferUser.user);
  document.getElementById("single_offer_review_list").innerHTML =
    getReviewWLinkTemplateList(currentReviews);
}

/**
 * Changes the review filter for the single offer and reloads the reviews.
 * @async
 * @function changeReviewFilterSingleOffer
 * @param {HTMLElement} element - The element containing the new review filter value.
 * @returns {Promise<void>}
 */
async function changeReviewFilterSingleOffer(element) {
  currentReviewOrdering = element.value;
  await setReviewsForBusinessUser(currentSingleOfferUser.user);
  document.getElementById("single_offer_review_list").innerHTML =
    getReviewWLinkTemplateList(currentReviews);
}

/**
 * Submits a new review for the single offer.
 * @async
 * @function onSubmitReviewSingleOffer
 * @returns {Promise<void>}
 */
async function onSubmitReviewSingleOffer() {
  let textInputRef = document.getElementById("review_description_input");
  if (textInputRef.value != "") {
    let data = {
      rating: countStars(),
      description: textInputRef.value,
      business_user: currentSingleOfferUser.user,
    };

    let resp = await createReview(data);
    if (resp.ok) {
      document.getElementById("single_offer_review_list").innerHTML =
        getReviewWLinkTemplateList(currentReviews);
      closeDialog("rating_dialog");
    }
  } else {
    showFormErrors(["review_text_error"]);
  }
}

/**
 * Creates a new order for the single offer.
 * @async
 * @function singleOfferOrderCreate
 * @returns {Promise<void>}
 */
async function singleOfferOrderCreate() {
  let orderResp = await createOrder(currentOpenedDetail.id);
  if (orderResp.ok) {
    document.getElementById("single_offe_order_dialog").innerHTML =
      getSendOrderDialogContentTemplate();
  } else {
    showToastMessage(true, extractErrorMessages(orderResp.data));
  }
}

// UI Handling

window.addEventListener("resize", moveOnResize);
window.addEventListener("load", moveOnResize);
let respView = false;
const RESPVIEWPOINT = 1024;

function moveDetailBox(source, destination) {
  let destinationRef = document.getElementById(destination);
  destinationRef.classList.remove("d_none");

  let fragment = document.createDocumentFragment();
  let sourceElement = document.getElementById(source);
  let destinationElement = document.getElementById(destination);

  while (sourceElement.firstChild) {
    fragment.appendChild(sourceElement.firstChild);
  }
  destinationElement.appendChild(fragment);

  let sourceRef = document.getElementById(source);
  sourceRef.classList.add("d_none");
}

function setRespView() {
  if (window.innerWidth < RESPVIEWPOINT) {
    moveDetailBox("detail_box", "resp_detail_box");
    respView = true;
  }
}

function moveOnResize() {
  if (window.innerWidth < RESPVIEWPOINT && !respView) {
    moveDetailBox("detail_box", "resp_detail_box");
    respView = !respView;
  }
  if (window.innerWidth >= RESPVIEWPOINT && respView) {
    moveDetailBox("resp_detail_box", "detail_box");
    respView = !respView;
  }
}
