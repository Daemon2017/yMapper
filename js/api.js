async function _resolveParentsForInput(elementId) {
    const input = document.getElementById(elementId);
    const snps = input.value.split(',').map(s => s.replace(/\s+/g, '')).filter(Boolean);
    if (snps.length === 0) return;
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const parentUrl = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.PARENT}`;
        const parents = await Promise.all(snps.map(async (snp) => {
            const response = await fetch(`${parentUrl}?${new URLSearchParams({ snp })}`);
            if (!response.ok) throw new Error('Server error');
            const data = await response.json();
            return (typeof data === 'string' && data) ? data : snp;
        }));
        input.value = [...new Set(parents)].join(', ');
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = OK_STATE_TEXT;
    } catch (error) {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = SERVER_ERROR_TEXT;
    }
}

function getParent() {
    return _resolveParentsForInput(SEARCH_FORM_ELEMENT_ID);
}

function getParentFiltering() {
    return _resolveParentsForInput(SEARCH_FILTERING_FORM_ELEMENT_ID);
}

function getParentMacro() {
    return _resolveParentsForInput(MACRO_SEARCH_FILTERING_FORM_ELEMENT_ID);
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

async function getCentroidsGeography(snp, size, isConfirmed) {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const url = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_GEOGRAPHY}`;
        const params = new URLSearchParams({
            snp: snp,
            size: size,
            is_confirmed: isConfirmed
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

async function getCentroidsDispersion(snp, size, groupMode, isConfirmed) {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const url = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_DISPERSION}`;
        const params = new URLSearchParams({
            snp: snp,
            size: size,
            group: groupMode,
            is_confirmed: isConfirmed
        });
        const response = await fetch(`${url}?${params}`);
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

async function getCentroidsHomeland(snp, size, isConfirmed, useStats) {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const url = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_HOMELAND}`;
        const params = new URLSearchParams({
            snp: snp,
            size: size,
            is_confirmed: isConfirmed,
            use_stats: useStats
        });
        const response = await fetch(`${url}?${params}`);
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


async function getCentroidsFiltering(start, end, size, groupMode, snp, excludeSnps, isConfirmed) {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const mode = document.getElementById("filteringModeSelect").value;
        let centroidsFilteringUrl = '';
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
            group: groupMode,
            snp: snp,
            exclude_snps: excludeSnps,
            is_confirmed: isConfirmed
        });
        const response = await fetch(`${centroidsFilteringUrl}?${params}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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

async function getCentroidsMax(start, end, size, groupMode, snp, isConfirmed) {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const url = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_MAX}`;
        const params = new URLSearchParams({
            start,
            end,
            size,
            group: groupMode,
            snp: snp,
            is_confirmed: isConfirmed
        });
        const response = await fetch(`${url}?${params}`);
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

async function getCentroidsCorrelation(snp, size, start, end, groupMode, isConfirmed) {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const url = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_CORRELATION}`;
        const params = new URLSearchParams({
            snp: snp,
            size: size,
            start: start,
            end: end,
            group: groupMode,
            is_confirmed: isConfirmed
        });
        const response = await fetch(`${url}?${params}`);
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

async function getCentroidsDepth(snp, size, isConfirmed) {
    try {
        document.getElementById(STATE_LABEL_ELEMENT_ID).innerText = BUSY_STATE_TEXT;
        const url = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CENTROIDS_DEPTH}`;
        const params = new URLSearchParams({
            snp: snp,
            size: size,
            is_confirmed: isConfirmed
        });
        const response = await fetch(`${url}?${params}`);
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
