const CONFIG = {
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8080'
        : 'https://bbamf0mf8kfcd675bt1e.containers.yandexcloud.net',
    ENDPOINTS: {
        LIST: '/list',
        PARENT: '/parent',
        CENTROIDS: '/centroids',
    },
};

const LAT_FORM_ELEMENT_ID = "latForm";
const LNG_FORM_ELEMENT_ID = "lngForm";
const SEARCH_FORM_ELEMENT_ID = "searchForm";
const STATE_LABEL_ELEMENT_ID = "stateLabel";
const BOXES_ELEMENT_ID = "boxes";
const GROUP_CHECKBOX_ELEMENT_ID = "groupCheckbox";
const GRID_SIZE_SELECT_ELEMENT_ID = "gridSizeSelect";

const BUSY_STATE_TEXT = "Busy...";
const OK_STATE_TEXT = "OK.";
const BOTH_LAT_AND_LNG_MUST_BE_A_NUMBER_ERROR_TEXT = "Error: Both Lat and Lng must be a number!";
const SERVER_ERROR_TEXT = "Error: Server error!";

let map;
let heatmapGroup = L.layerGroup();
let colorBoxesNumber = 0;

let gradientValues = [];
let uncheckedSnpsList = [];
let dataList = [];

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

async function showMap() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
    clearAll(false);

    dataList = await getCentroids();
    colorBoxesNumber = dataList.length
    gradientValues = createGradientList();
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

function clearAll(isClearButtonPressed) {
    if (isClearButtonPressed) {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        heatmapGroup.clearLayers();
        document.getElementById(BOXES_ELEMENT_ID).innerHTML = '';
        colorBoxesNumber = 0;
    }

    uncheckedSnpsList = [];

    if (isClearButtonPressed) {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
    }
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

document.addEventListener('DOMContentLoaded', main);