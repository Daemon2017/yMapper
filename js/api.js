async function getParent() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
    const parentUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.PARENT}`;
    const params = new URLSearchParams({
        snp: document.getElementById(SEARCH_FORM_ELEMENT_ID).value
    });
    const response = await fetch(`${parentUrl}?${params}`);
    if (response.status === 200) {
        const data = await response.json();
        let parentSnp = data['parent']
        document.getElementById(SEARCH_FORM_ELEMENT_ID).value = parentSnp;
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
    } else {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    }
}

async function getDbSnpsList() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
    const listUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.LIST}`;
    const response = await fetch(`${listUrl}`);
    if (response.status === 200) {
        dbSnpsList = await response.json();
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
    } else {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    }
}

async function getCentroids() {
    document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
    const centroidsUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS}`;
    const params = new URLSearchParams({
        snp: document.getElementById(SEARCH_FORM_ELEMENT_ID).value,
        size: document.getElementById(GRID_SIZE_SELECT_ELEMENT_ID).value,
        group: document.getElementById(GROUP_CHECKBOX_ELEMENT_ID).checked
    });
    const response = await fetch(`${centroidsUrl}?${params}`);
    if (response.status === 200) {
        const data = await response.json();
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
        return data;
    } else {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    }
}