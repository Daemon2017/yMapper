function getLatLng() {
    let center = map.getCenter();
    document.getElementById(LAT_FORM_ELEMENT_ID).value = center.lat;
    document.getElementById(LNG_FORM_ELEMENT_ID).value = center.lng;
}

function createGradientList(fullPalette) {
    let gradientList = [];
    let totalItems = colorBoxesNumber;
    let paletteSize = fullPalette.length;
    for (let i = 0; i < totalItems; i++) {
        let colorIndex = totalItems > 1 ? Math.floor(i * (paletteSize - 1) / (totalItems - 1)) : 0;
        let targetColor = fullPalette[colorIndex];
        let numberOfItems = 10;
        let rainbow = new Rainbow();
        rainbow.setNumberRange(1, numberOfItems);
        rainbow.setSpectrum("#FFFFFF", targetColor);
        let gradient = [];
        for (let j = 1; j <= numberOfItems; j++) {
            gradient.push("#" + rainbow.colourAt(j));
        }
        gradientList.push(gradient);
    }
    return gradientList;
}

function attachDropDownPrompt(dbSnpsList) {
    $(function () {
        $("#searchForm").on("keydown", function (event) {
            if (event.keyCode === $.ui.keyCode.TAB && $(this).autocomplete("instance").menu.active) {
                event.preventDefault();
            }
        }).autocomplete({
            source: function (request, response) {
                let term = request.term;
                let filteredSnpsList = dbSnpsList.filter(snp => snp.startsWith(term));
                let limitedSnpsList = filteredSnpsList.slice(0, 10);
                response(limitedSnpsList);
            },
            search: function (_event, _ui) {
                if (this.value.length <= 2) {
                    return false;
                }
            },
            focus: function (_event, _ui) {
                return false;
            },
            select: function (_event, ui) {
                this.value = ui.item.value;
                return false;
            }
        });
    });
}

function drawLayersDispersion() {
    const isGrouped = document.getElementById(GROUP_DISPERSION_CHECKBOX_ELEMENT_ID).checked;
    const caption = isGrouped ? 'level' : 'snps';
    const basePalette = isGrouped ? PALETTE_GROUP : PALETTE_SNPS;
    const gradientValues = createGradientList(basePalette);

    mainGroup.clearLayers();
    dataList.forEach((data, i) => {
        if (!uncheckedSnpsList.includes(i)) {
            let hexColor = gradientValues[i][9];
            let size = parseFloat(document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value);
            data['centroids'].forEach(element => {
                let lng = element[0];
                let lat = element[1];
                drawSingleHex(mainGroup, lat, lng, size, hexColor, `${caption}: ${data[caption]}`)
            });
            const label = document.getElementById(`checkBoxLabel${i}`);
            if (label) {
                label.style.backgroundColor = hexColor;
                label.innerHTML = `<span class="tooltiptext">${data[caption]}</span>`;
                document.getElementById(`checkBox${i}`).checked = true;
            }
        }
    });
    mainGroup.addTo(map);
    map.removeLayer(includedToSetsGroup);
}

function drawLayersFiltering() {
    const isGrouped = document.getElementById(GROUP_FILTERING_CHECKBOX_ELEMENT_ID).checked;
    const caption = isGrouped ? 'level' : 'snps';
    const basePalette = isGrouped ? PALETTE_GROUP : PALETTE_SNPS;
    const gradientValues = createGradientList(basePalette);

    mainGroup.clearLayers();
    dataList.forEach((data, i) => {
        if (!uncheckedSnpsList.includes(i)) {
            let hexColor = gradientValues[i][9];
            let size = parseFloat(document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value);
            data['centroids'].forEach(element => {
                let lng = element[0];
                let lat = element[1];
                drawSingleHex(mainGroup, lat, lng, size, hexColor, `${caption}: ${data[caption]}`)
            });
            const label = document.getElementById(`checkBoxLabel${i}`);
            if (label) {
                label.style.backgroundColor = hexColor;
                label.innerHTML = `<span class="tooltiptext">${data[caption]}</span>`;
                document.getElementById(`checkBox${i}`).checked = true;
            }
        }
    });
    mainGroup.addTo(map);
    map.removeLayer(includedToSetsGroup);
}

function drawSingleHex(group, lat, lng, size, hexColor, text) {
    const hexCoords = getHexVertices(lat, lng, size);
    const polygon = L.polygon(hexCoords, {
        color: hexColor,
        weight: 1,
        fillColor: hexColor,
        fillOpacity: 0.6,
        interactive: true
    });
    polygon.bindTooltip(text);
    group.addLayer(polygon);
    return polygon;
}

function getHexVertices(centerLat, centerLng, size) {
    let vertices = [];
    for (let i = 0; i < 6; i++) {
        let angle_rad = (Math.PI / 180) * (60 * i + 30);
        let lat = centerLat + size * Math.sin(angle_rad);
        let lng = centerLng + size * Math.cos(angle_rad);
        vertices.push([lat, lng]);
    }
    return vertices;
}

async function includeToSetA(lat, lng) {
    const size = parseFloat(document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value);
    const hexagon = await getHexagon(lat, lng, size);
    const cLat = hexagon[0];
    const cLng = hexagon[1];
    const existingIndex = includedToSetACentroids.findIndex(c => c.lat === cLat && c.lng === cLng);
    if (existingIndex !== -1) {
        const entry = includedToSetACentroids[existingIndex];
        includedToSetsGroup.removeLayer(entry.polygon);
        includedToSetACentroids.splice(existingIndex, 1);
    } else {
        if (includedToSetACentroids.length >= 12) {
            const oldestEntry = includedToSetACentroids.shift();
            includedToSetsGroup.removeLayer(oldestEntry.polygon);
        }
        const polygon = drawSingleHex(includedToSetsGroup, cLat, cLng, size, 'green', `Included to set A. Coords: ${cLat}, ${cLng}`);
        includedToSetACentroids.push({
            lat: cLat,
            lng: cLng,
            polygon: polygon
        });
    }
}

async function includeToSetB(lat, lng) {
    const size = parseFloat(document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value);
    const hexagon = await getHexagon(lat, lng, size);
    const cLat = hexagon[0];
    const cLng = hexagon[1];
    const existingIndex = includedToSetBCentroids.findIndex(c => c.lat === cLat && c.lng === cLng);
    if (existingIndex !== -1) {
        const entry = includedToSetBCentroids[existingIndex];
        includedToSetsGroup.removeLayer(entry.polygon);
        includedToSetBCentroids.splice(existingIndex, 1);
    } else {
        if (includedToSetBCentroids.length >= 12) {
            const oldestEntry = includedToSetBCentroids.shift();
            includedToSetsGroup.removeLayer(oldestEntry.polygon);
        }
        const polygon = drawSingleHex(includedToSetsGroup, cLat, cLng, size, 'blue', `Included to set B. Coords: ${cLat}, ${cLng}`);
        includedToSetBCentroids.push({
            lat: cLat,
            lng: cLng,
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

function updateUncheckedListDispersion(i) {
    if (document.getElementById(`checkBox${i}`).checked === true) {
        uncheckedSnpsList = uncheckedSnpsList.filter(item => item !== i);
    } else {
        uncheckedSnpsList.push(i);
    }
    drawLayersDispersion();
}

function updateUncheckedListFiltering(i) {
    if (document.getElementById(`checkBox${i}`).checked === true) {
        uncheckedSnpsList = uncheckedSnpsList.filter(item => item !== i);
    } else {
        uncheckedSnpsList.push(i);
    }
    drawLayersFiltering();
}