async function getParent() {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const parentUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.PARENT}`;
        const params = new URLSearchParams({
            snp: document.getElementById(SEARCH_FORM_ELEMENT_ID).value
        });
        const response = await fetch(`${parentUrl}?${params}`);
        if (response.ok) {
            const data = await response.json();
            let parentSnp = data;
            document.getElementById(SEARCH_FORM_ELEMENT_ID).value = parentSnp;
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
        } else {
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
        }
    } catch (error) {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    }
}

async function getDbSnpsList() {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const listUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.LIST}`;
        const response = await fetch(`${listUrl}`);
        if (response.ok) {
            const dbSnpsList = await response.json();
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
            return dbSnpsList;
        } else {
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
        }
    } catch (error) {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    }
}

async function getCentroidsDispersion() {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const centroidsDispersionUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_DISPERSION}`;
        const params = new URLSearchParams({
            snp: document.getElementById(SEARCH_FORM_ELEMENT_ID).value,
            size: document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value,
            group: document.getElementById(GROUP_DISPERSION_CHECKBOX_ELEMENT_ID).checked
        });
        const response = await fetch(`${centroidsDispersionUrl}?${params}`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
            return data;
        } else {
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
        }
    } catch (error) {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    }
}

async function getCentroidsFiltering() {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const mode = document.getElementById("filteringModeSelect").value;
        let centroidsFilteringUrl='';
        switch (mode) {
          case 'union':
            centroidsFilteringUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_UNION}`;
            break;
          case 'subtraction':
            centroidsFilteringUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_SUBTRACTION}`;
            break;
          case 'intersection':
            centroidsFilteringUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_INTERSECTION}`;
            break;
          case 'xor':
            centroidsFilteringUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_XOR}`;
            break;
        }
        const body = {
            a_points: includedToSetACentroids.map(item => item.h3Index),
            b_points: includedToSetBCentroids.map(item => item.h3Index)
        };
        const params = new URLSearchParams({
            size: document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value,
            start: document.getElementById(START_FORM_ELEMENT_ID).value,
            end: document.getElementById(END_FORM_ELEMENT_ID).value,
            group: document.getElementById(GROUP_FILTERING_CHECKBOX_ELEMENT_ID).checked
        });
        const response = await fetch(`${centroidsFilteringUrl}?${params}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
            return data;
        } else {
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
        }
    } catch (error) {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    }
}