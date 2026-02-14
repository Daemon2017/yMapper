function includeToSetA(lat, lng) {
    const size = parseInt(document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value);
    const h3Index = h3.latLngToCell(lat, lng, size);
    const existingIndex = includedToSetACentroids.findIndex(c => c.h3Index === h3Index);
    if (existingIndex !== -1) {
        const entry = includedToSetACentroids[existingIndex];
        includedToSetsGroup.removeLayer(entry.polygon);
        includedToSetACentroids.splice(existingIndex, 1);
    } else {
        if (includedToSetACentroids.length >= 100) {
            const oldestEntry = includedToSetACentroids.shift();
            includedToSetsGroup.removeLayer(oldestEntry.polygon);
        }
        const polygon = drawSingleHex(includedToSetsGroup, h3Index, 'green', `Included to set A.`);
        includedToSetACentroids.push({
            h3Index: h3Index,
            polygon: polygon
        });
    }
}

function includeToSetB(lat, lng) {
    const size = parseInt(document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value);
    const h3Index = h3.latLngToCell(lat, lng, size);
    const existingIndex = includedToSetBCentroids.findIndex(c => c.h3Index === h3Index);
    if (existingIndex !== -1) {
        const entry = includedToSetBCentroids[existingIndex];
        includedToSetsGroup.removeLayer(entry.polygon);
        includedToSetBCentroids.splice(existingIndex, 1);
    } else {
        if (includedToSetBCentroids.length >= 100) {
            const oldestEntry = includedToSetBCentroids.shift();
            includedToSetsGroup.removeLayer(oldestEntry.polygon);
        }
        const polygon = drawSingleHex(includedToSetsGroup, h3Index, 'blue', `Included to set B.`);
        includedToSetBCentroids.push({
            h3Index: h3Index,
            polygon: polygon
        });
    }
}

function clearFirst() {
    colorBoxesNumber = 0;
    uncheckedSnpsList = [];
    document.getElementById(BOXES_ELEMENT_ID).innerHTML = '';
    mainGroup.clearLayers();
}

function clearSecond() {
    isIncludeToSetAMode = false;
    isIncludeToSetBMode = false;
    includedToSetACentroids = [];
    includedToSetBCentroids = [];
    map.getContainer().style.cursor = '';
    includedToSetsGroup.clearLayers();
}