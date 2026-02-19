function getLatLng() {
    let center = map.getCenter();
    document.getElementById(LAT_FORM_ELEMENT_ID).value = center.lat;
    document.getElementById(LNG_FORM_ELEMENT_ID).value = center.lng;
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

function updateUncheckedList(i, action) {
    if (document.getElementById(`checkBox${i}`).checked) {
        uncheckedSnpsList = uncheckedSnpsList.filter(item => item !== i);
    } else {
        uncheckedSnpsList.push(i);
    }
    let isGrouped = false;
    if (action === 'Dispersion') {
        isGrouped = document.getElementById(GROUP_DISPERSION_CHECKBOX_ELEMENT_ID).checked;
    } else if (action === 'Filtering') {
        const start = document.getElementById(START_FORM_ELEMENT_ID).value;
        const end = document.getElementById(END_FORM_ELEMENT_ID).value;
        isGrouped = document.getElementById(GROUP_FILTERING_CHECKBOX_ELEMENT_ID).checked;
    } else if (action === 'Homeland') {
        isGrouped = true;
    }
    const caption = isGrouped ? 'level' : 'snps';
    drawLayers(dataList, action, caption, isGrouped);
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

function drawLayers(dataList, action, caption, isGrouped) {
    colorBoxesNumber = dataList.length
    let colorBoxesInnerHtml = ``;
    for (let i = 0; i < colorBoxesNumber; i++) {
        colorBoxesInnerHtml +=
            `<span class="colorBox tooltip" id="colorBox${i}">
                <input type="checkbox" class="checkBox" id="checkBox${i}" onclick="updateUncheckedList(${i}, '${action}')"/>
                <label class="checkBoxLabel" id="checkBoxLabel${i}" for="checkBox${i}"></label>
            </span>`;
    }
    document.getElementById(BOXES_ELEMENT_ID).innerHTML = colorBoxesInnerHtml;

    const basePalette = isGrouped ? PALETTE_GROUP : PALETTE_SNPS;
    const gradientValues = createGradientList(basePalette);

    hexagonsGroup.clearLayers();
    pointsGroup.clearLayers();
    dataList.forEach((data, i) => {
        if (!uncheckedSnpsList.includes(i)) {
            let hexColor = gradientValues[i][9];
            data['centroids'].forEach(h3Index => {
                let tooltipText = '';
                if (action === 'Homeland') {
                    tooltipText = `
                        <b>Level:</b> ${data.level.toFixed(2)}%<br/>
                        <b>Vavilov Score:</b> ${data.vavilov_score.toFixed(2)}<br/>
                        <b>TMRCA Score:</b> ${data.tmrca_score.toFixed(2)}<br/>
                    `;
                } else {
                    tooltipText = `<b>${caption}:</b> ${data[caption]}`;
                }
                drawSingleHex(hexagonsGroup, h3Index, hexColor, tooltipText);
            });
            const label = document.getElementById(`checkBoxLabel${i}`);
            if (label) {
                label.style.backgroundColor = hexColor;
                label.innerHTML = `<span class="tooltiptext">${data[caption]}</span>`;
                document.getElementById(`checkBox${i}`).checked = true;
            }
        }
    });
    hexagonsGroup.addTo(map);
    map.removeLayer(setsGroup);
}

function drawSingleHex(group, h3Index, hexColor, text) {
    const hexCoords = getHexVertices(h3Index);
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

function getHexVertices(h3Index) {
    return h3.cellToBoundary(h3Index);
}