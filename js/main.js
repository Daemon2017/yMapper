const CONFIG = {
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8080'
        : 'https://bbamf0mf8kfcd675bt1e.containers.yandexcloud.net',
    ENDPOINTS: {
        LIST: '/list',
        PARENT: '/parent',
        HEXAGON: '/hexagon',
        CENTROIDS_DISPERSION: '/centroids_dispersion',
        CENTROIDS_SIMILARITY: '/centroids_similarity',
    },
};

const LAT_FORM_ELEMENT_ID = "latForm";
const LNG_FORM_ELEMENT_ID = "lngForm";
const SEARCH_FORM_ELEMENT_ID = "searchForm";
const STATE_LABEL_ELEMENT_ID = "stateLabel";
const BOXES_ELEMENT_ID = "boxes";
const GROUP_CHECKBOX_ELEMENT_ID = "groupCheckbox";
const GROUP_CHECKBOX2_ELEMENT_ID = "group2Checkbox";
const GRID_SIZE_SELECT_ELEMENT_ID = "gridSizeSelect";
const START_FORM_ELEMENT_ID = "startForm";
const END_FORM_ELEMENT_ID = "endForm";

const BUSY_STATE_TEXT = "Busy...";
const OK_STATE_TEXT = "OK.";
const HEXAGONS_INCLUSION_STARTED_STATE_TEXT = "Click on the map to include from 1 to 12 hexagons, then click the Include button again to save them.";
const HEXAGONS_INCLUSION_FINISHED_STATE_TEXT = "Hexagons included! Ready to create similarity map.";
const HEXAGONS_EXCLUSION_STARTED_STATE_TEXT = "Click on the map to exclude from 1 to 12 hexagons, then click the Exclude button again to save them.";
const HEXAGONS_EXCLUSION_FINISHED_STATE_TEXT = "Hexagons excluded! Ready to create similarity map.";
const BOTH_LAT_AND_LNG_MUST_BE_A_NUMBER_ERROR_TEXT = "Error: Both Lat and Lng must be a number!";
const SERVER_ERROR_TEXT = "Error: Server error!";

const PALETTE_GROUP = [
  "#8B0000", "#8F0000", "#930000", "#980000", "#9D0000", "#A20000", "#A60000", "#AB0000", "#B00000", "#B50000",
  "#B90000", "#BE0000", "#C30000", "#C70000", "#CC0000", "#D10000", "#D60000", "#DA0000", "#DF0000", "#E40000",
  "#E80000", "#ED0000", "#F20000", "#F60000", "#FB0000", "#FD0300", "#FE0800", "#FF0F00", "#FF1600", "#FF1C00",
  "#FF2300", "#FF2900", "#FF3000", "#FF3700", "#FF3D00", "#FF4400", "#FF4A00", "#FF5100", "#FF5800", "#FF5E00",
  "#FF6500", "#FF6C00", "#FF7300", "#FF7900", "#FF8000", "#FF8600", "#FF8D00", "#FF9400", "#FF9A00", "#FFA000",
  "#FFA600", "#FFAA00", "#FFAE00", "#FFB100", "#FFB500", "#FFB800", "#FFBC00", "#FFC000", "#FFC300", "#FFC700",
  "#FFCA00", "#FFCE00", "#FFD200", "#FFD600", "#FFD900", "#FFDD00", "#FFE000", "#FFE400", "#FFE800", "#FFEC00",
  "#FFEF00", "#FFF200", "#FFF600", "#FEF900", "#FDFC01", "#FBFE04", "#F7FD0A", "#F2FC10", "#EEFC15", "#EAFB1B",
  "#E5FA21", "#E1F927", "#DCF92D", "#D7F832", "#D2F838", "#CEF73E", "#C9F644", "#C5F549", "#C1F54F", "#BCF455",
  "#B8F45B", "#B3F361", "#AFF267", "#AAF16D", "#A6F172", "#A1F078", "#9DEF7E", "#98EE84", "#94EE8A", "#90EE90"
];

