async function main() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;

    let lat = 53.2582;
    let lng = 34.2850;
    let zoom = 4;

    let baseLayer = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: 'Map data &copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://cloudmade.com">CloudMade</a>',
            maxZoom: 12,
        }
    );
    map = new L.Map("mapLayer", {
        center: new L.LatLng(lat, lng),
        zoom: zoom,
        layers: [baseLayer],
        preferCanvas: true
    });
    hexagonsGroup.addTo(map);
    setsGroup.addTo(map);
    pointsGroup.addTo(map);
    map.addEventListener("moveend", getLatLng);
    map.on('click', function(e) {
        if (isIncludeToSetAMode) {
            includeToSet(e.latlng.lat, e.latlng.lng, 'A');
        } else if (isIncludeToSetBMode) {
            includeToSet(e.latlng.lat, e.latlng.lng, 'B');
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

async function show(action) {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;

    isIncludeToSetAMode = false;
    isIncludeToSetBMode = false;
    map.getContainer().style.cursor = '';
    uncheckedSnpsList = [];

    const snp = document.getElementById(SEARCH_FORM_ELEMENT_ID).value;
    const size = document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value;
    let isGrouped = false;
    if (action === 'Dispersion') {
        isGrouped = document.getElementById(GROUP_DISPERSION_CHECKBOX_ELEMENT_ID).checked;
        dataList = await getCentroidsDispersion(snp, size, isGrouped);
    } else if (action === 'Filtering') {
        const start = document.getElementById(START_FORM_ELEMENT_ID).value;
        const end = document.getElementById(END_FORM_ELEMENT_ID).value;
        isGrouped = document.getElementById(GROUP_FILTERING_CHECKBOX_ELEMENT_ID).checked;
        dataList = await getCentroidsFiltering(start, end, size, isGrouped);
    } else if (action === 'Homeland') {
        isGrouped = true;
        dataList = await getCentroidsHomeland(snp, size);
    }
    const caption = isGrouped ? 'level' : 'snps';
    drawLayers(dataList, action, caption, isGrouped);
}

function clearAll() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
    clearHexagons();
    clearSets();
    clearPoints();
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

function addHexagonsToSet(target) {
    const isIncludeToSet = (target === 'A') ? isIncludeToSetAMode : isIncludeToSetBMode;
    let labelText;
    if (isIncludeToSet) {
        if (target === 'A') {
            isIncludeToSetAMode = false;
        } else {
            isIncludeToSetBMode = false;
        }
        map.getContainer().style.cursor = '';
        labelText = (target === 'A') ? HEXAGONS_INCLUSION_TO_SET_A_FINISHED_STATE_TEXT : HEXAGONS_INCLUSION_TO_SET_B_FINISHED_STATE_TEXT;
    } else {
        isIncludeToSetAMode = (target === 'A');
        isIncludeToSetBMode = (target === 'B');
        clearHexagons();
        clearPoints();
        setsGroup.addTo(map);
        map.getContainer().style.cursor = 'crosshair';
        labelText = (target === 'A') ? HEXAGONS_INCLUSION_TO_SET_A_STARTED_STATE_TEXT : HEXAGONS_INCLUSION_TO_SET_B_STARTED_STATE_TEXT;
    }
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = labelText;
}

function swapSets() {
    if (!isIncludeToSetAMode && !isIncludeToSetBMode) {
        [includedToSetACentroids, includedToSetBCentroids] = [includedToSetBCentroids, includedToSetACentroids];
        setsGroup.clearLayers();
        includedToSetACentroids.forEach(item => {
            item.polygon = drawSingleHex(setsGroup, item.h3Index, 'green', 'Included to set A.');
        });
        includedToSetBCentroids.forEach(item => {
            item.polygon = drawSingleHex(setsGroup, item.h3Index, 'blue', 'Included to set B.');
        });
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = HEXAGONS_SETS_SWAPPED_STATE_TEXT;
    } else {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = HEXAGONS_SETTING_NOT_FINISHED_ERROR_TEXT;
    }
}

document.addEventListener('DOMContentLoaded', main);