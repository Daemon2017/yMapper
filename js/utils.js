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
        includedToSetsGroup.removeLayer(entry.polygon);
        targetSet.splice(existingIndex, 1);
    } else {
        if (targetSet.length >= 100) {
            const oldestEntry = targetSet.shift();
            includedToSetsGroup.removeLayer(oldestEntry.polygon);
        }
        const polygon = drawSingleHex(includedToSetsGroup, h3Index, color, label);
        targetSet.push({
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