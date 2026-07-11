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

    const getDualPlanetName = (name) => {
        const glyphMap = {
            'Sun': '☉', 'Moon': '☽', 'Mars': '♂', 'Mercury': '☿', 'Jupiter': '♃', 
            'Venus': '♀', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇', 
            'True North Node': '☊', 'True South Node': '☋', 'North Node': '☊', 'South Node': '☋',
            'Rahu': '☊', 'Ketu': '☋', 'Ascendant': 'ASC', 'Lilith': '⚳', 'Chiron': '⚷'
        };
        const hiMap = {
            'Sun': 'सूर्य', 'Moon': 'चंद्र', 'Mars': 'मंगल', 'Mercury': 'बुध', 'Jupiter': 'बृहस्पति (गुरु)', 
            'Venus': 'शुक्र', 'Saturn': 'शनि', 'Rahu': 'राहु', 'Ketu': 'केतु', 'Uranus': 'अरुण (यूरेनस)', 
            'Neptune': 'वरुण (नेप्च्यून)', 'Pluto': 'यम (प्लूटो)', 'Ascendant': 'लग्न',
            'True North Node': 'उत्तरी ध्रुव / राहू', 'True South Node': 'दक्षिणी ध्रुव / केतु',
            'North Node': 'उत्तरी ध्रुव / राहू', 'South Node': 'दक्षिणी ध्रुव / केतु'
        };
        const glyph = glyphMap[name] || '';
        const hiName = hiMap[name] || name;
        const displayName = name !== hiName ? `${name} (${hiName})` : name;
        return glyph ? `<span style="font-size: 1.1rem; color: #ffd700; margin-right: 0.5rem; vertical-align: middle; line-height: 1;">${glyph}</span>${displayName}` : displayName;
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

    // 3. Location Geocoding & Geolocation Autofill
    const searchInputs = document.querySelectorAll('.location-search-input');
    const detectGpsBtns = document.querySelectorAll('.detect-gps-btn');

    function debounce(func, delay) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => func.apply(this, args), delay);
        };
    }

    searchInputs.forEach(input => {
        const dropdown = input.parentNode.querySelector('.geocoding-results-dropdown');
        if (!dropdown) return;
        
        const handleSearch = async (e) => {
            const query = e.target.value.trim();
            if (query.length < 3) {
                dropdown.style.display = 'none';
                dropdown.innerHTML = '';
                return;
            }

            try {
                const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`);
                const data = await res.json();
                
                if (data && data.length > 0) {
                    dropdown.innerHTML = data.map(item => {
                        return `
                            <div class="dropdown-item" 
                                 data-lat="${parseFloat(item.lat).toFixed(4)}" 
                                 data-lon="${parseFloat(item.lon).toFixed(4)}" 
                                 data-name="${item.display_name.replace(/"/g, '&quot;')}"
                                 style="padding: 0.5rem 1rem; font-size: 0.82rem; color: #fff; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.03); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-family: Outfit;"
                                 onmouseover="this.style.background='rgba(212,175,55,0.1)'"
                                 onmouseout="this.style.background='transparent'">
                                <i class="fa-solid fa-location-dot" style="color: #ffd700; margin-right: 0.5rem; font-size: 0.75rem;"></i>
                                ${item.display_name}
                            </div>
                        `;
                    }).join('');
                    dropdown.style.display = 'block';
                } else {
                    dropdown.innerHTML = `<div style="padding: 0.5rem 1rem; font-size: 0.8rem; color: var(--color-text-secondary); text-align: center;">No cities found</div>`;
                    dropdown.style.display = 'block';
                }
            } catch (err) {
                console.error("Geocoding error:", err);
            }
        };

        input.addEventListener('input', debounce(handleSearch, 400));

        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        dropdown.addEventListener('click', (e) => {
            const item = e.target.closest('.dropdown-item');
            if (item) {
                const lat = item.getAttribute('data-lat');
                const lon = item.getAttribute('data-lon');
                const name = item.getAttribute('data-name');
                
                input.value = name;
                dropdown.style.display = 'none';
                
                const form = input.closest('form') || input.closest('.partner-panel');
                if (form) {
                    const latInput = form.querySelector('[id$="lat"]');
                    const lngInput = form.querySelector('[id$="lng"]');
                    if (latInput) latInput.value = lat;
                    if (lngInput) lngInput.value = lon;
                }
            }
        });
    });

    detectGpsBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const icon = btn.querySelector('i');
            const originalClass = icon.className;
            
            icon.className = 'fa-solid fa-spinner fa-spin';
            btn.disabled = true;
            btn.style.opacity = '0.7';

            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const lat = position.coords.latitude.toFixed(4);
                    const lng = position.coords.longitude.toFixed(4);
                    
                    const form = btn.closest('form') || btn.closest('.partner-panel');
                    if (form) {
                        const latInput = form.querySelector('[id$="lat"]');
                        const lngInput = form.querySelector('[id$="lng"]');
                        const searchInput = form.querySelector('.location-search-input');
                        
                        if (latInput) latInput.value = lat;
                        if (lngInput) lngInput.value = lng;
                        
                        if (searchInput) {
                            searchInput.value = `Current Location (${lat}, ${lng})`;
                            try {
                                const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
                                const data = await res.json();
                                if (data && data.display_name) {
                                    searchInput.value = data.display_name;
                                }
                            } catch (e) {
                                console.warn("Reverse geocode failed:", e);
                            }
                        }
                    }
                    
                    icon.className = originalClass;
                    btn.disabled = false;
                    btn.style.opacity = '1';
                },
                (err) => {
                    console.error("GPS detection error:", err);
                    alert(`Unable to retrieve GPS coordinates: ${err.message}. Please enter manually or grant browser location permission.`);
                    
                    icon.className = originalClass;
                    btn.disabled = false;
                    btn.style.opacity = '1';
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
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

                fetch(`${apiBase}/horoscope/daily?sign=${sign}&la=${currentLang}`)
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

            fetch(`${apiBase}/astrology/panchang?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}&la=${currentLang}`)
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

            fetch(`${apiBase}/astrology/kundli?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}&la=${currentLang}`)
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

            fetch(`${apiBase}/astrology/kundli-matching?girl_dob=${encodeURIComponent(gIso)}&girl_latitude=${gLat}&girl_longitude=${gLng}&boy_dob=${encodeURIComponent(bIso)}&boy_coordinates=${bLat}&boy_longitude=${bLng}&la=${currentLang}`)
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
            const zodiacSys = document.getElementById('planet-pos-zodiac').value;
            const resultBox = document.getElementById('planet-position-result');

            showLoader('planet-position-result');

            const isoDt = `${dateVal}:00+05:30`;

            const planetPosPromise = fetch(`${apiBase}/astrology/planet-position?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}&ayanamsa=${zodiacSys}&la=${currentLang}`).then(res => res.json());
            const natalChartPromise = fetch(`${apiBase}/astrology/natal-chart?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}&ayanamsa=${zodiacSys}&la=${currentLang}`).then(res => res.json());

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
                            const retroText = isRetro ? translateText('Retrograde') : translateText('Direct');
                            const retroBadge = isRetro 
                                ? `<span style="color: #ff5757; font-weight: 700; background: rgba(255,87,87,0.1); padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(255,87,87,0.2);">${retroText}</span>` 
                                : `<span style="color: #2ef56a; font-weight: 700; background: rgba(46,245,106,0.1); padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(46,245,106,0.2);">${retroText}</span>`;

                            planetRows += `
                                <tr>
                                    <td><strong>${getDualPlanetName(name)}</strong></td>
                                    <td>${translateText(sign)}</td>
                                    <td>${translateText(lordInfo)}</td>
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
                                
                                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.04); border-radius: 8px; padding: 0.8rem 1.2rem; margin-top: 1rem; display: flex; flex-wrap: wrap; gap: 1rem; justify-content: space-between; font-family: Outfit; font-size: 0.85rem; color: var(--color-text-secondary);">
                                    <div>
                                        <i class="fa-regular fa-clock" style="color: #ffd700; margin-right: 0.4rem;"></i>
                                        <strong>Birth Time:</strong> ${dateVal.replace('T', ' ')}
                                    </div>
                                    <div>
                                        <i class="fa-solid fa-earth-americas" style="color: #ffd700; margin-right: 0.4rem;"></i>
                                        <strong>Location:</strong> ${lat}°, ${lng}°
                                    </div>
                                    <div>
                                        <i class="fa-solid fa-compass" style="color: #ffd700; margin-right: 0.4rem;"></i>
                                        <strong>System:</strong> ${zodiacSys === '0' ? 'Tropical (Western)' : 'Sidereal Lahiri (Vedic)'}
                                    </div>
                                </div>
                                
                                <div class="aspects-tabs" style="display: flex; gap: 1.5rem; margin-top: 1.5rem; margin-bottom: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.5rem; flex-wrap: wrap;">
                                    <button class="aspect-tab-btn active" data-target="placements-pane" style="background: none; border: none; color: #ffd700; font-family: Outfit; font-weight: 700; font-size: 0.95rem; cursor: pointer; padding-bottom: 0.5rem; border-bottom: 2px solid #ffd700; outline: none; transition: all 0.2s;">Planetary Positions</button>
                                    <button class="aspect-tab-btn" data-target="aspects-pane" style="background: none; border: none; color: var(--color-text-secondary); font-family: Outfit; font-weight: 500; font-size: 0.95rem; cursor: pointer; padding-bottom: 0.5rem; outline: none; transition: all 0.2s;">Planetary Aspects</button>
                                    <button class="aspect-tab-btn" data-target="history-pane" id="load-history-tab-btn" style="background: none; border: none; color: var(--color-text-secondary); font-family: Outfit; font-weight: 500; font-size: 0.95rem; cursor: pointer; padding-bottom: 0.5rem; outline: none; transition: all 0.2s;">History of every 15 min</button>
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
                                
                                <div id="history-pane" class="aspects-pane-content" style="display: none;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem; flex-wrap: wrap; gap: 0.6rem;">
                                        <h4 style="font-family: Outfit; color: #ffd700; margin: 0; font-size: 1.1rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
                                            <i class="fa-solid fa-clock-rotate-left"></i> History of Every 15 Min (Last 2 Months)
                                        </h4>
                                        <span style="font-size: 0.75rem; color: var(--color-text-secondary); background: rgba(255,255,255,0.05); padding: 0.2rem 0.5rem; border-radius: 4px;">4 intervals per hour going back</span>
                                    </div>
                                    
                                    <div class="planet-table-wrapper" style="max-height: 480px; overflow-y: auto; width: 100%;">
                                        <table class="planet-table" style="width: 100%; border-collapse: collapse;">
                                            <thead>
                                                <tr>
                                                    <th style="padding: 0.6rem 0.8rem; text-align: left;">Date & Time</th>
                                                    <th style="padding: 0.6rem 0.8rem; text-align: left;">ASC (Lagna)</th>
                                                    <th style="padding: 0.6rem 0.8rem; text-align: left;">☉ Sun (सूर्य)</th>
                                                    <th style="padding: 0.6rem 0.8rem; text-align: left;">☽ Moon (चंद्र)</th>
                                                    <th style="padding: 0.6rem 0.8rem; text-align: left;">☿ Mercury (बुध)</th>
                                                    <th style="padding: 0.6rem 0.8rem; text-align: left;">♀ Venus (शुक्र)</th>
                                                    <th style="padding: 0.6rem 0.8rem; text-align: left;">♂ Mars (मंगल)</th>
                                                    <th style="padding: 0.6rem 0.8rem; text-align: left;">☊ N.Node (राहू)</th>
                                                    <th style="padding: 0.6rem 0.8rem; text-align: left;">☋ S.Node (केतु)</th>
                                                </tr>
                                            </thead>
                                            <tbody id="history-table-body">
                                                <tr>
                                                    <td colspan="9" style="text-align: center; opacity: 0.6; padding: 2rem 0;">
                                                        <i class="fa-solid fa-spinner fa-spin" style="margin-right: 0.5rem; color: #ffd700;"></i> Loading transit history...
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                    <div style="display: flex; justify-content: center; margin-top: 1.2rem;">
                                        <button id="history-load-more-btn" style="background: rgba(255,215,0,0.1); border: 1px solid rgba(255,215,0,0.3); color: #ffd700; border-radius: 6px; padding: 0.5rem 1.5rem; font-family: Outfit; font-size: 0.85rem; font-weight: 700; cursor: pointer; transition: all 0.2s; display: none; outline: none;">Load More Intervals</button>
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
                        
                        // Load More History Logic
                        let historyOffset = 0;
                        const historyLimit = 50;
                        const historyTbody = resultBox.querySelector('#history-table-body');
                        const loadMoreBtn = resultBox.querySelector('#history-load-more-btn');
                        const historyTabBtn = resultBox.querySelector('#load-history-tab-btn');

                        const fetchHistoryData = () => {
                            fetch(`${apiBase}/astrology/transit-history?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}&ayanamsa=${zodiacSys}&limit=${historyLimit}&offset=${historyOffset}`)
                                .then(res => res.json())
                                .then(res => {
                                    if (res.status === 'success' && res.data && res.data.history) {
                                        let rowsHtml = '';
                                        res.data.history.forEach(item => {
                                            const p = item.planets;
                                            
                                            const getColHtml = (pName) => {
                                                const pData = p[pName];
                                                if (!pData) return '<td>N/A</td>';
                                                
                                                const glyphMap = {
                                                    'Sun': '☉', 'Moon': '☽', 'Mars': '♂', 'Mercury': '☿', 'Jupiter': '♃', 
                                                    'Venus': '♀', 'Saturn': '♄', 'True North Node': '☊', 'True South Node': '☋',
                                                    'Ascendant': 'ASC', 'Midheaven': 'MC'
                                                };
                                                const glyph = glyphMap[pName] || '';
                                                const glyphPrefix = glyph ? `<span style="color: #ffd700; font-size: 0.95rem; margin-right: 0.35rem; vertical-align: middle;">${glyph}</span>` : '';
                                                return `<td style="padding: 0.6rem 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.02);">${glyphPrefix}${translateText(pData.sign)} ${pData.degree.toFixed(1)}°</td>`;
                                            };
                                            
                                            rowsHtml += `
                                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                                                    <td style="padding: 0.6rem 0.8rem; color: #ffd700; font-weight: 600; border-bottom: 1px solid rgba(255,255,255,0.02);">${item.datetime}</td>
                                                    ${getColHtml('Ascendant')}
                                                    ${getColHtml('Sun')}
                                                    ${getColHtml('Moon')}
                                                    ${getColHtml('Mercury')}
                                                    ${getColHtml('Venus')}
                                                    ${getColHtml('Mars')}
                                                    ${getColHtml('True North Node')}
                                                    ${getColHtml('True South Node')}
                                                </tr>
                                            `;
                                        });

                                        if (historyOffset === 0) {
                                            historyTbody.innerHTML = rowsHtml;
                                        } else {
                                            historyTbody.innerHTML += rowsHtml;
                                        }

                                        historyOffset += historyLimit;
                                        if (res.data.has_more) {
                                            loadMoreBtn.style.display = 'block';
                                        } else {
                                            loadMoreBtn.style.display = 'none';
                                        }
                                    } else {
                                        if (historyOffset === 0) {
                                            historyTbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: red; padding: 1rem;">Failed to load history data.</td></tr>';
                                        }
                                    }
                                })
                                .catch(err => {
                                    console.error("Error loading history:", err);
                                    if (historyOffset === 0) {
                                        historyTbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: red; padding: 1rem;">Error: ' + err.message + '</td></tr>';
                                    }
                                });
                        };

                        if (historyTabBtn) {
                            historyTabBtn.addEventListener('click', () => {
                                if (historyOffset === 0) {
                                    fetchHistoryData();
                                }
                            });
                        }

                        if (loadMoreBtn) {
                            loadMoreBtn.addEventListener('click', fetchHistoryData);
                        }
                        
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
                                    
                                    const p1Data = (window.currentPlanetsData || []).find(p => (p.name || p.planet) === a.planet_one);
                                    const p2Data = (window.currentPlanetsData || []).find(p => (p.name || p.planet) === a.planet_two);
                                    
                                    let p1Sign = '';
                                    if (p1Data) {
                                        const s = p1Data.rasi?.name || p1Data.sign || '';
                                        if (s) p1Sign = ` <span style="font-size: 0.8rem; color: var(--color-text-secondary); font-weight: 500;">(${translateText(s)})</span>`;
                                    }
                                    let p2Sign = '';
                                    if (p2Data) {
                                        const s = p2Data.rasi?.name || p2Data.sign || '';
                                        if (s) p2Sign = ` <span style="font-size: 0.8rem; color: var(--color-text-secondary); font-weight: 500;">(${translateText(s)})</span>`;
                                    }

                                    html += `
                                        <tr>
                                            <td><strong>${getDualPlanetName(a.planet_one)}</strong>${p1Sign}</td>
                                            <td style="color: #00d2ff; font-weight: 600;">${translateText(a.aspect_name)}</td>
                                            <td><strong>${getDualPlanetName(a.planet_two)}</strong>${p2Sign}</td>
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
            const zodiacSys = document.getElementById('natal-chart-zodiac').value;
            const resultBox = document.getElementById('natal-chart-result');

            showLoader('natal-chart-result');

            const isoDt = `${dateVal}:00+05:30`;

            const planetPosPromise = fetch(`${apiBase}/astrology/planet-position?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}&ayanamsa=${zodiacSys}&la=${currentLang}`).then(res => res.json());
            const natalChartPromise = fetch(`${apiBase}/astrology/natal-chart?datetime=${encodeURIComponent(isoDt)}&latitude=${lat}&longitude=${lng}&ayanamsa=${zodiacSys}&la=${currentLang}`).then(res => res.json());

            Promise.all([planetPosPromise, natalChartPromise])
                .then(([planetRes, natalRes]) => {
                    if (planetRes.status === 'success' && planetRes.data) {
                        window.currentPlanetsData = planetRes.data.planet_position || planetRes.data.planetary_positions || [];
                    }

                    if (natalRes.status === 'success' && natalRes.data && natalRes.data.svg) {
                        // Generate planetary positions rows specifically for the natal wheel view
                        let planetRows = '';
                        if (window.currentPlanetsData) {
                            window.currentPlanetsData.forEach(p => {
                                const name = p.name || p.planet || 'N/A';
                                let sign = 'N/A';
                                const rasi = p.rasi;
                                if (rasi && typeof rasi === 'object') {
                                    sign = rasi.name || 'N/A';
                                } else {
                                    sign = p.sign || 'N/A';
                                }

                                const deg = typeof p.degree === 'number' ? `${p.degree.toFixed(1)}°` : 'N/A';
                                const isRetro = p.is_retrograde || p.isRetrograde || false;
                                const retroText = isRetro ? translateText('Retrograde') : translateText('Direct');
                                const retroBadge = isRetro 
                                    ? `<span style="color: #ff5757; font-weight: 700; background: rgba(255,87,87,0.1); padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(255,87,87,0.2);">${retroText}</span>` 
                                    : `<span style="color: #2ef56a; font-weight: 700; background: rgba(46,245,106,0.1); padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(46,245,106,0.2);">${retroText}</span>`;

                                planetRows += `
                                    <tr>
                                        <td style="padding: 0.6rem 0.8rem;"><strong>${getDualPlanetName(name)}</strong></td>
                                        <td style="padding: 0.6rem 0.8rem;"><strong>${translateText(sign)}</strong></td>
                                        <td style="padding: 0.6rem 0.8rem;">${deg}</td>
                                        <td style="padding: 0.6rem 0.8rem;">${retroBadge}</td>
                                    </tr>
                                `;
                            });
                        }

                        resultBox.innerHTML = `
                            <div class="result-card" style="width: 100%;">
                                <div class="result-header">
                                    <div class="result-title">Western Natal Wheel & Placements</div>
                                    <span class="result-badge">Natal Chart</span>
                                </div>
                                
                                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.04); border-radius: 8px; padding: 0.8rem 1.2rem; margin-top: 1rem; display: flex; flex-wrap: wrap; gap: 1rem; justify-content: space-between; font-family: Outfit; font-size: 0.85rem; color: var(--color-text-secondary);">
                                    <div>
                                        <i class="fa-regular fa-clock" style="color: #ffd700; margin-right: 0.4rem;"></i>
                                        <strong>Birth Time:</strong> ${dateVal.replace('T', ' ')}
                                    </div>
                                    <div>
                                        <i class="fa-solid fa-earth-americas" style="color: #ffd700; margin-right: 0.4rem;"></i>
                                        <strong>Location:</strong> ${lat}°, ${lng}°
                                    </div>
                                    <div>
                                        <i class="fa-solid fa-compass" style="color: #ffd700; margin-right: 0.4rem;"></i>
                                        <strong>System:</strong> ${zodiacSys === '0' ? 'Tropical (Western)' : 'Sidereal Lahiri (Vedic)'}
                                    </div>
                                </div>

                                <div style="display: flex; flex-direction: row; gap: 2rem; margin-top: 1.5rem; flex-wrap: wrap; width: 100%;">
                                    <!-- Left: Wheel Chart SVG -->
                                    <div style="flex: 1; min-width: 320px; display: flex; justify-content: center; background: rgba(0,0,0,0.15); padding: 1.5rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); align-items: center; box-sizing: border-box;">
                                        <div class="natal-chart-wheel-container click-expand-wheel" style="width: 100%; max-width: 440px; cursor: pointer; transition: transform 0.25s, box-shadow 0.25s;" title="Click to view full screen">
                                            ${natalRes.data.svg}
                                        </div>
                                    </div>

                                    <!-- Right: Planet placements table -->
                                    <div style="flex: 1.2; min-width: 320px; display: flex; flex-direction: column; gap: 1rem; box-sizing: border-box;">
                                        <h4 style="font-family: Outfit; color: #ffd700; margin: 0; font-size: 1.1rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
                                            <i class="fa-solid fa-table-list" style="font-size: 0.95rem;"></i> Planetary Sign Placements
                                        </h4>
                                        <div class="planet-table-wrapper" style="max-height: 440px; overflow-y: auto; width: 100%;">
                                            <table class="planet-table" style="width: 100%; border-collapse: collapse;">
                                                <thead>
                                                    <tr>
                                                        <th style="text-align: left; padding: 0.6rem 0.8rem;">Planet</th>
                                                        <th style="text-align: left; padding: 0.6rem 0.8rem;">Zodiac Sign</th>
                                                        <th style="text-align: left; padding: 0.6rem 0.8rem;">Degree</th>
                                                        <th style="text-align: left; padding: 0.6rem 0.8rem;">Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${planetRows || '<tr><td colspan="4" style="text-align: center; opacity: 0.6; padding: 1rem;">No placements returned.</td></tr>'}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        throw new Error(natalRes.message || "Failed retrieving natal chart SVG");
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
    const wheelContainer = document.getElementById('lightbox-wheel-container');
    const magnifierDefault = document.getElementById('magnifier-default-state');
    const magnifierActive = document.getElementById('magnifier-active-state');
    const closeLightboxBtn = document.getElementById('close-lightbox-modal');
    const closeLightboxBackdrop = document.getElementById('close-lightbox-backdrop');

    document.addEventListener('click', (e) => {
        const expandContainer = e.target.closest('.click-expand-wheel');
        if (expandContainer) {
            const svgContent = expandContainer.innerHTML;
            if (wheelContainer && lightboxModal) {
                wheelContainer.innerHTML = svgContent;
                const modalSvg = wheelContainer.querySelector('svg');
                if (modalSvg) {
                    modalSvg.style.width = '100%';
                    modalSvg.style.height = '100%';
                    modalSvg.style.maxWidth = '100%';
                    modalSvg.style.maxHeight = '100%';
                }
                // Reset magnifier to default state
                if (magnifierDefault) magnifierDefault.style.display = 'block';
                if (magnifierActive) magnifierActive.style.display = 'none';
                
                lightboxModal.classList.add('active');
            }
        }
    });

    // 11. Zodiac Sector Clicking, Magnification, and Multiple Selector Aspect Filtering Logic
    const selectedSigns = new Set();

    const updateRashiHighlightsAndAspectLines = (svgElement) => {
        if (!svgElement) return;
        console.log("[Rashi Selector] Updating highlights and aspect lines for SVG. Selected signs:", [...selectedSigns]);

        // 1. Update Rashi Highlight Styles dynamically via injected CSS rules
        let styleEl = document.getElementById('rashi-highlight-styles');
        if (!styleEl) {
            styleEl = document.createElement('style');
            styleEl.id = 'rashi-highlight-styles';
            document.head.appendChild(styleEl);
        }

        if (selectedSigns.size > 0) {
            const rules = [...selectedSigns].map(sign => `
                /* Highlight the selected sectors in both Mock and Live SVGs */
                .natal-chart-wheel-container svg g.${sign.toLowerCase()},
                .natal-chart-wheel-container svg path.${sign.toLowerCase()},
                .natal-chart-wheel-container svg text.${sign.toLowerCase()},
                .natal-chart-wheel-container svg .pk-zodiac-${sign.toLowerCase()},
                #lightbox-wheel-container svg g.${sign.toLowerCase()},
                #lightbox-wheel-container svg path.${sign.toLowerCase()},
                #lightbox-wheel-container svg text.${sign.toLowerCase()},
                #lightbox-wheel-container svg .pk-zodiac-${sign.toLowerCase()} {
                    fill: rgba(255, 215, 0, 0.16) !important;
                    stroke: rgba(255, 215, 0, 0.4) !important;
                    stroke-width: 1px !important;
                    opacity: 1 !important;
                }
            `).join('\n');
            styleEl.innerHTML = rules;
        } else {
            styleEl.innerHTML = '';
        }

        // 2. Filter aspect lines in the SVG
        const aspectLines = svgElement.querySelectorAll('.pk-planet-aspect, line');
        console.log("[Rashi Selector] Found aspect/line elements count:", aspectLines.length);
        aspectLines.forEach(line => {
            const classAttr = line.getAttribute('class') || '';
            const classes = classAttr.split(/\s+/);
            const isProkeralaAspect = classes.includes('pk-planet-aspect');
            const isMockAspect = !line.closest('.svg-planet-marker') && !line.closest('.pk-zodiac') && line.getAttribute('x1') && parseFloat(line.getAttribute('x1')) !== 500 && line.parentElement && line.parentElement.tagName === 'g' && line.getAttribute('stroke') && line.getAttribute('stroke') !== '#d4af37';
            
            if (isProkeralaAspect || isMockAspect) {
                if (selectedSigns.size === 0) {
                    line.style.display = 'block';
                    line.style.opacity = '0.65';
                } else {
                    if (isProkeralaAspect) {
                        // Check if the aspect line has any class matching a selected sign
                        const hasMatch = classes.some(c => c.startsWith('pk-zodiac-') && selectedSigns.has(c.replace('pk-zodiac-', '').charAt(0).toUpperCase() + c.replace('pk-zodiac-', '').slice(1)));
                        if (hasMatch) {
                            line.style.display = 'block';
                            line.style.opacity = '1.0';
                        } else {
                            line.style.display = 'none';
                        }
                    } else if (isMockAspect) {
                        line.style.display = 'block';
                    }
                }
            }
        });
    };

    document.addEventListener('click', (e) => {
        // Find which sign was clicked in the SVG (either by class list starting with pk-zodiac-, or dataset data-sign)
        let clickedSignElement = e.target;
        let sign = null;
        
        while (clickedSignElement && clickedSignElement.tagName !== 'svg') {
            const classAttr = clickedSignElement.getAttribute('class') || '';
            const classes = classAttr.split(/\s+/);
            const match = classes.find(c => c.startsWith('pk-zodiac-') && c !== 'pk-zodiac-outer' && c !== 'pk-zodiac-layer' && c !== 'pk-zodiac-path');
            if (match) {
                const rawSign = match.replace('pk-zodiac-', '');
                sign = rawSign.charAt(0).toUpperCase() + rawSign.slice(1);
                break;
            }
            if (clickedSignElement.getAttribute('data-sign')) {
                sign = clickedSignElement.getAttribute('data-sign');
                sign = sign.charAt(0).toUpperCase() + sign.slice(1);
                break;
            }
            clickedSignElement = clickedSignElement.parentElement;
        }

        if (sign && magnifierDefault && magnifierActive) {
            console.log("[Rashi Click] Rashi clicked:", sign);
            
            // If the lightbox modal is not yet active, open it first!
            if (lightboxModal && !lightboxModal.classList.contains('active')) {
                const mainWheelContainer = document.querySelector('.natal-chart-wheel-container');
                if (mainWheelContainer && wheelContainer) {
                    const mainSvg = mainWheelContainer.querySelector('svg');
                    if (mainSvg) {
                        wheelContainer.innerHTML = mainSvg.outerHTML;
                        const modalSvg = wheelContainer.querySelector('svg');
                        if (modalSvg) {
                            modalSvg.style.width = '100%';
                            modalSvg.style.height = '100%';
                            modalSvg.style.maxWidth = '100%';
                            modalSvg.style.maxHeight = '100%';
                        }
                    }
                }
                lightboxModal.classList.add('active');
            }

            // Toggle selection state of this rashi sign
            if (selectedSigns.has(sign)) {
                selectedSigns.delete(sign);
            } else {
                selectedSigns.add(sign);
            }

            // Find both SVGs on the page (main and lightbox)
            const mainSvg = document.querySelector('.natal-chart-wheel-container svg');
            const modalSvg = document.querySelector('#lightbox-wheel-container svg');
            updateRashiHighlightsAndAspectLines(mainSvg);
            updateRashiHighlightsAndAspectLines(modalSvg);

            // If selectedSigns has this sign, display its 30° arc magnification
            // Otherwise, if there are other selected signs, display the last one, else reset to default state
            const activeSign = selectedSigns.has(sign) ? sign : [...selectedSigns].pop();

            if (!activeSign) {
                // Reset magnifier
                magnifierDefault.style.display = 'block';
                magnifierActive.style.display = 'none';
                return;
            }

            // Use window.currentPlanetsData to populate planets inside the active sign
            const planetsInSign = [];
            const glyphMap = {
                "Sun": "☉", "Moon": "☽", "Mars": "♂", "Mercury": "☿", "Jupiter": "♃", "Venus": "♀", "Saturn": "♄", 
                "Uranus": "♅", "Neptune": "♆", "Pluto": "♇", "True North Node": "☊", "True South Node": "☋", 
                "Lilith": "⚳", "Chiron": "⚷"
            };
            const colorMap = {
                "Sun": "#ffe600", "Moon": "#ffffff", "Mars": "#ff3333", "Mercury": "#33ff57", "Jupiter": "#ffb333", 
                "Venus": "#ff33b3", "Saturn": "#e033ff", "Uranus": "#33e0ff", "Neptune": "#3357ff", "Pluto": "#999999",
                "True North Node": "#33ffaa", "True South Node": "#ff33aa", "Lilith": "#aa33ff", "Chiron": "#aaff33"
            };

            if (window.currentPlanetsData) {
                window.currentPlanetsData.forEach(p => {
                    const name = p.name || p.planet || "N/A";
                    let planetSign = "N/A";
                    if (p.rasi && p.rasi.name) {
                        planetSign = p.rasi.name;
                    } else if (p.sign) {
                        planetSign = p.sign;
                    }
                    
                    if (planetSign.toLowerCase() === activeSign.toLowerCase()) {
                        planetsInSign.push({
                            name: name,
                            symbol: glyphMap[name] || "?",
                            degree: typeof p.degree === 'number' ? p.degree : 0,
                            color: colorMap[name] || "#ffffff"
                        });
                    }
                });
            }

            // Generate degree ticks (0 to 30) for the semi-circle
            let ticksHtml = '';
            for (let d = 0; d <= 30; d++) {
                const thetaDeg = 180 + (d * 6);
                const thetaRad = thetaDeg * Math.PI / 180;
                
                let r1 = 144;
                let r2 = 156;
                let strokeW = 0.5;
                let showLabel = false;
                
                if (d % 10 === 0) {
                    r1 = 135;
                    r2 = 165;
                    strokeW = 1.2;
                    showLabel = true;
                } else if (d % 5 === 0) {
                    r1 = 138;
                    r2 = 162;
                    strokeW = 0.8;
                    showLabel = true;
                }
                
                const x1 = 200 + r1 * Math.cos(thetaRad);
                const y1 = 200 + r1 * Math.sin(thetaRad);
                const x2 = 200 + r2 * Math.cos(thetaRad);
                const y2 = 200 + r2 * Math.sin(thetaRad);
                
                ticksHtml += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="#d4af37" stroke-width="${strokeW}" opacity="0.6" />`;
                
                if (showLabel) {
                    const lx = 200 + 178 * Math.cos(thetaRad);
                    const ly = 200 + 178 * Math.sin(thetaRad) + 3.5;
                    ticksHtml += `<text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" fill="rgba(255,255,255,0.7)" font-size="9.5" font-family="Outfit" font-weight="700" text-anchor="middle">${d}°</text>`;
                }
            }

            // Render planet glyph positions on the magnifier arc
            let planetsHtml = '';
            let listHtml = '';
            
            if (planetsInSign.length === 0) {
                listHtml = `<div style="text-align: center; opacity: 0.5; font-size: 0.85rem; padding: 2rem 0; font-family: Outfit; color: #fff;">${translations[currentLang]['magnifier-empty']}${translateText(activeSign)}.</div>`;
            } else {
                planetsInSign.sort((a, b) => a.degree - b.degree);
                planetsInSign.forEach(p => {
                    const thetaDeg = 180 + (p.degree * 6);
                    const thetaRad = thetaDeg * Math.PI / 180;
                    
                    const px1 = 200 + 130 * Math.cos(thetaRad);
                    const py1 = 200 + 130 * Math.sin(thetaRad);
                    const px2 = 200 + 144 * Math.cos(thetaRad);
                    const py2 = 200 + 144 * Math.sin(thetaRad);
                    
                    planetsHtml += `<line x1="${px1.toFixed(1)}" y1="${py1.toFixed(1)}" x2="${px2.toFixed(1)}" y2="${py2.toFixed(1)}" stroke="${p.color}" stroke-width="1" stroke-dasharray="1.5,1.5" />`;
                    
                    const bx = 200 + 112 * Math.cos(thetaRad);
                    const by = 200 + 112 * Math.sin(thetaRad);
                    
                    planetsHtml += `
                        <circle cx="${bx.toFixed(1)}" cy="${by.toFixed(1)}" r="13" fill="#04020f" stroke="${p.color}" stroke-width="1.2" />
                        <text x="${bx.toFixed(1)}" y="${(by + 4.5).toFixed(1)}" fill="${p.color}" font-size="13" font-weight="bold" text-anchor="middle">${p.symbol}</text>
                    `;
                    
                    const tx = 200 + 82 * Math.cos(thetaRad);
                    const ty = 200 + 82 * Math.sin(thetaRad) + 3;
                    const degInt = Math.floor(p.degree);
                    const minInt = Math.round((p.degree % 1) * 60);
                    planetsHtml += `<text x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" fill="#ffffff" font-size="7.5" font-family="Outfit" font-weight="700" text-anchor="middle">${degInt}°${minInt.toString().padStart(2, '0')}'</text>`;
                    
                    listHtml += `
                        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); padding: 0.6rem 1rem; border-radius: 6px; border: 1px solid rgba(255,255,255,0.02);">
                            <div style="display: flex; align-items: center; gap: 0.6rem;">
                                <span style="font-size: 1.25rem; color: ${p.color}; font-weight: bold; line-height: 1;">${p.symbol}</span>
                                <span style="font-family: Outfit; font-weight: 700; color: #fff; font-size: 0.9rem;">${getDualPlanetName(p.name)}</span>
                            </div>
                            <span style="font-family: Outfit; font-weight: 600; color: #ffd700; font-size: 0.85rem;">${degInt}° ${minInt.toString().padStart(2, '0')}' ${translateText(activeSign)}</span>
                        </div>
                    `;
                });
            }

            magnifierDefault.style.display = 'none';
            magnifierActive.style.display = 'flex';
            
            const clearBtnHtml = selectedSigns.size > 1 
                ? `<button id="clear-rashi-filter-btn" style="background: none; border: 1px solid rgba(255,215,0,0.4); color: #ffd700; border-radius: 4px; padding: 0.25rem 0.6rem; font-family: Outfit; font-size: 0.75rem; font-weight: 700; cursor: pointer; transition: all 0.2s; outline: none; margin-top: 0.25rem;">Clear (${selectedSigns.size})</button>`
                : '';

            magnifierActive.innerHTML = `
                <div style="text-align: center; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 0.8rem; margin-bottom: 1rem; width: 100%; display: flex; flex-direction: column; align-items: center;">
                    <h3 style="font-family: Outfit; color: #ffd700; margin: 0; font-size: 1.4rem; font-weight: 800; letter-spacing: 0.5px;">${translateText(activeSign).toUpperCase()}</h3>
                    <span style="font-size: 0.75rem; color: var(--color-text-secondary); text-transform: uppercase; font-family: Outfit; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 0.25rem;">${translations[currentLang]['magnifier-arc']}</span>
                    ${clearBtnHtml}
                </div>
                
                <div style="width: 100%; display: flex; justify-content: center; margin-bottom: 1rem;">
                    <svg viewBox="0 0 400 230" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="max-height: 220px;">
                        <path d="M 50 200 A 150 150 0 0 1 350 200" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="12" />
                        <path d="M 50 200 A 150 150 0 0 1 350 200" fill="none" stroke="#d4af37" stroke-width="1.8" opacity="0.5" />
                        ${ticksHtml}
                        ${planetsHtml}
                        <text x="200" y="222" fill="#ffd700" font-family="Outfit" font-size="8" font-weight="700" letter-spacing="1" text-anchor="middle">${translations[currentLang]['magnifier-range']}</text>
                    </svg>
                </div>
                
                <div style="flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.5rem; max-height: 250px; padding-right: 0.25rem; width: 100%;">
                    ${listHtml}
                </div>
            `;
            
            // Add clear button listener if rendered
            const clearBtn = document.getElementById('clear-rashi-filter-btn');
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    selectedSigns.clear();
                    updateRashiHighlightsAndAspectLines(mainSvg);
                    updateRashiHighlightsAndAspectLines(modalSvg);
                    magnifierDefault.style.display = 'block';
                    magnifierActive.style.display = 'none';
                });
            }
        }
    });

    const closeLightbox = () => {
        if (lightboxModal) {
            lightboxModal.classList.remove('active');
            selectedSigns.clear();
            const mainSvg = document.querySelector('.natal-chart-wheel-container svg');
            const modalSvg = document.querySelector('#lightbox-wheel-container svg');
            updateRashiHighlightsAndAspectLines(mainSvg);
            updateRashiHighlightsAndAspectLines(modalSvg);
        }
    };

    if (closeLightboxBtn) closeLightboxBtn.addEventListener('click', closeLightbox);
    if (closeLightboxBackdrop) closeLightboxBackdrop.addEventListener('click', closeLightbox);

    // 12. Hindi Translation Dictionary & Engine
    let currentLang = 'en';

    const translations = {
        'en': {
            'menu-home': 'Dashboard Home',
            'menu-horoscope': 'Daily Horoscope',
            'menu-panchang': 'Vedic Panchang',
            'menu-positions': 'Planet Positions',
            'menu-wheel': 'Natal Chart Wheel',
            'menu-kundli': 'Kundli Generator',
            'menu-matching': 'Relationship Matcher',
            'demo-text': 'Demo Mode (Mock Data)',
            
            // Views
            'home-view-title': 'Dashboard Home',
            'home-view-subtitle': 'Welcome to your daily cosmic alignment forecast.',
            'horoscope-view-title': 'Daily Horoscope',
            'horoscope-view-subtitle': 'Receive planetary forecasts for all twelve zodiac signs.',
            'panchang-view-title': 'Vedic Panchang',
            'panchang-view-subtitle': 'Explore sunrise, lunar phases, and daily auspicious muhurtas.',
            'planet-position-view-title': 'Planet Positions',
            'planet-position-view-subtitle': 'Detailed coordinates, rasi lords, and retrograde phases for celestial bodies.',
            'natal-chart-view-title': 'Natal Chart Wheel',
            'natal-chart-view-subtitle': 'Interactive Western Astrology natal chart wheel showing aspect lines, signs, and houses.',
            'kundli-view-title': 'Kundli Generator',
            'kundli-view-subtitle': 'Calculate your birth chart elements and planetary positions.',
            'matching-view-title': 'Relationship Matcher',
            'matching-view-subtitle': 'Assess energy compatibility scores using Ashta Kuta matching.',
            
            // Magnifier
            'magnifier-title': 'Zodiac Magnifier',
            'magnifier-desc': 'Hover & click on any outer zodiac sector (e.g., Aries, Taurus) on the wheel to magnify its 30° orbital arc and view planet details.',
            'magnifier-arc': '30° ORBITAL ARC MAGNIFIER',
            'magnifier-range': 'ZODIAC RANGE (0° - 30°)',
            'magnifier-empty': 'No planets currently transiting in ',
            
            // General
            'btn-hindi': 'हिन्दी',
            'btn-english': 'English',
            'form-zodiac-system': 'Zodiac System',
            'zodiac-tropical': 'Tropical (Western / Sayana)',
            'zodiac-sidereal': 'Sidereal (Vedic / Nirayana - Lahiri)'
        },
        'hi': {
            'menu-home': 'होम',
            'menu-horoscope': 'दैनिक राशिफल',
            'menu-panchang': 'वैदिक पंचांग',
            'menu-positions': 'ग्रहों की स्थिति',
            'menu-wheel': 'कुंडली चक्र',
            'menu-kundli': 'कुण्डली निर्माता',
            'menu-matching': 'कुंडली मिलान',
            'demo-text': 'डेमो मोड (काल्पनिक डेटा)',
            
            // Views
            'home-view-title': 'मुख्य पृष्ठ',
            'home-view-subtitle': 'आपके दैनिक ब्रह्मांडीय संरेखण पूर्वानुमान में आपका स्वागत है।',
            'horoscope-view-title': 'दैनिक राशिफल',
            'horoscope-view-subtitle': 'सभी बारह राशियों के लिए ग्रहों के राशिफल प्राप्त करें।',
            'panchang-view-title': 'वैदिक पंचांग',
            'panchang-view-subtitle': 'सूर्योदय, चंद्र चरण और दैनिक शुभ मुहूर्त देखें।',
            'planet-position-view-title': 'ग्रहों की स्थिति',
            'planet-position-view-subtitle': 'खगोलीय पिंडों के लिए विस्तृत निर्देशांक, राशि स्वामी और वक्री चरण।',
            'natal-chart-view-title': 'जन्म कुंडली चक्र',
            'natal-chart-view-subtitle': 'पहलू रेखाओं, राशियों और घरों को दर्शाने वाला इंटरैक्टिव वेस्टर्न कुंडली चक्र।',
            'kundli-view-title': 'कुण्डली निर्माता',
            'kundli-view-subtitle': 'अपने जन्म विवरण के अनुसार ग्रहों की स्थिति और कुंडली का विश्लेषण करें।',
            'matching-view-title': 'कुंडली मिलान',
            'matching-view-subtitle': 'अष्टकूट मिलान का उपयोग करके ऊर्जा अनुकूलता स्कोर का आकलन करें।',
            
            // Magnifier
            'magnifier-title': 'राशिफल आवर्धक (Magnifier)',
            'magnifier-desc': 'ग्रहों के विवरण और उसके 30° कक्षीय चाप (Arc) को देखने के लिए कुंडली चक्र के बाहरी राशि क्षेत्रों (जैसे मेष, वृषभ) पर क्लिक करें।',
            'magnifier-arc': '30° कक्षीय चाप आवर्धक',
            'magnifier-range': 'राशि सीमा (0° - 30°)',
            'magnifier-empty': 'वर्तमान में कोई ग्रह इस राशि में नहीं है: ',
            
            // General
            'btn-hindi': 'हिन्दी',
            'btn-english': 'English',
            'form-zodiac-system': 'राशि चक्र प्रणाली',
            'zodiac-tropical': 'सायन (पश्चिमी / Tropical)',
            'zodiac-sidereal': 'निरयण (वैदिक / Sidereal - लाहिड़ी)'
        }
    };

    const translationMap = {
        'Sun': 'सूर्य', 'Moon': 'चंद्र', 'Mars': 'मंगल', 'Mercury': 'बुध', 'Jupiter': 'बृहस्पति (गुरु)', 'Venus': 'शुक्र', 'Saturn': 'शनि', 'Rahu': 'राहु', 'Ketu': 'केतु', 'Uranus': 'अरुण (यूरेनस)', 'Neptune': 'वरुण (नेप्च्यून)', 'Pluto': 'यम (प्लूटो)', 'Ascendant': 'लग्न',
        'Conjunction': 'युति (Conjunction)', 'Opposition': 'प्रतियुति (Opposition)', 'Trine': 'त्रिकोण (Trine)', 'Square': 'वर्ग/केंद्र (Square)', 'Sextile': 'षष्ठक (Sextile)', 'Quincunx': 'षडाष्टक (Quincunx)', 'Semi-square': 'अर्ध-वर्ग (Semi-square)', 'Semi-sextile': 'अर्ध-षष्ठक (Semi-sextile)', 'Quintile': 'पंचमेश (Quintile)', 'Sesquiquadrate': 'त्रिपाद-वर्ग (Sesquiquadrate)',
        'Aries': 'मेष', 'Taurus': 'वृषभ', 'Gemini': 'मिथुन', 'Cancer': 'कर्क', 'Leo': 'सिंह', 'Virgo': 'कन्या', 'Libra': 'तुला', 'Scorpio': 'वृश्चिक', 'Sagittarius': 'धनु', 'Capricorn': 'मकर', 'Aquarius': 'कुंभ', 'Pisces': 'मीन',
        'Name': 'नाम', 'Planet': 'ग्रह', 'Sign': 'राशि', 'Rasi': 'राशि', 'Rasi Lord': 'राशि स्वामी', 'Degree': 'अंश (Degree)', 'Nakshatra': 'नक्षत्र', 'Nakshatra Lord': 'नक्षत्र स्वामी', 'Retrograde': 'वक्री (Retro)', 'House': 'भाव (House)',
        'Calculate Positions': 'ग्रहों की स्थिति की गणना करें', 'Generate Natal Chart': 'कुंडली चक्र बनाएं', 'Generate Panchang': 'पंचांग बनाएं', 'Generate Kundli Profile': 'कुंडली प्रोफाइल बनाएं', 'Check Synergy compatibility': 'कुंडली मिलान जांचें',
        'Compatibility Score': 'अनुकूलता स्कोर', 'Daily Prediction': 'दैनिक भविष्यफल', 'Sunrise': 'सूर्ोदय', 'Sunset': 'सूर्यास्त', 'Moonrise': 'चंद्रोदय', 'Moonset': 'चंद्रस्त', 'Auspicious Period': 'शुभ काल', 'Inauspicious Period': 'अशुभ काल', 'Tithi': 'तिथि', 'Nakshatra': 'नक्षत्र', 'Yoga': 'योग', 'Karana': 'करण'
    };

    function translateText(text) {
        if (currentLang === 'en') return text;
        if (!text) return '';
        
        let translated = text;
        Object.keys(translationMap).forEach(key => {
            const regex = new RegExp('\\b' + key + '\\b', 'gi');
            translated = translated.replace(regex, translationMap[key]);
        });
        return translated;
    }

    const langToggleBtn = document.getElementById('lang-toggle-btn');
    const langBtnText = document.getElementById('lang-btn-text');

    if (langToggleBtn && langBtnText) {
        langToggleBtn.addEventListener('click', () => {
            currentLang = currentLang === 'en' ? 'hi' : 'en';
            langBtnText.textContent = currentLang === 'en' ? 'हिन्दी' : 'English';
            
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (translations[currentLang][key]) {
                    el.textContent = translations[currentLang][key];
                }
            });

            const activeView = document.querySelector('.dashboard-view.active');
            if (activeView) {
                const viewId = activeView.id;
                const viewMetaKey = viewId + '-title';
                const viewMetaSubKey = viewId + '-subtitle';
                
                const titleEl = document.getElementById('view-title');
                const subtitleEl = document.getElementById('view-subtitle');
                
                if (titleEl && translations[currentLang][viewMetaKey]) {
                    titleEl.textContent = translations[currentLang][viewMetaKey];
                }
                if (subtitleEl && translations[currentLang][viewMetaSubKey]) {
                    subtitleEl.textContent = translations[currentLang][viewMetaSubKey];
                }
            }

            document.querySelectorAll('.location-search-input').forEach(input => {
                if (currentLang === 'hi') {
                    input.placeholder = 'शहर का नाम टाइप करें (उदा. मुंबई, दिल्ली...)';
                } else {
                    input.placeholder = 'Type city (e.g. Mumbai, New York...)';
                }
            });

            const demoSpan = document.querySelector('#demo-indicator span');
            if (demoSpan) {
                demoSpan.textContent = translations[currentLang]['demo-text'];
            }
            
            const magTitle = document.querySelector('#magnifier-default-state h4');
            const magDesc = document.querySelector('#magnifier-default-state p');
            if (magTitle) magTitle.textContent = translations[currentLang]['magnifier-title'];
            if (magDesc) magDesc.textContent = translations[currentLang]['magnifier-desc'];
        });
    }

});
