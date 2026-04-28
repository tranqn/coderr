/**
 * Indicates if the offer page is loaded.
 * @type {boolean}
 */
let offerPageLoaded = true;

/**
 * Stores the current offer list filter.
 * @type {Object}
 * @property {string} search - The search query.
 * @property {number} page - The current page number.
 * @property {string} ordering - The ordering of the offers.
 * @property {string} max_delivery_time - The maximum delivery time.
 */
let currentOfferListFilter = {
  search: "",
  page: 1,
  ordering: "",
  max_delivery_time: "",
};

/**
 * Stores the current maximum delivery time filter.
 * @type {string}
 */
let currentmaxDeliveryTime = "";

/**
 * Stores the current ordering filter.
 * @type {string}
 */
let currentOrdering = "";

/**
 * Initializes the offer list page by setting the current user, setting the greetings section,
 * and loading and rendering the offers.
 * @async
 * @function offerListInit
 * @returns {Promise<void>}
 */
async function offerListInit() {
  const urlParams = new URLSearchParams(window.location.search);
  const search = urlParams.get("search");
  if (search) {
    currentOfferListFilter.search = search;
    document.getElementById("offer_list_searchbar").value = search;
  }
  await setCurrentUser();
  setGreetingsSection();
  await setOffersWODetails(currentOfferListFilter);
  renderOfferList();
}

/**
 * Renders the offer list.
 * @function renderOfferList
 */
function renderOfferList() {
  let listRef = document.getElementById("offer_list_content");
  listRef.innerHTML =
    getOfferTemplateList(currentOffers) +
    getOfferPagination(
      calculateNumPages(allOffersLength, PAGE_SIZE),
      currentOfferListFilter.page
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
    currentOfferListFilter.page = pageNum;
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
  currentOfferListFilter.ordering = currentOrdering;
  await setOffersWODetails(currentOfferListFilter);
  renderOfferList();
}

/**
 * Aborts the ordering filter and updates the offer list.
 * @function offerListAbboardOrdering
 */
function offerListAbboardOrdering() {
  offerListDeactivateAllRadio("offer_list_filter_ordering");
  currentOrdering = "";
  updateOfferListFilter();
  closeOpenId("order_filter");
}

/**
 * Updates the offer list filter with the maximum delivery time and navigates to the first page.
 * @async
 * @function updateOfferListFilterMaxDeliveryTime
 * @returns {Promise<void>}
 */
async function updateOfferListFilterMaxDeliveryTime() {
  currentOfferListFilter.max_delivery_time = currentmaxDeliveryTime;
  goToOfferPage(1);
}

/**
 * Updates the offer list filter with the search query and navigates to the first page.
 * @async
 * @function updateOfferListFilterSearch
 * @returns {Promise<void>}
 */
async function updateOfferListFilterSearch() {
  currentOfferListFilter.search = document.getElementById(
    "offer_list_searchbar"
  ).value;
  goToOfferPage(1);
}

/**
 * Sets the greetings section based on the current user.
 * @function setGreetingsSection
 */
function setGreetingsSection() {
  if (currentUser) {
    let greetingRef = document.getElementById("offer_list_greeting_section");
    greetingRef.classList.remove("d_none");
    let name = currentUser.first_name
      ? currentUser.first_name
      : "@" + currentUser.username;
    greetingRef.innerHTML = getGreetingBoxTemplate(name);
  }
}

/**
 * Deactivates all radio buttons within the specified element.
 * @function offerListDeactivateAllRadio
 * @param {string} id - The ID of the element containing the radio buttons.
 */
function offerListDeactivateAllRadio(id) {
  let element = document.getElementById(id);
  const radioInputs = element.querySelectorAll('input[type="radio"]');
  radioInputs.forEach((element) => {
    if (element) {
      element.checked = false;
    }
  });
}

/**
 * Aborts the delivery time filter and updates the offer list.
 * @function offerListAbboardDeliveryTime
 */
function offerListAbboardDeliveryTime() {
  offerListDeactivateAllRadio("offer_list_delivery_time_box");
  currentmaxDeliveryTime = "";
  updateOfferListFilterMaxDeliveryTime();
  toggleOpenId("time_filter");
}

/**
 * Applies the delivery time filter and updates the offer list.
 * @function offerListApplyDeliveryTimeFilter
 */
function offerListApplyDeliveryTimeFilter() {
  updateOfferListFilterMaxDeliveryTime();
  toggleOpenId("time_filter");
}