const PALETTE_SNPS = [
    "#FFB300", "#803E75", "#FF6800", "#A6BDD7", "#C10020", "#CEA262", "#817066", "#007D34",
    "#F6768E", "#00538A", "#FF7A5C", "#53377A", "#FF8E00", "#B32851", "#F4C800", "#7F180D",
    "#93AA00", "#593315", "#F13A13", "#232C16", "#00A1C1", "#1CE6FF", "#FF34FF", "#FF4A46",
    "#008941", "#006FA6", "#A30059", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43",
    "#8FB0FF", "#997D45", "#5A0007", "#809181", "#1B4400", "#4FC601", "#3B5DFF", "#4A3B53",
    "#FF2F80", "#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B1CC10",
    "#E0FF66", "#740AFF",
    "#433366", "#36B238", "#660A23", "#598CB2", "#5C661F", "#9A12B2", "#33664F", "#B25736",
    "#0A0D66", "#76B259", "#661F4A", "#12A3B2", "#665C33", "#7636B2", "#0A661F", "#B2595F",
    "#1F3866", "#7BB212", "#663363", "#36B295", "#66360A", "#6959B2", "#27661F", "#B21253",
    "#335666", "#B1B236", "#4C0A66", "#59B280", "#66281F", "#122BB2", "#4A6633", "#B23692",
    "#0A6663", "#B29659", "#3A1F66", "#12B221", "#66333D", "#3673B2", "#52660A", "#AC59B2",
    "#1F664C", "#B24912", "#363366", "#53B236", "#660A3B", "#59A3B2", "#665E1F", "#7112B2",
    "#336642", "#B23736"
];

let map;
let mainGroup = L.layerGroup();
let includedExcludedGroup = L.layerGroup();
let colorBoxesNumber = 0;
let isIncludeMode = false;
let isExcludeMode = false;

let uncheckedSnpsList = [];
let dataList = [];
let includedCentroids = [];
let excludedCentroids = [];

async function main() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;

    let lat = 53.2582;
    let lng = 34.2850;
    let zoom = 4;

    let baseLayer = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: 'Map data &copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://cloudmade.com">CloudMade</a>',
            maxZoom: 10,
        }
    );
    map = new L.Map("mapLayer", {
        center: new L.LatLng(lat, lng),
        zoom: zoom,
        layers: [baseLayer],
    });
    mainGroup.addTo(map);
    includedExcludedGroup.addTo(map);
    map.addEventListener("moveend", getLatLng);
    map.on('click', function(e) {
        if (isIncludeMode) {
            addPolygonToIncluded(e.latlng.lat, e.latlng.lng);
        }
        if (isExcludeMode) {
            addPolygonToExcluded(e.latlng.lat, e.latlng.lng);
        }
    });

    L.Control.FileLayerLoad.LABEL = '<img class="icon" src="./img/folder.svg" alt="file icon"/>';
    let lflControl = L.Control.fileLayerLoad({
        fitBounds: true,
        layer: L.geoJson,
        layerOptions: {
            style: {
                color: 'red',
                fillOpacity: 0.1
            }
        },
    });
    lflControl.addTo(map);

    const snps = await getDbSnpsList();
    attachDropDownPrompt(snps);
}

async function showDispersion() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;

    isIncludeMode = false;
    isExcludeMode = false;
    map.getContainer().style.cursor = '';
    uncheckedSnpsList = [];

    dataList = await getCentroidsDispersion();
    colorBoxesNumber = dataList.length
    let colorBoxesInnerHtml = ``;
    for (let i = 0; i < colorBoxesNumber; i++) {
        colorBoxesInnerHtml +=
            `<span class="colorBox tooltip" id="colorBox${i}">
            <input type="checkbox" class="checkBox" id="checkBox${i}" onclick="updateUncheckedListDispersion(${i})"/>
            <label class="checkBoxLabel" id="checkBoxLabel${i}" for="checkBox${i}"></label>
        </span>`;
    }
    document.getElementById(BOXES_ELEMENT_ID).innerHTML = colorBoxesInnerHtml;
    drawLayersDispersion();
}

