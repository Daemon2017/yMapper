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

async function getParentFiltering() {
    const input = document.getElementById(SEARCH_FILTERING_FORM_ELEMENT_ID);
    const snp = input.value.replace(/\s+/g, '');
    if (!snp) return;
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const parentUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.PARENT}`;
        const params = new URLSearchParams({ snp: snp });
        const response = await fetch(`${parentUrl}?${params}`);
        if (response.ok) {
            const data = await response.json();
            input.value = data;
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
        } else {
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
        }
    } catch (error) {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    }
}

async function getParentMacro() {
    const input = document.getElementById(MACRO_SEARCH_FILTERING_FORM_ELEMENT_ID);
    const snp = input.value.replace(/\s+/g, '');
    if (!snp) return;
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const parentUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.PARENT}`;
        const params = new URLSearchParams({ snp: snp });
        const response = await fetch(`${parentUrl}?${params}`);
        if (response.ok) {
            const data = await response.json();
            input.value = data;
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

async function getCentroidsGeography(snp, size) {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const url = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_GEOGRAPHY}`;
        const params = new URLSearchParams({
            snp: snp,
            size: size
        });
        const response = await fetch(`${url}?${params}`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
            return data;
        }
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    } catch (error) {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    }
}

async function getCentroidsDispersion(snp, size, isGrouped) {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const centroidsDispersionUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_DISPERSION}`;
        const params = new URLSearchParams({
            snp: snp,
            size: size,
            group: isGrouped
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

async function getCentroidsHomeland(snp, size, group) {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const centroidsHomelandUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_HOMELAND}`;
        const params = new URLSearchParams({
            snp: snp,
            size: size,
        });
        const response = await fetch(`${centroidsHomelandUrl}?${params}`);
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

async function getCentroidsFiltering(start, end, size, isGrouped, snp) {
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
            size: size,
            start: start,
            end: end,
            group: isGrouped,
            snp: snp
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

async function getCentroidsMax(start, end, size, isGrouped, snp) {
    const url = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_MAX}`;
    const params = new URLSearchParams({ start, end, size, group: isGrouped, snp: snp });
    const response = await fetch(`${url}?${params}`);
    return await response.json();
}