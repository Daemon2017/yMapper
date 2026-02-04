function getLatLng() {
    let center = map.getCenter();
    document.getElementById(LAT_FORM_ELEMENT_ID).value = center.lat;
    document.getElementById(LNG_FORM_ELEMENT_ID).value = center.lng;
}

function createGradientList() {
    let lastColorList = [
        "#201923",
        "#5d4c86",
        "#fcff5d",
        "#7dfc00",
        "#0ec434",
        "#228c68",
        "#8ad8e8",
        "#235b54",
        "#29bdab",
        "#3998f5",
        "#37294f",
        "#277da7",
        "#3750db",
        "#f22020",
        "#991919",
        "#ffcba5",
        "#e68f66",
        "#c56133",
        "#96341c",
        "#632819",
        "#ffc413",
        "#f47a22",
        "#2f2aa0",
        "#b732cc",
        "#772b9d",
        "#f07cab",
        "#d30b94",
        "#edeff3",
        "#c3a5b4",
        "#946aa2"
    ];
    let gradientList = [];
    for (let i = 0; i < colorBoxesNumber; i++) {
        let numberOfItems = 10;
        let rainbow = new Rainbow();
        rainbow.setNumberRange(1, numberOfItems);
        rainbow.setSpectrum("#FFFFFF", lastColorList[i % lastColorList.length]);
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

function drawLayers() {
    heatmapGroup.clearLayers();

    let caption = '';
    if (document.getElementById(GROUP_CHECKBOX_ELEMENT_ID).checked) {
        caption = 'level'
    } else {
        caption = 'snps'
    }

    let i = 0;
    for (const data of dataList) {
        if (!uncheckedSnpsList.includes(i)) {
            let hexColor = gradientValues[i][9];
            let size = parseFloat(document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value) || 1.0;
            data['centroids'].forEach(element => {
                let lng = element[0];
                let lat = element[1];
                let hexCoords = getHexVertices(lat, lng, size);
                let polygon = L.polygon(hexCoords, {
                    color: hexColor,
                    weight: 1,
                    fillColor: hexColor,
                    fillOpacity: 0.6,
                    interactive: true
                });
                polygon.bindTooltip(`${caption}: ${data[caption]}`);
                heatmapGroup.addLayer(polygon);
            });
            document.getElementById(`checkBoxLabel${i}`).style.backgroundColor = gradientValues[i][9];
            document.getElementById(`checkBox${i}`).checked = true;
            document.getElementById(`checkBoxLabel${i}`).innerHTML = `<span class="tooltiptext" id="tooltipText${i}">${data[caption]}</span>`;
        }
        i++;
    }
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
