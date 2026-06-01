function includeToSet(lat, lng, target) {
    const isA = (target === 'A');
    const targetSet = isA ? includedToSetACentroids : includedToSetBCentroids;
    const color = isA ? 'green' : 'blue';
    const label = `Included to set ${target}.`;
    const size = parseInt(document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value);
    const h3Index = h3.latLngToCell(lat, lng, size);
    const existingIndex = targetSet.findIndex(c => c.h3Index === h3Index);
    if (existingIndex !== -1) {
        const entry = targetSet[existingIndex];
        setsGroup.removeLayer(entry.polygon);
        targetSet.splice(existingIndex, 1);
    } else {
        if (targetSet.length >= 150) {
            const oldestEntry = targetSet.shift();
            setsGroup.removeLayer(oldestEntry.polygon);
        }
        const polygon = drawSingleHex(setsGroup, h3Index, color, label);
        targetSet.push({
            h3Index: h3Index,
            polygon: polygon
        });
    }
}

function clearHexagons() {
    colorBoxesNumber = 0;
    uncheckedSnpsList = [];
    document.getElementById(BOXES_ELEMENT_ID).innerHTML = '';
    hexagonsGroup.clearLayers();
}

function clearSets() {
    isIncludeToSetAMode = false;
    isIncludeToSetBMode = false;
    includedToSetACentroids = [];
    includedToSetBCentroids = [];
    map.getContainer().style.cursor = '';
    setsGroup.clearLayers();
}

function clearPoints() {
    pointsGroup.clearLayers();
}

function updateUrlParams(currentAction) {
    const params = new URLSearchParams();
    if (map) {
        const center = map.getCenter();
        params.set('lat', center.lat.toFixed(4));
        params.set('lng', center.lng.toFixed(4));
        params.set('z', map.getZoom());
    }
    params.set('grid', document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value);
    let action = currentAction;
    if (!action) {
        const currentHashParams = new URLSearchParams(window.location.hash.substring(1));
        action = currentHashParams.get('action');
    }
    if (action) {
        params.set('action', action);
        if (['Geography', 'Dispersion', 'Homeland', 'Correlation'].includes(action)) {
            params.set('snp', document.getElementById(SEARCH_FORM_ELEMENT_ID).value);
            if (action === 'Dispersion' || action === 'Correlation') {
                params.set('groupDisp', document.getElementById(GROUP_DISPERSION_CHECKBOX_ELEMENT_ID).checked ? '1' : '0');
            }
            if (action === 'Correlation') {
                params.set('sStart', document.getElementById('searchStartForm').value);
                params.set('sEnd', document.getElementById('searchEndForm').value);
            }
        }
        else if (action === 'Max') {
            params.set('macroSnp', document.getElementById(MACRO_SEARCH_FILTERING_FORM_ELEMENT_ID).value);
            params.set('macroStart', document.getElementById(MACRO_START_FORM_ELEMENT_ID).value);
            params.set('macroEnd', document.getElementById(MACRO_END_FORM_ELEMENT_ID).value);
            params.set('groupMacro', document.getElementById(GROUP_MACRO_CHECKBOX_ELEMENT_ID).checked ? '1' : '0');
        }
        else if (action === 'Filtering') {
            params.set('filterSnp', document.getElementById(SEARCH_FILTERING_FORM_ELEMENT_ID).value);
            params.set('fStart', document.getElementById(START_FORM_ELEMENT_ID).value);
            params.set('fEnd', document.getElementById(END_FORM_ELEMENT_ID).value);
            params.set('modeSelect', document.getElementById('filteringModeSelect').value);
            params.set('groupFilter', document.getElementById(GROUP_FILTERING_CHECKBOX_ELEMENT_ID).checked ? '1' : '0');
        }
    }
    window.location.hash = params.toString();
}

function restoreParamsFromUrl() {
    const hash = window.location.hash.substring(1);
    if (!hash) return null;
    const params = new URLSearchParams(hash);
    const setVal = (id, key) => {
        const el = document.getElementById(id);
        if (el && params.has(key)) el.value = params.get(key);
    };
    const setCheck = (id, key) => {
        const el = document.getElementById(id);
        if (el && params.has(key)) el.checked = params.get(key) === '1';
    };
    setVal(GRID_SIZE_SELECT_ELEMENT_ID, 'grid');
    const action = params.get('action');
    if (action) {
        if (['Geography', 'Dispersion', 'Homeland', 'Correlation'].includes(action)) {
            setVal(SEARCH_FORM_ELEMENT_ID, 'snp');
            setCheck(GROUP_DISPERSION_CHECKBOX_ELEMENT_ID, 'groupDisp');
            setVal('searchStartForm', 'sStart');
            setVal('searchEndForm', 'sEnd');
        }
        else if (action === 'Max') {
            setVal(MACRO_SEARCH_FILTERING_FORM_ELEMENT_ID, 'macroSnp');
            setVal(MACRO_START_FORM_ELEMENT_ID, 'macroStart');
            setVal(MACRO_END_FORM_ELEMENT_ID, 'macroEnd');
            setCheck(GROUP_MACRO_CHECKBOX_ELEMENT_ID, 'groupMacro');
        }
        else if (action === 'Filtering') {
            setVal(SEARCH_FILTERING_FORM_ELEMENT_ID, 'filterSnp');
            setVal(START_FORM_ELEMENT_ID, 'fStart');
            setVal(END_FORM_ELEMENT_ID, 'fEnd');
            setVal('filteringModeSelect', 'modeSelect');
            setCheck(GROUP_FILTERING_CHECKBOX_ELEMENT_ID, 'groupFilter');
        }
    }
    return {
        lat: params.has('lat') ? parseFloat(params.get('lat')) : null,
        lng: params.has('lng') ? parseFloat(params.get('lng')) : null,
        zoom: params.has('z') ? parseInt(params.get('z')) : null,
        action: action
    };
}