async function showSimilarity() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;

    isIncludeMode = false;
    isExcludeMode = false;
    map.getContainer().style.cursor = '';
    uncheckedSnpsList = [];

    dataList = await getCentroidsSimilarity();
    colorBoxesNumber = dataList.length
    let colorBoxesInnerHtml = ``;
    for (let i = 0; i < colorBoxesNumber; i++) {
        colorBoxesInnerHtml +=
            `<span class="colorBox tooltip" id="colorBox${i}">
            <input type="checkbox" class="checkBox" id="checkBox${i}" onclick="updateUncheckedListSimilarity(${i})"/>
            <label class="checkBoxLabel" id="checkBoxLabel${i}" for="checkBox${i}"></label>
        </span>`;
    }
    document.getElementById(BOXES_ELEMENT_ID).innerHTML = colorBoxesInnerHtml;
    drawLayersSimilarity();
}

function clearAll() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
    clearMain();
    clearIncludedExcluded();
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
}

function clearMain() {
    colorBoxesNumber = 0;
    uncheckedSnpsList = [];
    document.getElementById(BOXES_ELEMENT_ID).innerHTML = '';
    mainGroup.clearLayers();
}

function clearIncludedExcluded() {
    isIncludeMode = false;
    isExcludeMode = false;
    includedCentroids = [];
    excludedCentroids = [];
    map.getContainer().style.cursor = '';
    includedExcludedGroup.clearLayers();
}

function setLatLng() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
    let lat = Number(document.getElementById(LAT_FORM_ELEMENT_ID).value);
    let lng = Number(document.getElementById(LNG_FORM_ELEMENT_ID).value);
    if (isNaN(lat) || isNaN(lng)) {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BOTH_LAT_AND_LNG_MUST_BE_A_NUMBER_ERROR_TEXT;
    }
    map.panTo(new L.LatLng(lat, lng));
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
}

function updateUncheckedListDispersion(i) {
    if (document.getElementById(`checkBox${i}`).checked === true) {
        uncheckedSnpsList = uncheckedSnpsList.filter(item => item !== i);
    } else {
        uncheckedSnpsList.push(i);
    }
    drawLayersDispersion();
}

function updateUncheckedListSimilarity(i) {
    if (document.getElementById(`checkBox${i}`).checked === true) {
        uncheckedSnpsList = uncheckedSnpsList.filter(item => item !== i);
    } else {
        uncheckedSnpsList.push(i);
    }
    drawLayersSimilarity();
}

function includeHexagons() {
    if (isIncludeMode) {
        isIncludeMode = false;
        map.getContainer().style.cursor = '';
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = HEXAGONS_INCLUSION_FINISHED_STATE_TEXT;
    } else {
        isIncludeMode = true;
        isExcludeMode = false;
        clearMain();
        includedExcludedGroup.addTo(map);
        map.getContainer().style.cursor = 'crosshair';
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = HEXAGONS_INCLUSION_STARTED_STATE_TEXT;
    }
}

function excludeHexagons() {
    if (isExcludeMode) {
        isExcludeMode = false;
        map.getContainer().style.cursor = '';
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = HEXAGONS_EXCLUSION_FINISHED_STATE_TEXT;
    } else {
        isExcludeMode = true;
        isIncludeMode = false;
        clearMain();
        includedExcludedGroup.addTo(map);
        map.getContainer().style.cursor = 'crosshair';
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = HEXAGONS_EXCLUSION_STARTED_STATE_TEXT;
    }
}

document.addEventListener('DOMContentLoaded', main);