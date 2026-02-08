const CONFIG = {
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8080'
        : 'https://bbamf0mf8kfcd675bt1e.containers.yandexcloud.net',
    ENDPOINTS: {
        LIST: '/list',
        PARENT: '/parent',
        HEXAGON: '/hexagon',
        CENTROIDS: '/centroids',
        CENTROIDS2: '/centroids2',
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
const BOTH_LAT_AND_LNG_MUST_BE_A_NUMBER_ERROR_TEXT = "Error: Both Lat and Lng must be a number!";
const SERVER_ERROR_TEXT = "Error: Server error!";

const PALETTE_GROUP = [
    "#8B0000", "#940000", "#9E0000", "#A70000", "#B10000",
    "#BA0000", "#C40000", "#CD0000", "#D70000", "#E00000",
    "#EA0000", "#F30000", "#FD0000",
    "#FF0A00", "#FF1800", "#FF2500", "#FF3300", "#FF4000",
    "#FF4D00", "#FF5B00", "#FF6800", "#FF7600", "#FF8300",
    "#FF9100", "#FF9E00", "#FFA900", "#FFB000", "#FFB700",
    "#FFBF00", "#FFC600", "#FFCD00", "#FFD500", "#FFDC00",
    "#FFE300", "#FFEB00", "#FFF200", "#FFF900",
    "#FDFF03", "#F4FD0F", "#EBFC1A", "#E2FA26", "#D8F932",
    "#CFF83E", "#C6F649", "#BDF555", "#B4F461", "#ABF26D",
    "#A2F178", "#99EF84", "#90EE90"
];

const PALETTE_SNPS = [
    "#FFB300", "#803E75", "#FF6800", "#A6BDD7", "#C10020", "#CEA262", "#817066", "#007D34",
    "#F6768E", "#00538A", "#FF7A5C", "#53377A", "#FF8E00", "#B32851", "#F4C800", "#7F180D",
    "#93AA00", "#593315", "#F13A13", "#232C16", "#00A1C1", "#1CE6FF", "#FF34FF", "#FF4A46",
    "#008941", "#006FA6", "#A30059", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43",
    "#8FB0FF", "#997D45", "#5A0007", "#809181", "#1B4400", "#4FC601", "#3B5DFF", "#4A3B53",
    "#FF2F80", "#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B1CC10",
    "#E0FF66", "#740AFF"
];

let map;
let heatmapGroup = L.layerGroup();
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
    heatmapGroup.addTo(map);
    map.addEventListener("moveend", getLatLng);
    map.on('click', function(e) {
        if (isIncludeMode) {
            handleMapClick(e.latlng.lat, e.latlng.lng);
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

    const snps = await getDbSnpsList()
    attachDropDownPrompt(snps);
}

async function showDispersion() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;

    uncheckedSnpsList = [];

    dataList = await getCentroids();
    colorBoxesNumber = dataList.length
    let colorBoxesInnerHtml = ``;
    for (let i = 0; i < colorBoxesNumber; i++) {
        colorBoxesInnerHtml +=
            `<span class="colorBox tooltip" id="colorBox${i}">
            <input type="checkbox" class="checkBox" id="checkBox${i}" onclick="updateUncheckedList(${i})"/>
            <label class="checkBoxLabel" id="checkBoxLabel${i}" for="checkBox${i}"></label>
        </span>`;
    }
    document.getElementById(BOXES_ELEMENT_ID).innerHTML = colorBoxesInnerHtml;
    drawLayers();
}

async function showSimilarity() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;

    uncheckedSnpsList = [];

    dataList = await getCentroids2();
    colorBoxesNumber = dataList.length
    let colorBoxesInnerHtml = ``;
    for (let i = 0; i < colorBoxesNumber; i++) {
        colorBoxesInnerHtml +=
            `<span class="colorBox tooltip" id="colorBox${i}">
            <input type="checkbox" class="checkBox" id="checkBox${i}" onclick="updateUncheckedList2(${i})"/>
            <label class="checkBoxLabel" id="checkBoxLabel${i}" for="checkBox${i}"></label>
        </span>`;
    }
    document.getElementById(BOXES_ELEMENT_ID).innerHTML = colorBoxesInnerHtml;
    drawLayers2();
}

function clearAll() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
    heatmapGroup.clearLayers();
    includedCentroids = [];
    document.getElementById(BOXES_ELEMENT_ID).innerHTML = '';
    colorBoxesNumber = 0;

    isIncludeMode = false;
    map.getContainer().style.cursor = '';

    uncheckedSnpsList = [];

    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
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

function updateUncheckedList(i) {
    if (document.getElementById(`checkBox${i}`).checked === true) {
        uncheckedSnpsList = uncheckedSnpsList.filter(item => item !== i);
    } else {
        uncheckedSnpsList.push(i);
    }
    drawLayers();
}

function updateUncheckedList2(i) {
    if (document.getElementById(`checkBox${i}`).checked === true) {
        uncheckedSnpsList = uncheckedSnpsList.filter(item => item !== i);
    } else {
        uncheckedSnpsList.push(i);
    }
    drawLayers2();
}

function includeHexagons() {
    if (isIncludeMode) {
        isIncludeMode = false;
        map.getContainer().style.cursor = '';
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = HEXAGONS_INCLUSION_FINISHED_STATE_TEXT;
    } else {
        clearAll();
        isIncludeMode = true;
        map.getContainer().style.cursor = 'crosshair';
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = HEXAGONS_INCLUSION_STARTED_STATE_TEXT;
    }
}

document.addEventListener('DOMContentLoaded', main);