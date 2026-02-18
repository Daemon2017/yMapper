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
        if (targetSet.length >= 100) {
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