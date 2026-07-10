/* ==========================================================================
   COSMIC DASHBOARD INTERACTIVE SCRIPT
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

    const apiBase = '/api';

    // 1. View Routing (Hash-Based)
    const menuLinks = document.querySelectorAll('.menu-link');
    const viewSections = document.querySelectorAll('.dashboard-view');
    const viewTitleEl = document.getElementById('view-title');
    const viewSubtitleEl = document.getElementById('view-subtitle');

    const viewMeta = {
        'home-view': { title: 'Dashboard Home', subtitle: 'Welcome to your daily cosmic alignment forecast.' },
        'horoscope-view': { title: 'Daily Horoscope', subtitle: 'Receive planetary forecasts for all twelve zodiac signs.' },
        'panchang-view': { title: 'Vedic Panchang', subtitle: 'Explore sunrise, lunar phases, and daily auspicious muhurtas.' },
        'planet-position-view': { title: 'Planet Positions', subtitle: 'Detailed coordinates, rasi lords, and retrograde phases for celestial bodies.' },
        'natal-chart-view': { title: 'Natal Chart Wheel', subtitle: 'Interactive Western Astrology natal chart wheel showing aspect lines, signs, and houses.' },
        'kundli-view': { title: 'Kundli Generator', subtitle: 'Calculate your birth chart elements and planetary positions.' },
        'matching-view': { title: 'Relationship Matcher', subtitle: 'Assess energy compatibility scores using Ashta Kuta matching.' }
    };

    const navigateToView = (viewId) => {
        // Toggle view visibility
        viewSections.forEach(section => {
            if (section.id === viewId) {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });

        // Toggle active menu link
        menuLinks.forEach(link => {
            if (link.getAttribute('data-view') === viewId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Update titles
        const meta = viewMeta[viewId] || { title: 'Dashboard', subtitle: '' };
        if (viewTitleEl) viewTitleEl.textContent = meta.title;
        if (viewSubtitleEl) viewSubtitleEl.textContent = meta.subtitle;

        // Reset scroll position
        window.scrollTo(0, 0);
    };

    // Listen to sidebar links
    menuLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetView = link.getAttribute('data-view');
            const targetHash = link.getAttribute('href');
            window.location.hash = targetHash;
            navigateToView(targetView);
        });
    });

    // Listen to quick banner anchor links
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('anchor-link') || e.target.closest('.anchor-link')) {
            const el = e.target.classList.contains('anchor-link') ? e.target : e.target.closest('.anchor-link');
            const targetHash = el.getAttribute('href');
            const correspondingLink = document.querySelector(`.menu-link[href="${targetHash}"]`);
            if (correspondingLink) {
                e.preventDefault();
                window.location.hash = targetHash;
                navigateToView(correspondingLink.getAttribute('data-view'));
            }
        }
    });

    // Check hash on load
    const checkHashRoute = () => {
        const hash = window.location.hash || '#home';
        const activeLink = document.querySelector(`.menu-link[href="${hash}"]`);
        if (activeLink) {
            navigateToView(activeLink.getAttribute('data-view'));
        } else {
            navigateToView('home-view');
        }
    };
    checkHashRoute();

    // 2. Config & Mode Check
    fetch(`${apiBase}/config`)
        .then(res => res.json())
        .then(data => {
            const indicator = document.getElementById('demo-indicator');
            if (indicator) {
                if (data.demo_mode) {
                    indicator.style.display = 'flex';
                } else {
                    indicator.innerHTML = '<i class="fa-solid fa-circle-check" style="color: #2ef56a;"></i><span>Connected to Prokerala API</span>';
                    indicator.style.backgroundColor = 'rgba(46, 245, 106, 0.08)';
                    indicator.style.borderColor = 'rgba(46, 245, 106, 0.2)';
                    indicator.style.color = '#2ef56a';
                }
            }
        })
        .catch(err => {
            console.warn("Could not check config endpoint. Operating in fallback mock mode.");
        });

    // Set header date
    const dateEl = document.getElementById('current-date');
    if (dateEl) {
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        dateEl.textContent = new Date().toLocaleDateString('en-US', options);
    }

    // 3. City Preset coordinates autofill
    const presets = document.querySelectorAll('.city-preset');
    presets.forEach(preset => {
        preset.addEventListener('change', (e) => {
            const val = e.target.value;
            const form = e.target.closest('form');
            if (!form) return;

            const id = e.target.id;
            let latInput, lngInput;

            if (id === 'match-g-city') {
                latInput = document.getElementById('match-g-lat');
                lngInput = document.getElementById('match-g-lng');
            } else if (id === 'match-b-city') {
                latInput = document.getElementById('match-b-lat');
                lngInput = document.getElementById('match-b-lng');
            } else {
                latInput = form.querySelector('input[id$="-lat"]');
                lngInput = form.querySelector('input[id$="-lng"]');
            }

            if (val !== 'custom') {
                const [lat, lng] = val.split(',');
                if (latInput) latInput.value = lat;
                if (lngInput) lngInput.value = lng;
            } else {
                if (latInput) latInput.value = '';
                if (lngInput) lngInput.value = '';
            }
        });
    });

    // Helper for loading animation
    const showLoader = (targetId) => {
        const container = document.getElementById(targetId);
        if (container) {
            container.innerHTML = `
                <div class="spinner-container">
                    <span class="loader-cosmic"></span>
                    <span class="loader-text">Consulting the alignment of the stars...</span>
                </div>
            `;
        }
    };

    // Helper to generate ISO 8601 offset strings
    const getISODatetime = (dateStr, timeStr) => {
        return `${dateStr}T${timeStr || '12:00'}:00+05:30`;
    };

    // Populate default dates on inputs
    const todayStr = new Date().toISOString().split('T')[0];
    const defaultLocalTime = new Date().toLocaleTimeString('en-US', { hour12: false }).substring(0, 5);
    
    const pDateInput = document.getElementById('panchang-date');
    if (pDateInput) {
        pDateInput.value = `${todayStr}T${defaultLocalTime}`;
    }

    const pPosDateInput = document.getElementById('planet-pos-date');
    if (pPosDateInput) {
        pPosDateInput.value = `${todayStr}T${defaultLocalTime}`;
    }

    const nChartDateInput = document.getElementById('natal-chart-date');
    if (nChartDateInput) {
        nChartDateInput.value = `${todayStr}T${defaultLocalTime}`;
    }

    const kDobInput = document.getElementById('kundli-dob');
    if (kDobInput) kDobInput.value = '1995-05-15';
    const kTobInput = document.getElementById('kundli-tob');
    if (kTobInput) kTobInput.value = '08:30';

    const mDobInput = document.getElementById('match-g-dob');
    if (mDobInput) mDobInput.value = '1996-08-20T10:15';
    const mDobInput2 = document.getElementById('match-b-dob');
    if (mDobInput2) mDobInput2.value = '1994-12-05T14:45';

    // 4. Daily Horoscope View Handlers
    const zodiacCards = document.querySelectorAll('.zodiac-card');
    const filterButtons = document.querySelectorAll('.filter-btn');

    // Sign elements helper
    const signIcons = {
        aries: 'fa-hand-fist', taurus: 'fa-leaf', gemini: 'fa-comments', cancer: 'fa-water',
        leo: 'fa-crown', virgo: 'fa-list-check', libra: 'fa-scale-balanced', scorpio: 'fa-eye',
        sagittarius: 'fa-compass', capricorn: 'fa-gem', aquarius: 'fa-lightbulb', pisces: 'fa-wand-sparkles'
    };

    // Element filter click
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const element = btn.getAttribute('data-element');
            zodiacCards.forEach(card => {
                if (element === 'all' || card.getAttribute('data-element') === element) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });

    // Horoscope Modal trigger
    const hModal = document.getElementById('horoscope-modal');
    const hModalClose = document.getElementById('close-horoscope-modal');
    const hModalBody = document.getElementById('horoscope-modal-body');

    zodiacCards.forEach(card => {
        card.addEventListener('click', () => {
            const sign = card.getAttribute('data-sign');
            if (hModal && hModalBody) {
                hModal.classList.add('active');
                
                hModalBody.innerHTML = `
                    <div class="spinner-container">
                        <span class="loader-cosmic"></span>
                        <span class="loader-text">Reading the sky charts...</span>
                    </div>
                `;

                fetch(`${apiBase}/horoscope/daily?sign=${sign}`)
                    .then(res => res.json())
                    .then(res => {
                        if (res.status === 'success' && res.data) {
                            const data = res.data;
                            const iconClass = signIcons[sign] || 'fa-star-and-crescent';
                            hModalBody.innerHTML = `
                                <div class="h-modal-header">
                                    <i class="fa-solid ${iconClass}"></i>
                                    <div>
                                        <h2>${data.sign} Daily Forecast</h2>
                                        <span>${data.date}</span>
                                    </div>
                                </div>
                                <div class="h-modal-body">
                                    <p class="main-pred">"${data.prediction}"</p>
                                    <div class="h-modal-grid">
                                        <div class="h-modal-box">
                                            <h4><i class="fa-solid fa-user"></i> Personal</h4>
                                            <p>${data.areas?.personal || 'Reflect and establish a balanced routine.'}</p>
                                        </div>
                                        <div class="h-modal-box">
                                            <h4><i class="fa-solid fa-heart"></i> Love</h4>
                                            <p>${data.areas?.relationship || 'Express warmth and show appreciation.'}</p>
                                        </div>
                                        <div class="h-modal-box">
                                            <h4><i class="fa-solid fa-briefcase"></i> Career</h4>
                                            <p>${data.areas?.profession || 'Plan organized approaches and schedules.'}</p>
                                        </div>
                                        <div class="h-modal-box">
                                            <h4><i class="fa-solid fa-dumbbell"></i> Wellness</h4>
                                            <p>${data.areas?.health || 'Incorporate physical activity or stretching.'}</p>
                                        </div>
                                    </div>
                                </div>
                            `;
                        } else {
                            throw new Error("Unable to fetch");
                        }
                    })
                    .catch(err => {
                        hModalBody.innerHTML = `
                            <div class="empty-state">
                                <i class="fa-solid fa-circle-exclamation text-danger"></i>
                                <p>Error loading forecast: ${err.message}. Ensure the API server is running.</p>
                            </div>
                        `;
                    });
            }
        });
    });

    if (hModalClose && hModal) {
        hModalClose.addEventListener('click', () => {
            hModal.classList.remove('active');
        });
    }

    // 5. Panchang Form Submission
    const panchangForm = document.getElementById('panchang-form');
    if (panchangForm) {
        panchangForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const dateVal = document.getElementById('panchang-date').value;
            const lat = document.getElementById('panchang-lat').value;
            const lng = document.getElementById('panchang-lng').value;
            const resultBox = document.getElementById('panchang-result');

            showLoader('panchang-result');

            // Format date local (YYYY-MM-DDTHH:MM) to ISO with +05:30
            const isoDt = `${dateVal}:00+05:30`;

            fetch(`${apiBase}/astrology/panchang?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}`)
                .then(res => res.json())
                .then(res => {
                    if (res.status === 'success' && res.data) {
                        const data = res.data;
                        
                        let auspiciousHtml = '';
                        let inauspiciousHtml = '';
                        
                        const auspicious = data.auspicious_timings || [];
                        auspicious.forEach(a => {
                            auspiciousHtml += `
                                <div class="muhurta-item">
                                    <span class="name">${a.name}</span>
                                    <span class="time-span">${a.start} - ${a.end}</span>
                                </div>
                            `;
                        });

                        const inauspicious = data.inauspicious_timings || [];
                        inauspicious.forEach(i => {
                            inauspiciousHtml += `
                                <div class="muhurta-item">
                                    <span class="name">${i.name}</span>
                                    <span class="time-span">${i.start} - ${i.end}</span>
                                </div>
                            `;
                        });

                        resultBox.innerHTML = `
                            <div class="result-card">
                                <div class="result-header">
                                    <div class="result-title">Vedic Panchang Report</div>
                                    <span class="result-badge">Muhurta Chart</span>
                                </div>
                                <div class="result-content">
                                    <div class="panchang-grid-meta">
                                        <div class="meta-block">
                                            <span>Tithi</span>
                                            <strong>${data.tithi?.name || 'N/A'}</strong>
                                        </div>
                                        <div class="meta-block">
                                            <span>Nakshatra</span>
                                            <strong>${data.nakshatra?.name || 'N/A'}</strong>
                                        </div>
                                        <div class="meta-block">
                                            <span>Yoga</span>
                                            <strong>${data.yoga?.name || 'N/A'}</strong>
                                        </div>
                                        <div class="meta-block">
                                            <span>Karana</span>
                                            <strong>${data.karana?.name || 'N/A'}</strong>
                                        </div>
                                    </div>
                                    
                                    <div class="panchang-main-metrics">
                                        <div class="panchang-metric-item">
                                            <h4>Solar Transitions</h4>
                                            <p>${data.sunrise} / ${data.sunset}</p>
                                            <span>Sunrise / Sunset</span>
                                        </div>
                                        <div class="panchang-metric-item">
                                            <h4>Lunar Transitions</h4>
                                            <p>${data.moonrise} / ${data.moonset}</p>
                                            <span>Moonrise / Moonset</span>
                                        </div>
                                    </div>

                                    <div class="muhurtas-split">
                                        <div class="muhurta-box">
                                            <h4>Auspicious Muhurtas</h4>
                                            <div class="muhurta-list">
                                                ${auspiciousHtml || '<p class="text-muted small">No timings calculated.</p>'}
                                            </div>
                                        </div>
                                        <div class="muhurta-box inauspicious">
                                            <h4>Inauspicious Timings</h4>
                                            <div class="muhurta-list">
                                                ${inauspiciousHtml || '<p class="text-muted small">No timings calculated.</p>'}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;

                        // Feed the home view quick overview if the date is today
                        const inputDateOnly = dateVal.split('T')[0];
                        if (inputDateOnly === todayStr) {
                            const homeSun = document.getElementById('home-sunrise-set');
                            const homeTithi = document.getElementById('home-tithi');
                            const homeNakshatra = document.getElementById('home-nakshatra');
                            if (homeSun) homeSun.textContent = `${data.sunrise.substring(0,5)} ${data.sunrise.slice(-2)} / ${data.sunset.substring(0,5)} ${data.sunset.slice(-2)}`;
                            if (homeTithi) homeTithi.textContent = data.tithi?.name || 'N/A';
                            if (homeNakshatra) homeNakshatra.textContent = data.nakshatra?.name || 'N/A';
                        }

                    } else {
                        throw new Error(res.message || "Failed parsing data");
                    }
                })
                .catch(err => {
                    resultBox.innerHTML = `
                        <div class="empty-state">
                            <i class="fa-solid fa-circle-exclamation text-danger"></i>
                            <p>Error generating panchang: ${err.message}. Make sure the backend is active.</p>
                        </div>
                    `;
                });
        });
    }

    // 6. Kundli Form Submission
    const zodiacNumbers = {
        aries: 1, taurus: 2, gemini: 3, cancer: 4, leo: 5, virgo: 6,
        libra: 7, scorpio: 8, sagittarius: 9, capricorn: 10, aquarius: 11, pisces: 12
    };

    const drawDiamondChart = (ascendantName, planetsList) => {
        // Calculate sign numbers
        const ascSignLower = ascendantName.toLowerCase();
        const startSignNum = zodiacNumbers[ascSignLower] || 1;

        // Map house index (1-12) to sign number
        const houseSigns = {};
        for (let house = 1; house <= 12; house++) {
            houseSigns[house] = ((startSignNum + house - 2) % 12) + 1;
        }

        // Map house index (1-12) to list of planet labels
        const housePlanets = {};
        for (let h = 1; h <= 12; h++) housePlanets[h] = [];
        
        planetsList.forEach(p => {
            const label = p.planet.substring(0, 2);
            if (p.house >= 1 && p.house <= 12) {
                housePlanets[p.house].push(label);
            }
        });

        // Coordinates for text placement for each of the 12 houses
        // House 1 (Lagna) is the central top triangle.
        // House 2 is top-left, House 3 is left-top, etc.
        const positions = {
            1:  { label: { x: 150, y: 70 },  planets: { x: 150, y: 95 } },
            2:  { label: { x: 95, y: 35 },   planets: { x: 95, y: 55 } },
            3:  { label: { x: 35, y: 95 },   planets: { x: 55, y: 95 } },
            4:  { label: { x: 75, y: 150 },  planets: { x: 100, y: 150 } },
            5:  { label: { x: 35, y: 205 },  planets: { x: 55, y: 205 } },
            6:  { label: { x: 95, y: 265 },  planets: { x: 95, y: 245 } },
            7:  { label: { x: 150, y: 230 }, planets: { x: 150, y: 205 } },
            8:  { label: { x: 205, y: 265 }, planets: { x: 205, y: 245 } },
            9:  { label: { x: 265, y: 205 }, planets: { x: 245, y: 205 } },
            10: { label: { x: 225, y: 150 }, planets: { x: 200, y: 150 } },
            11: { label: { x: 265, y: 95 },  planets: { x: 245, y: 95 } },
            12: { label: { x: 205, y: 35 },  planets: { x: 205, y: 55 } }
        };

        let signLabelsHtml = '';
        let planetLabelsHtml = '';

        for (let house = 1; house <= 12; house++) {
            const pos = positions[house];
            const sign = houseSigns[house];
            const planets = housePlanets[house].join(', ');

            // Inject sign numbers
            signLabelsHtml += `
                <text x="${pos.label.x}" y="${pos.label.y}" fill="#ffd700" font-size="10" font-weight="700" text-anchor="middle">${sign}</text>
            `;

            // Inject planets labels
            if (planets) {
                planetLabelsHtml += `
                    <text x="${pos.planets.x}" y="${pos.planets.y}" fill="#ffffff" font-size="11" font-weight="500" text-anchor="middle">${planets}</text>
                `;
            }
        }

        // Return full SVG markup
        return `
            <svg width="300" height="300" viewBox="0 0 300 300" class="svg-chart">
                <!-- Outer borders -->
                <rect x="10" y="10" width="280" height="280" stroke="#ffd700" stroke-width="2" fill="none" opacity="0.6" />
                
                <!-- Diagonals -->
                <line x1="10" y1="10" x2="290" y2="290" stroke="#ffd700" stroke-width="1.5" opacity="0.6" />
                <line x1="290" y1="10" x2="10" y2="290" stroke="#ffd700" stroke-width="1.5" opacity="0.6" />
                
                <!-- Inner diamond polygon -->
                <polygon points="150,10 290,150 150,290 10,150" stroke="#ffd700" stroke-width="1.5" fill="none" opacity="0.6" />
                
                <!-- Sign & Planets Text Injections -->
                ${signLabelsHtml}
                ${planetLabelsHtml}
            </svg>
        `;
    };

    const kundliForm = document.getElementById('kundli-form');
    if (kundliForm) {
        kundliForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const dob = document.getElementById('kundli-dob').value;
            const tob = document.getElementById('kundli-tob').value;
            const lat = document.getElementById('kundli-lat').value;
            const lng = document.getElementById('kundli-lng').value;
            const resultBox = document.getElementById('kundli-result');

            showLoader('kundli-result');
            const isoDt = getISODatetime(dob, tob);

            fetch(`${apiBase}/astrology/kundli?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}`)
                .then(res => res.json())
                .then(res => {
                    if (res.status === 'success' && res.data) {
                        const data = res.data;
                        const planets = data.planetary_positions || [];

                        let planetRows = '';
                        planets.forEach(p => {
                            planetRows += `
                                <tr>
                                    <td><strong>${p.planet}</strong></td>
                                    <td>${p.sign}</td>
                                    <td>House ${p.house}</td>
                                    <td>${p.degree.toFixed(1)}°</td>
                                </tr>
                            `;
                        });

                        // Draw visual chart
                        const ascName = data.ascendant?.name || 'Aries';
                        const chartSvg = drawDiamondChart(ascName, planets);

                        resultBox.innerHTML = `
                            <div class="result-card">
                                <div class="result-header">
                                    <div class="result-title">Kundli Birth Chart</div>
                                    <span class="result-badge">Vedic Horoscope</span>
                                </div>
                                <div class="result-content">
                                    <div class="kundli-grid-meta">
                                        <div class="meta-box">
                                            <span>Ascendant</span>
                                            <strong>${data.ascendant?.name || 'N/A'}</strong>
                                        </div>
                                        <div class="meta-box">
                                            <span>Moon Sign</span>
                                            <strong>${data.moon_sign?.name || 'N/A'}</strong>
                                        </div>
                                        <div class="meta-box">
                                            <span>Nakshatra</span>
                                            <strong>${data.nakshatra?.name || 'N/A'}</strong>
                                        </div>
                                    </div>
                                    
                                    <p><strong>Behavioral Profile:</strong></p>
                                    <p class="small text-muted font-italic" style="margin-bottom: 2rem;">
                                        ${data.ascendant?.description || ''} ${data.moon_sign?.description || ''} ${data.nakshatra?.description || ''}
                                    </p>

                                    <div class="chart-section">
                                        <div class="kundli-chart-draw">
                                            ${chartSvg}
                                        </div>
                                        <div class="planet-table-wrapper">
                                            <table class="planet-table">
                                                <thead>
                                                    <tr>
                                                        <th>Planet</th>
                                                        <th>Sign</th>
                                                        <th>House</th>
                                                        <th>Degree</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${planetRows || '<tr><td colspan="4">No planetary positions calculated.</td></tr>'}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        throw new Error(res.message || "Failed loading Kundli");
                    }
                })
                .catch(err => {
                    resultBox.innerHTML = `
                        <div class="empty-state">
                            <i class="fa-solid fa-circle-exclamation text-danger"></i>
                            <p>Error calculating chart: ${err.message}. Make sure the backend is active.</p>
                        </div>
                    `;
                });
        });
    }

    // 7. Matching Form Submission
    const matchingForm = document.getElementById('matching-form');
    if (matchingForm) {
        matchingForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const gDobVal = document.getElementById('match-g-dob').value;
            const gLat = document.getElementById('match-g-lat').value;
            const gLng = document.getElementById('match-g-lng').value;
            
            const bDobVal = document.getElementById('match-b-dob').value;
            const bLat = document.getElementById('match-b-lat').value;
            const bLng = document.getElementById('match-b-lng').value;
            
            const resultBox = document.getElementById('matching-result');

            showLoader('matching-result');

            // Formulate ISO strings
            const gIso = `${gDobVal}:00+05:30`;
            const bIso = `${bDobVal}:00+05:30`;

            fetch(`${apiBase}/astrology/kundli-matching?girl_dob=${encodeURIComponent(gIso)}&girl_latitude=${gLat}&girl_longitude=${gLng}&boy_dob=${encodeURIComponent(bIso)}&boy_coordinates=${bLat}&boy_longitude=${bLng}`)
                .then(res => res.json())
                .then(res => {
                    if (res.status === 'success' && res.data) {
                        const data = res.data;
                        const score = data.score;
                        const maxScore = data.max_score || 36;

                        const radius = 60;
                        const circumference = 2 * Math.PI * radius;
                        const offset = circumference - (score / maxScore) * circumference;

                        let verdictClass = 'average';
                        if (score >= 25) verdictClass = 'excellent';
                        else if (score < 18) verdictClass = 'low';

                        let gunaRows = '';
                        const gunas = data.guna_details || {};
                        for (const [key, value] of Object.entries(gunas)) {
                            gunaRows += `
                                <tr>
                                    <td><strong>${key}</strong></td>
                                    <td>${value}</td>
                                </tr>
                            `;
                        }

                        resultBox.innerHTML = `
                            <div class="result-card">
                                <div class="result-header">
                                    <div class="result-title">Energy Compatibility</div>
                                    <span class="result-badge">Ashta Kuta</span>
                                </div>
                                <div class="result-content">
                                    <div class="compatibility-display">
                                        <div class="score-circle-wrapper">
                                            <svg class="score-svg" width="150" height="150">
                                                <circle class="score-bg" cx="75" cy="75" r="60"></circle>
                                                <circle class="score-bar" cx="75" cy="75" r="60" 
                                                        stroke-dasharray="${circumference}" 
                                                        stroke-dashoffset="${offset}"></circle>
                                            </svg>
                                            <div class="score-text">
                                                <span class="score-num">${score}</span>
                                                <span class="score-max">/ ${maxScore}</span>
                                            </div>
                                        </div>
                                        
                                        <span class="verdict-badge ${verdictClass}">${data.verdict}</span>
                                    </div>
                                    
                                    <h4 class="margin-top-lg" style="font-size: 1rem; color: var(--color-white); font-weight: 700; border-left: 3px solid var(--color-gold); padding-left: 0.75rem;">Guna Matching Scorecard</h4>
                                    <div class="guna-table-wrapper">
                                        <table class="guna-table">
                                            <thead>
                                                <tr>
                                                    <th>Milap Koot</th>
                                                    <th>Obtained / Max Points</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${gunaRows}
                                            </tbody>
                                        </table>
                                    </div>

                                    <div class="match-advice">
                                        <h4><i class="fa-solid fa-lightbulb"></i> Compatibility Analysis</h4>
                                        <p style="margin: 0; font-size: 0.9rem; color: var(--color-text-secondary);">${data.alignment_advice}</p>
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        throw new Error(res.message || "Failed loading");
                    }
                })
                .catch(err => {
                    resultBox.innerHTML = `
                        <div class="empty-state">
                            <i class="fa-solid fa-circle-exclamation text-danger"></i>
                            <p>Error checking compatibility: ${err.message}. Make sure the backend is active.</p>
                        </div>
                    `;
                });
        });
    }

    // 8. Planet Positions Form Submission
    const planetPosForm = document.getElementById('planet-position-form');
    if (planetPosForm) {
        planetPosForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const dateVal = document.getElementById('planet-pos-date').value;
            const lat = document.getElementById('planet-pos-lat').value;
            const lng = document.getElementById('planet-pos-lng').value;
            const resultBox = document.getElementById('planet-position-result');

            showLoader('planet-position-result');

            const isoDt = `${dateVal}:00+05:30`;

            const planetPosPromise = fetch(`${apiBase}/astrology/planet-position?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}`).then(res => res.json());
            const natalChartPromise = fetch(`${apiBase}/astrology/natal-chart?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}`).then(res => res.json());

            Promise.all([planetPosPromise, natalChartPromise])
                .then(([planetRes, natalRes]) => {
                    if (planetRes.status === 'success' && planetRes.data) {
                        const data = planetRes.data;
                        const planets = data.planet_position || data.planetary_positions || [];

                        let planetRows = '';
                        planets.forEach(p => {
                            const name = p.name || p.planet || 'N/A';
                            
                            // Check Rasi info
                            let sign = 'N/A';
                            let lordInfo = 'N/A';
                            const rasi = p.rasi;
                            if (rasi && typeof rasi === 'object') {
                                sign = rasi.name || 'N/A';
                                const lordName = rasi.lord?.name || 'N/A';
                                const lordVedic = rasi.lord?.vedic_name || rasi.lord?.vedicName || 'N/A';
                                lordInfo = `${lordName} (${lordVedic})`;
                            } else {
                                sign = p.sign || 'N/A';
                            }

                            const deg = typeof p.degree === 'number' ? `${p.degree.toFixed(1)}°` : 'N/A';
                            const isRetro = p.is_retrograde || p.isRetrograde || false;
                            const retroBadge = isRetro 
                                ? '<span style="color: #ff5757; font-weight: 700; background: rgba(255,87,87,0.1); padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(255,87,87,0.2);">Retrograde</span>' 
                                : '<span style="color: #2ef56a; font-weight: 700; background: rgba(46,245,106,0.1); padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(46,245,106,0.2);">Direct</span>';

                            planetRows += `
                                <tr>
                                    <td><strong>${name}</strong></td>
                                    <td>${sign}</td>
                                    <td>${lordInfo}</td>
                                    <td>${deg}</td>
                                    <td>${retroBadge}</td>
                                </tr>
                            `;
                        });

                        let natalChartHtml = '';
                        if (natalRes.status === 'success' && natalRes.data && natalRes.data.svg) {
                            natalChartHtml = `
                                <div class="chart-section" style="display: flex; justify-content: center; background: rgba(0,0,0,0.15); padding: 1.5rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); margin-bottom: 2rem;">
                                    <div class="natal-chart-wheel-container click-expand-wheel" style="width: 100%; max-width: 440px; cursor: pointer; transition: transform 0.25s, box-shadow 0.25s;" title="Click to view full screen">
                                        ${natalRes.data.svg}
                                    </div>
                                </div>
                            `;
                        }

                        const aspects = data.aspects || [];
                        const planetSet = new Set();
                        planets.forEach(p => {
                            const name = p.name || p.planet;
                            if (name) planetSet.add(name);
                        });
                        let selectOptions = '<option value="all">All Objects</option>';
                        planetSet.forEach(pName => {
                            selectOptions += `<option value="${pName}">${pName}</option>`;
                        });

                        resultBox.innerHTML = `
                            <div class="result-card">
                                <div class="result-header">
                                    <div class="result-title">Celestial Placements & Aspects</div>
                                    <span class="result-badge">Positions & Aspects</span>
                                </div>
                                
                                <div class="aspects-tabs" style="display: flex; gap: 1.5rem; margin-top: 1rem; margin-bottom: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.5rem;">
                                    <button class="aspect-tab-btn active" data-target="placements-pane" style="background: none; border: none; color: #ffd700; font-family: Outfit; font-weight: 700; font-size: 0.95rem; cursor: pointer; padding-bottom: 0.5rem; border-bottom: 2px solid #ffd700; outline: none; transition: all 0.2s;">Planetary Positions</button>
                                    <button class="aspect-tab-btn" data-target="aspects-pane" style="background: none; border: none; color: var(--color-text-secondary); font-family: Outfit; font-weight: 500; font-size: 0.95rem; cursor: pointer; padding-bottom: 0.5rem; outline: none; transition: all 0.2s;">Planetary Aspects</button>
                                </div>
                                
                                <div id="placements-pane" class="aspects-pane-content">
                                    ${natalChartHtml}
                                    <div class="planet-table-wrapper">
                                        <table class="planet-table">
                                            <thead>
                                                <tr>
                                                    <th>Body / Planet</th>
                                                    <th>Zodiac Sign</th>
                                                    <th>Rasi Lord (Vedic)</th>
                                                    <th>Degree</th>
                                                    <th>Status</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${planetRows || '<tr><td colspan="5">No positions returned.</td></tr>'}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                
                                <div id="aspects-pane" class="aspects-pane-content" style="display: none;">
                                    <div class="aspect-filters" style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; align-items: center; background: rgba(0,0,0,0.1); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.02);">
                                        <div style="display: flex; gap: 0.5rem;">
                                            <button class="filter-type-btn active" data-type="all" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); color: #fff; padding: 0.35rem 0.9rem; border-radius: 6px; font-size: 0.8rem; font-family: Outfit; font-weight: 600; cursor: pointer; transition: all 0.2s;">All Aspects</button>
                                            <button class="filter-type-btn" data-type="major" style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); color: var(--color-text-secondary); padding: 0.35rem 0.9rem; border-radius: 6px; font-size: 0.8rem; font-family: Outfit; font-weight: 500; cursor: pointer; transition: all 0.2s;">Major Only</button>
                                            <button class="filter-type-btn" data-type="minor" style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); color: var(--color-text-secondary); padding: 0.35rem 0.9rem; border-radius: 6px; font-size: 0.8rem; font-family: Outfit; font-weight: 500; cursor: pointer; transition: all 0.2s;">Minor Only</button>
                                        </div>
                                        
                                        <div style="display: flex; align-items: center; gap: 0.6rem; margin-left: auto;">
                                            <label style="font-size: 0.8rem; color: var(--color-text-secondary); font-family: Outfit; font-weight: 500;">Filter by Planet:</label>
                                            <select id="aspect-planet-filter" style="background: #0d0826; border: 1px solid rgba(255,255,255,0.15); color: #fff; border-radius: 6px; padding: 0.35rem 0.75rem; font-size: 0.8rem; font-family: Outfit; outline: none; cursor: pointer;">
                                                ${selectOptions}
                                            </select>
                                        </div>
                                    </div>
                                    
                                    <div class="planet-table-wrapper">
                                        <table class="planet-table">
                                            <thead>
                                                <tr>
                                                    <th>Planet 1</th>
                                                    <th>Aspect</th>
                                                    <th>Planet 2</th>
                                                    <th>Type</th>
                                                    <th>Exact Diff</th>
                                                    <th>Orb</th>
                                                </tr>
                                            </thead>
                                            <tbody id="aspects-table-body">
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        `;

                        const tabButtons = resultBox.querySelectorAll('.aspect-tab-btn');
                        const panes = resultBox.querySelectorAll('.aspects-pane-content');
                        
                        tabButtons.forEach(btn => {
                            btn.addEventListener('click', () => {
                                tabButtons.forEach(b => {
                                    b.classList.remove('active');
                                    b.style.color = 'var(--color-text-secondary)';
                                    b.style.fontWeight = '500';
                                    b.style.borderBottom = 'none';
                                });
                                btn.classList.add('active');
                                btn.style.color = '#ffd700';
                                btn.style.fontWeight = '700';
                                btn.style.borderBottom = '2px solid #ffd700';
                                
                                const target = btn.getAttribute('data-target');
                                panes.forEach(pane => {
                                    if (pane.id === target) {
                                        pane.style.display = 'block';
                                    } else {
                                        pane.style.display = 'none';
                                    }
                                });
                            });
                        });
                        
                        const typeButtons = resultBox.querySelectorAll('.filter-type-btn');
                        const planetFilterSelect = resultBox.querySelector('#aspect-planet-filter');
                        const aspectsTbody = resultBox.querySelector('#aspects-table-body');
                        
                        let activeType = 'all';
                        let activePlanet = 'all';
                        
                        function renderFilteredAspects() {
                            let filtered = aspects;
                            if (activeType !== 'all') {
                                filtered = filtered.filter(a => a.type === activeType);
                            }
                            if (activePlanet !== 'all') {
                                filtered = filtered.filter(a => a.planet_one === activePlanet || a.planet_two === activePlanet);
                            }
                            
                            let html = '';
                            if (filtered.length === 0) {
                                html = '<tr><td colspan="6" style="text-align: center; opacity: 0.6; padding: 2rem 0;">No matching aspects found for the selected filters.</td></tr>';
                            } else {
                                filtered.forEach(a => {
                                    const typeBadge = a.type === 'major' 
                                        ? '<span style="color: #ffd700; background: rgba(255,215,0,0.08); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(255,215,0,0.15); font-weight: 600;">Major</span>'
                                        : '<span style="color: #a0aec0; background: rgba(255,255,255,0.05); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(255,255,255,0.1); font-weight: 500;">Minor</span>';
                                    
                                    html += `
                                        <tr>
                                            <td><strong>${a.planet_one}</strong></td>
                                            <td style="color: #00d2ff; font-weight: 600;">${a.aspect_name}</td>
                                            <td><strong>${a.planet_two}</strong></td>
                                            <td>${typeBadge}</td>
                                            <td>${a.exact_diff.toFixed(1)}°</td>
                                            <td>${a.orb.toFixed(1)}°</td>
                                        </tr>
                                    `;
                                });
                            }
                            aspectsTbody.innerHTML = html;
                        }
                        
                        typeButtons.forEach(btn => {
                            btn.addEventListener('click', () => {
                                typeButtons.forEach(b => {
                                    b.classList.remove('active');
                                    b.style.background = 'rgba(0,0,0,0.2)';
                                    b.style.border = '1px solid rgba(255,255,255,0.05)';
                                    b.style.color = 'var(--color-text-secondary)';
                                    b.style.fontWeight = '500';
                                });
                                btn.classList.add('active');
                                btn.style.background = 'rgba(255,255,255,0.06)';
                                btn.style.border = '1px solid rgba(255,255,255,0.12)';
                                btn.style.color = '#fff';
                                btn.style.fontWeight = '600';
                                
                                activeType = btn.getAttribute('data-type');
                                renderFilteredAspects();
                            });
                        });
                        
                        if (planetFilterSelect) {
                            planetFilterSelect.addEventListener('change', (e) => {
                                activePlanet = e.target.value;
                                renderFilteredAspects();
                            });
                        }
                        
                        renderFilteredAspects();
                    } else {
                        throw new Error(planetRes.message || "Failed retrieving planet positions");
                    }
                })
                .catch(err => {
                    resultBox.innerHTML = `
                        <div class="empty-state">
                            <i class="fa-solid fa-circle-exclamation text-danger"></i>
                            <p>Error calculating planet positions: ${err.message}. Make sure the backend is active.</p>
                        </div>
                    `;
                });
        });
    }

    // 9. Western Natal Chart Form Submission
    const natalChartForm = document.getElementById('natal-chart-form');
    if (natalChartForm) {
        natalChartForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const dateVal = document.getElementById('natal-chart-date').value;
            const lat = document.getElementById('natal-chart-lat').value;
            const lng = document.getElementById('natal-chart-lng').value;
            const resultBox = document.getElementById('natal-chart-result');

            showLoader('natal-chart-result');

            const isoDt = `${dateVal}:00+05:30`;

            fetch(`${apiBase}/astrology/natal-chart?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}`)
                .then(res => res.json())
                .then(res => {
                    if (res.status === 'success' && res.data && res.data.svg) {
                        resultBox.innerHTML = `
                            <div class="result-card" style="width: 100%; display: flex; flex-direction: column; align-items: center;">
                                <div class="result-header" style="width: 100%;">
                                    <div class="result-title">Western Natal Wheel</div>
                                    <span class="result-badge">Natal Chart</span>
                                </div>
                                <div class="result-content" style="width: 100%; display: flex; justify-content: center; background: rgba(0,0,0,0.15); padding: 1.5rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03);">
                                    <div class="natal-chart-wheel-container click-expand-wheel" style="width: 100%; max-width: 480px; cursor: pointer; transition: transform 0.25s, box-shadow 0.25s;" title="Click to view full screen">
                                        ${res.data.svg}
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        throw new Error(res.message || "Failed retrieving natal chart SVG");
                    }
                })
                .catch(err => {
                    resultBox.innerHTML = `
                        <div class="empty-state">
                            <i class="fa-solid fa-circle-exclamation text-danger"></i>
                            <p>Error generating natal chart: ${err.message}. Make sure the backend is active.</p>
                        </div>
                    `;
                });
        });
    }

    // 10. Natal Chart Lightbox Modal Logic
    const lightboxModal = document.getElementById('chart-lightbox-modal');
    const lightboxBody = document.getElementById('lightbox-modal-body');
    const closeLightboxBtn = document.getElementById('close-lightbox-modal');
    const closeLightboxBackdrop = document.getElementById('close-lightbox-backdrop');

    document.addEventListener('click', (e) => {
        const expandContainer = e.target.closest('.click-expand-wheel');
        if (expandContainer) {
            const svgContent = expandContainer.innerHTML;
            if (lightboxBody && lightboxModal) {
                lightboxBody.innerHTML = svgContent;
                const modalSvg = lightboxBody.querySelector('svg');
                if (modalSvg) {
                    modalSvg.style.width = '100%';
                    modalSvg.style.height = '100%';
                    modalSvg.style.maxWidth = '100%';
                    modalSvg.style.maxHeight = '100%';
                }
                lightboxModal.classList.add('active');
            }
        }
    });

    const closeLightbox = () => {
        if (lightboxModal) {
            lightboxModal.classList.remove('active');
        }
    };

    if (closeLightboxBtn) closeLightboxBtn.addEventListener('click', closeLightbox);
    if (closeLightboxBackdrop) closeLightboxBackdrop.addEventListener('click', closeLightbox);

});
