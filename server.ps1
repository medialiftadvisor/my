# Local PowerShell Web Server for Astrology Web App
$port = 8081
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:${port}/")
$listener.Prefixes.Add("http://127.0.0.1:${port}/")

try {
    $listener.Start()
    Write-Host "============================================================"
    Write-Host " Astrology App Server running locally at:"
    Write-Host "   -> http://localhost:${port}/"
    Write-Host "   -> http://127.0.0.1:${port}/"
    Write-Host "============================================================"
} catch {
    Write-Host "Error starting listener on port ${port}: $_"
    exit 1
}

$root = "d:\my"

function Parse-QueryString($rawUrl) {
    $dict = @{}
    if ([string]::IsNullOrEmpty($rawUrl)) { return $dict }
    $qIdx = $rawUrl.IndexOf('?')
    if ($qIdx -lt 0) { return $dict }
    $qStr = $rawUrl.Substring($qIdx + 1)
    $pairs = $qStr.Split('&')
    foreach ($p in $pairs) {
        if (-not $p) { continue }
        $kv = $p.Split('=', 2)
        $k = [System.Uri]::UnescapeDataString($kv[0])
        $v = if ($kv.Length -eq 2) { [System.Uri]::UnescapeDataString($kv[1]) } else { "" }
        $dict[$k] = $v
    }
    return $dict
}

function Calculate-Lagna($year, $month, $day, $hourUTC, $lat, $lon, $ayanamsa = 24.22) {
    if ($month -le 2) {
        $year -= 1
        $month += 12
    }
    $A = [math]::Floor($year / 100)
    $B = 2 - $A + [math]::Floor($A / 4)
    $JD = [math]::Floor(365.25 * ($year + 4716)) + [math]::Floor(30.6001 * ($month + 1)) + $day + ($hourUTC / 24.0) + $B - 1524.5

    $T = ($JD - 2451545.0) / 36525.0
    $GMST_deg = 280.46061837 + 360.98564736629 * ($JD - 2451545.0) + 0.000387933 * $T * $T - ($T * $T * $T) / 38710000.0
    $GMST_deg = $GMST_deg % 360.0
    if ($GMST_deg -lt 0) { $GMST_deg += 360.0 }

    $RAMC = ($GMST_deg + $lon) % 360.0
    if ($RAMC -lt 0) { $RAMC += 360.0 }

    $obliquity = 23.4392911

    $ramc_rad = $RAMC * [math]::PI / 180.0
    $obliq_rad = $obliquity * [math]::PI / 180.0
    $lat_rad = $lat * [math]::PI / 180.0

    $y = [math]::Cos($ramc_rad)
    $x = -[math]::Sin($ramc_rad) * [math]::Cos($obliq_rad) - [math]::Tan($lat_rad) * [math]::Sin($obliq_rad)

    $asc_rad = [math]::Atan2($y, $x)
    $asc_deg = $asc_rad * 180.0 / [math]::PI

    $tropical_ascendant = $asc_deg % 360.0
    if ($tropical_ascendant -lt 0) { $tropical_ascendant += 360.0 }

    $vedic_ascendant = ($tropical_ascendant - $ayanamsa) % 360.0
    if ($vedic_ascendant -lt 0) { $vedic_ascendant += 360.0 }

    return [PSCustomObject]@{
        tropical = $tropical_ascendant
        vedic = $vedic_ascendant
    }
}

function Calculate-Declination($tropicalLon) {
    $obliqRad = 23.4392911 * [math]::PI / 180.0
    $lonRad = ($tropicalLon % 360.0) * [math]::PI / 180.0
    $sinDec = [math]::Sin($obliqRad) * [math]::Sin($lonRad)
    $decRad = [math]::Asin([math]::Max(-1.0, [math]::Min(1.0, $sinDec)))
    $decDeg = $decRad * 180.0 / [math]::PI

    $decSign = if ($decDeg -ge 0) { "+" } else { "-" }
    $decAbs = [math]::Abs($decDeg)
    $d = [math]::Floor($decAbs)
    $m = [math]::Floor(($decAbs - $d) * 60)
    $s = [math]::Round((($decAbs - $d) * 60 - $m) * 60)
    if ($s -eq 60) { $m += 1; $s = 0 }
    if ($m -eq 60) { $d += 1; $m = 0 }
    $decStr = "{0}{1:D2}° {2:D2}' {3:D2}""" -f $decSign, [int]$d, [int]$m, [int]$s

    return [PSCustomObject]@{
        deg = [math]::Round($decDeg, 4)
        formatted = $decStr
    }
}

function Calculate-EphemerisPlanets($year, $month, $day, $hourUTC, $ayanamsaVal = 0.0) {
    if ($month -le 2) { $year -= 1; $month += 12 }
    $A = [math]::Floor($year / 100)
    $B = 2 - $A + [math]::Floor($A / 4)
    $JD = [math]::Floor(365.25 * ($year + 4716)) + [math]::Floor(30.6001 * ($month + 1)) + $day + ($hourUTC / 24.0) + $B - 1524.5
    $T = ($JD - 2451545.0) / 36525.0

    $L_sun = (280.46646 + 36000.76983 * $T) % 360
    $M_sun = (357.52911 + 35999.05029 * $T) * [math]::PI / 180.0
    $C_sun = 1.914602 * [math]::Sin($M_sun) + 0.019993 * [math]::Sin(2*$M_sun)
    $sun_lon = ($L_sun + $C_sun) % 360; if ($sun_lon -lt 0) { $sun_lon += 360 }

    $L_moon = (218.3165 + 481267.8813 * $T) % 360
    $M_moon = (134.9634 + 477198.8675 * $T) * [math]::PI / 180.0
    $D_moon = (297.8502 + 445267.1114 * $T) * [math]::PI / 180.0
    $moon_corr = 6.2886 * [math]::Sin($M_moon) + 1.2740 * [math]::Sin(2*$D_moon - $M_moon) + 0.6583 * [math]::Sin(2*$D_moon)
    $moon_lon = ($L_moon + $moon_corr) % 360; if ($moon_lon -lt 0) { $moon_lon += 360 }

    $L_merc = (252.2509 + 149472.6741 * $T) % 360
    $M_merc = (174.7948 + 149472.5153 * $T) * [math]::PI / 180.0
    $merc_lon = ($L_merc + 23.44 * [math]::Sin($M_merc)) % 360; if ($merc_lon -lt 0) { $merc_lon += 360 }

    $L_ven = (181.9798 + 58517.8157 * $T) % 360
    $M_ven = (50.4161 + 58517.4485 * $T) * [math]::PI / 180.0
    $ven_lon = ($L_ven + 0.7758 * [math]::Sin($M_ven)) % 360; if ($ven_lon -lt 0) { $ven_lon += 360 }

    $L_mars = (355.4330 + 19140.2993 * $T) % 360
    $M_mars = (19.3730 + 19139.9770 * $T) * [math]::PI / 180.0
    $mars_lon = ($L_mars + 10.691 * [math]::Sin($M_mars)) % 360; if ($mars_lon -lt 0) { $mars_lon += 360 }

    $L_jup = (34.3515 + 3034.9057 * $T) % 360
    $M_jup = (20.0202 + 3034.6920 * $T) * [math]::PI / 180.0
    $jup_lon = ($L_jup + 5.555 * [math]::Sin($M_jup)) % 360; if ($jup_lon -lt 0) { $jup_lon += 360 }

    $L_sat = (50.0774 + 1222.1138 * $T) % 360
    $M_sat = (317.0207 + 1221.5515 * $T) * [math]::PI / 180.0
    $sat_lon = ($L_sat + 6.358 * [math]::Sin($M_sat)) % 360; if ($sat_lon -lt 0) { $sat_lon += 360 }

    $uran_lon = (314.0550 + 428.4660 * $T) % 360; if ($uran_lon -lt 0) { $uran_lon += 360 }
    $nep_lon = (304.3487 + 218.4862 * $T) % 360; if ($nep_lon -lt 0) { $nep_lon += 360 }
    $plut_lon = (238.96 + 145.18 * $T) % 360; if ($plut_lon -lt 0) { $plut_lon += 360 }
    $rahu_lon = (125.0445 - 1934.1363 * $T) % 360; if ($rahu_lon -lt 0) { $rahu_lon += 360 }
    $ketu_lon = ($rahu_lon + 180.0) % 360; if ($ketu_lon -lt 0) { $ketu_lon += 360 }

    if ($ayanamsaVal -gt 0) {
        $sun_lon = ($sun_lon - $ayanamsaVal) % 360; if ($sun_lon -lt 0) { $sun_lon += 360 }
        $moon_lon = ($moon_lon - $ayanamsaVal) % 360; if ($moon_lon -lt 0) { $moon_lon += 360 }
        $merc_lon = ($merc_lon - $ayanamsaVal) % 360; if ($merc_lon -lt 0) { $merc_lon += 360 }
        $ven_lon = ($ven_lon - $ayanamsaVal) % 360; if ($ven_lon -lt 0) { $ven_lon += 360 }
        $mars_lon = ($mars_lon - $ayanamsaVal) % 360; if ($mars_lon -lt 0) { $mars_lon += 360 }
        $jup_lon = ($jup_lon - $ayanamsaVal) % 360; if ($jup_lon -lt 0) { $jup_lon += 360 }
        $sat_lon = ($sat_lon - $ayanamsaVal) % 360; if ($sat_lon -lt 0) { $sat_lon += 360 }
        $uran_lon = ($uran_lon - $ayanamsaVal) % 360; if ($uran_lon -lt 0) { $uran_lon += 360 }
        $nep_lon = ($nep_lon - $ayanamsaVal) % 360; if ($nep_lon -lt 0) { $nep_lon += 360 }
        $plut_lon = ($plut_lon - $ayanamsaVal) % 360; if ($plut_lon -lt 0) { $plut_lon += 360 }
        $rahu_lon = ($rahu_lon - $ayanamsaVal) % 360; if ($rahu_lon -lt 0) { $rahu_lon += 360 }
        $ketu_lon = ($ketu_lon - $ayanamsaVal) % 360; if ($ketu_lon -lt 0) { $ketu_lon += 360 }
    }

    return [PSCustomObject]@{
        Sun = $sun_lon; Moon = $moon_lon; Mercury = $merc_lon; Venus = $ven_lon
        Mars = $mars_lon; Jupiter = $jup_lon; Saturn = $sat_lon; Uranus = $uran_lon
        Neptune = $nep_lon; Pluto = $plut_lon; Rahu = $rahu_lon; Ketu = $ketu_lon
    }
}

while ($listener.IsListening) {
    try {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        # Add CORS headers
        $response.Headers.Add("Access-Control-Allow-Origin", "*")
        $response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        $response.Headers.Add("Access-Control-Allow-Headers", "*")

        if ($request.HttpMethod -eq "OPTIONS") {
            $response.StatusCode = 200
            $response.Close()
            continue
        }

        $urlPath = $request.Url.AbsolutePath

        if ($urlPath -eq "/api/config") {
            $json = '{"status":"success","demo_mode":true,"provider":"astronomyapi"}'
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
            $response.Close()
            continue
        }

        if ($urlPath.StartsWith("/api/astrology/lagna-history")) {
            $query = Parse-QueryString $request.Url.PathAndQuery
            $dtStr = $query["datetime"]
            $fromDtStr = $query["from_datetime"]
            $toDtStr = $query["to_datetime"]
            $latStr = $query["latitude"]
            $lngStr = $query["longitude"]
            $ayanamsaStr = $query["ayanamsa"]
            $limitStr = $query["limit"]
            $offsetStr = $query["offset"]
            $intervalStr = $query["interval"]
            $exportStr = $query["export"]

            $lat = if ($latStr) { [double]$latStr } else { 19.0655 }
            $lng = if ($lngStr) { [double]$lngStr } else { 72.8644 }
            $ayanamsaVal = if ($ayanamsaStr -eq "1") { 24.22 } else { 0.0 }
            $intervalMin = if ($intervalStr) { [int]$intervalStr } else { 60 }
            if ($intervalMin -le 0) { $intervalMin = 60 }
            
            $isExport = ($exportStr -eq "1")
            $limit = if ($limitStr) { [int]$limitStr } else { if ($isExport) { 25000 } else { 100 } }
            $offset = if ($offsetStr) { [int]$offsetStr } else { 0 }

            $targetDtStr = if ($toDtStr) { $toDtStr } else { $dtStr }
            $baseDt = [DateTimeOffset]::Now
            if ($targetDtStr) {
                try { $baseDt = [DateTimeOffset]::Parse($targetDtStr) } catch {}
            }

            $maxSteps = [int](1051920 / $intervalMin)
            if ($fromDtStr) {
                try {
                    $startDt = [DateTimeOffset]::Parse($fromDtStr)
                    $spanMin = [int](($baseDt - $startDt).TotalMinutes)
                    if ($spanMin -gt 0) {
                        $maxSteps = [int]($spanMin / $intervalMin) + 1
                    }
                } catch {}
            }

            $history = @()
            $signs = @("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")

            for ($i = 0; $i -lt $limit; $i++) {
                $stepIdx = $offset + $i
                if ($stepIdx -ge $maxSteps) { break }
                $stepDt = $baseDt.AddMinutes(-$intervalMin * $stepIdx)
                $utcObj = $stepDt.ToUniversalTime()
                $year = $utcObj.Year; $month = $utcObj.Month; $day = $utcObj.Day
                $hourUTC = $utcObj.Hour + ($utcObj.Minute / 60.0) + ($utcObj.Second / 3600.0)

                $ascObj = Calculate-Lagna $year $month $day $hourUTC $lat $lng $ayanamsaVal
                $ascLon = $ascObj.vedic
                $ascSignIdx = [math]::Floor($ascLon / 30) % 12
                $ascDeg = $ascLon % 30

                $degD = [int][math]::Floor($ascDeg)
                $degM = [int][math]::Floor(($ascDeg - $degD) * 60)
                $degS = [int][math]::Round((($ascDeg - $degD) * 60 - $degM) * 60)
                if ($degS -eq 60) { $degM += 1; $degS = 0 }
                if ($degM -eq 60) { $degD += 1; $degM = 0 }
                $degFormatted = "{0:D2}° {1:D2}' {2:D2}""" -f $degD, $degM, $degS

                # RA, Dec, ALT, AZ calculation
                $A = [math]::Floor($year / 100)
                $B = 2 - $A + [math]::Floor($A / 4)
                $JD = [math]::Floor(365.25 * ($year + 4716)) + [math]::Floor(30.6001 * ($month + 1)) + $day + ($hourUTC / 24.0) + $B - 1524.5
                $T = ($JD - 2451545.0) / 36525.0
                $GMST_deg = (280.46061837 + 360.98564736629 * ($JD - 2451545.0)) % 360.0; if ($GMST_deg -lt 0) { $GMST_deg += 360.0 }
                $RAMC = ($GMST_deg + $lng) % 360.0; if ($RAMC -lt 0) { $RAMC += 360.0 }

                $raDeg = ($RAMC + 90.0) % 360.0
                $raH = [math]::Floor($raDeg / 15.0)
                $raM = [math]::Floor(($raDeg / 15.0 - $raH) * 60)
                $raStr = "{0:D2}h {1:D2}m ({2:F2}°)" -f [int]$raH, [int]$raM, $raDeg

                $sinDec = [math]::Sin(23.4392911 * [math]::PI / 180.0) * [math]::Sin($ascObj.tropical * [math]::PI / 180.0)
                $decDeg = [math]::Asin([math]::Max(-1.0, [math]::Min(1.0, $sinDec))) * 180.0 / [math]::PI
                $decSign = if ($decDeg -ge 0) { "+" } else { "-" }
                $decD = [math]::Floor([math]::Abs($decDeg))
                $decM = [math]::Floor(([math]::Abs($decDeg) - $decD) * 60)
                $decStr = "{0}{1:D2}° {2:D2}'" -f $decSign, [int]$decD, [int]$decM

                $history += [PSCustomObject]@{
                    datetime = $stepDt.ToString("yyyy-MM-dd HH:mm")
                    sign = $signs[$ascSignIdx]
                    degree = [math]::Round($ascDeg, 4)
                    degree_formatted = $degFormatted
                    longitude = [math]::Round($ascLon, 4)
                    right_ascension = $raStr
                    ra_deg = [math]::Round($raDeg, 4)
                    declination = $decStr
                    altitude = '00° 00'' 00"'
                    azimuth = '085° 30'''
                    nakshatra = "Punarvasu (Pada 3)"
                    nakshatra_name = "Punarvasu"
                    pada = 3
                    nakshatra_lord = "Jupiter"
                    sub_lord = "Mercury"
                    ayanamsa_value = $ayanamsaVal
                }
            }

            $resObj = [PSCustomObject]@{
                status = "success"
                data = [PSCustomObject]@{
                    history = $history
                    has_more = ($offset + $limit) -lt $maxSteps
                    total_returned = $history.Count
                    interval_min = $intervalMin
                    max_steps = $maxSteps
                    base_datetime = $baseDt.ToString("yyyy-MM-dd HH:mm")
                    latitude = $lat
                    longitude = $lng
                    ayanamsa = if ($ayanamsaVal -gt 0) { "Sidereal Lahiri" } else { "Tropical" }
                }
            }

            $json = $resObj | ConvertTo-Json -Depth 5
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
            $response.Close()
            continue
        }

        if ($urlPath.StartsWith("/api/astrology/transit-history")) {
            $query = Parse-QueryString $request.Url.PathAndQuery
            $dtStr = $query["datetime"]
            $latStr = $query["latitude"]
            $lngStr = $query["longitude"]
            $ayanamsaStr = $query["ayanamsa"]
            $limitStr = $query["limit"]
            $offsetStr = $query["offset"]
            $intervalStr = $query["interval"]

            $lat = if ($latStr) { [double]$latStr } else { 19.0655 }
            $lng = if ($lngStr) { [double]$lngStr } else { 72.8644 }
            $ayanamsaVal = if ($ayanamsaStr -eq "1") { 24.22 } else { 0.0 }
            $limit = if ($limitStr) { [int]$limitStr } else { 50 }
            $offset = if ($offsetStr) { [int]$offsetStr } else { 0 }
            $intervalMin = if ($intervalStr) { [int]$intervalStr } else { 60 } # Default 1 hr

            $baseDt = [DateTimeOffset]::Now
            if ($dtStr) {
                try { $baseDt = [DateTimeOffset]::Parse($dtStr) } catch {}
            }

            # 2 months = 1440 1-hour steps
            $maxSteps = [math]::Floor(1440 * 60 / $intervalMin)
            $history = @()

            $signs = @("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")

            for ($i = 0; $i -lt $limit; $i++) {
                $stepIdx = $offset + $i
                if ($stepIdx -ge $maxSteps) { break }
                $stepDt = $baseDt.AddMinutes(-$intervalMin * $stepIdx)
                $utcObj = $stepDt.ToUniversalTime()
                $year = $utcObj.Year; $month = $utcObj.Month; $day = $utcObj.Day
                $hourUTC = $utcObj.Hour + ($utcObj.Minute / 60.0) + ($utcObj.Second / 3600.0)

                $ascObj = Calculate-Lagna $year $month $day $hourUTC $lat $lng $ayanamsaVal
                $ascLon = $ascObj.vedic
                $ascSignIdx = [math]::Floor($ascLon / 30) % 12
                $ascDeg = $ascLon % 30

                $eph = Calculate-EphemerisPlanets $year $month $day $hourUTC $ayanamsaVal

                $makePlanet = { param($lon) [PSCustomObject]@{ sign = $signs[[math]::Floor($lon / 30) % 12]; degree = [math]::Round($lon % 30, 2); longitude = [math]::Round($lon, 2) } }

                $stepPlanets = [PSCustomObject]@{
                    "Ascendant" = [PSCustomObject]@{ sign = $signs[$ascSignIdx]; degree = [math]::Round($ascDeg, 2); longitude = [math]::Round($ascLon, 2) }
                    "Sun" = & $makePlanet $eph.Sun
                    "Moon" = & $makePlanet $eph.Moon
                    "Mars" = & $makePlanet $eph.Mars
                    "Mercury" = & $makePlanet $eph.Mercury
                    "Jupiter" = & $makePlanet $eph.Jupiter
                    "Venus" = & $makePlanet $eph.Venus
                    "Saturn" = & $makePlanet $eph.Saturn
                    "Uranus" = & $makePlanet $eph.Uranus
                    "Neptune" = & $makePlanet $eph.Neptune
                    "Pluto" = & $makePlanet $eph.Pluto
                    "Rahu" = & $makePlanet $eph.Rahu
                    "Ketu" = & $makePlanet $eph.Ketu
                    "Spashth Rahu" = & $makePlanet (($eph.Rahu + 0.9) % 360)
                    "Spashth Ketu" = & $makePlanet (($eph.Ketu + 0.9) % 360)
                    "Earth" = & $makePlanet (($eph.Sun + 180) % 360)
                }

                $history += [PSCustomObject]@{
                    datetime = $stepDt.ToString("yyyy-MM-dd HH:mm")
                    planets = $stepPlanets
                }
            }

            $resObj = [PSCustomObject]@{
                status = "success"
                data = [PSCustomObject]@{
                    history = $history
                    has_more = ($offset + $limit) -lt $maxSteps
                    interval_min = $intervalMin
                    max_steps = $maxSteps
                }
            }

            $json = $resObj | ConvertTo-Json -Depth 5
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
            $response.Close()
            continue
        }

        if ($urlPath.StartsWith("/api/astrology/planet-position")) {
            $query = Parse-QueryString $request.Url.PathAndQuery
            $dtStr = $query["datetime"]
            $latStr = $query["latitude"]
            $lngStr = $query["longitude"]
            $ayanamsaStr = $query["ayanamsa"]

            $lat = if ($latStr) { [double]$latStr } else { 19.0655 }
            $lng = if ($lngStr) { [double]$lngStr } else { 72.8644 }
            $ayanamsaVal = if ($ayanamsaStr -eq "1") { 24.22 } else { 0.0 }

            $year = 2020; $month = 5; $day = 12; $hourUTC = 3.833333
            if ($dtStr) {
                try {
                    $dtObj = [DateTimeOffset]::Parse($dtStr)
                    $utcObj = $dtObj.ToUniversalTime()
                    $year = $utcObj.Year
                    $month = $utcObj.Month
                    $day = $utcObj.Day
                    $hourUTC = $utcObj.Hour + ($utcObj.Minute / 60.0) + ($utcObj.Second / 3600.0)
                } catch {}
            }

            $ascObj = Calculate-Lagna $year $month $day $hourUTC $lat $lng $ayanamsaVal
            $ascLon = $ascObj.vedic

            $signs = @("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
            $lords = @("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
            $vedicLords = @("Mangala", "Shukra", "Budha", "Chandra", "Surya", "Budha", "Shukra", "Mangala", "Guru", "Shani", "Shani", "Guru")

            $ascSignIdx = [math]::Floor($ascLon / 30) % 12
            $ascDeg = $ascLon % 30

            $planets = @(
                [PSCustomObject]@{
                    name = "Ascendant"
                    planet = "Ascendant"
                    longitude = [math]::Round($ascLon, 2)
                    degree = [math]::Round($ascDeg, 2)
                    is_retrograde = $false
                    rasi = [PSCustomObject]@{
                        name = $signs[$ascSignIdx]
                        lord = [PSCustomObject]@{
                            name = $lords[$ascSignIdx]
                            vedic_name = $vedicLords[$ascSignIdx]
                        }
                    }
                    nakshatra = "Punarvasu"
                    padam = 3
                    nakshatra_lord = "Jupiter"
                    sub_lord = "Mercury"
                },
                [PSCustomObject]@{
                    name = "Sun"
                    planet = "Sun"
                    longitude = 59.2
                    degree = 29.1
                    is_retrograde = $false
                    rasi = [PSCustomObject]@{ name = "Taurus"; lord = [PSCustomObject]@{ name = "Venus"; vedic_name = "Shukra" } }
                    nakshatra = "Mrigashira"
                    padam = 2
                    nakshatra_lord = "Mars"
                    sub_lord = "Saturn"
                },
                [PSCustomObject]@{
                    name = "Moon"
                    planet = "Moon"
                    longitude = 38.5
                    degree = 8.5
                    is_retrograde = $false
                    rasi = [PSCustomObject]@{ name = "Taurus"; lord = [PSCustomObject]@{ name = "Venus"; vedic_name = "Shukra" } }
                    nakshatra = "Krittika"
                    padam = 4
                    nakshatra_lord = "Sun"
                    sub_lord = "Venus"
                },
                [PSCustomObject]@{
                    name = "Mars"
                    planet = "Mars"
                    longitude = 345.3
                    degree = 15.3
                    is_retrograde = $false
                    rasi = [PSCustomObject]@{ name = "Pisces"; lord = [PSCustomObject]@{ name = "Jupiter"; vedic_name = "Guru" } }
                    nakshatra = "Uttara Bhadrapada"
                    padam = 4
                    nakshatra_lord = "Saturn"
                    sub_lord = "Jupiter"
                },
                [PSCustomObject]@{
                    name = "Mercury"
                    planet = "Mercury"
                    longitude = 64.1
                    degree = 4.1
                    is_retrograde = $true
                    rasi = [PSCustomObject]@{ name = "Gemini"; lord = [PSCustomObject]@{ name = "Mercury"; vedic_name = "Budha" } }
                    nakshatra = "Ardra"
                    padam = 1
                    nakshatra_lord = "Rahu"
                    sub_lord = "Moon"
                },
                [PSCustomObject]@{
                    name = "Jupiter"
                    planet = "Jupiter"
                    longitude = 322.8
                    degree = 22.8
                    is_retrograde = $false
                    rasi = [PSCustomObject]@{ name = "Aquarius"; lord = [PSCustomObject]@{ name = "Saturn"; vedic_name = "Shani" } }
                    nakshatra = "Purva Bhadrapada"
                    padam = 1
                    nakshatra_lord = "Jupiter"
                    sub_lord = "Saturn"
                },
                [PSCustomObject]@{
                    name = "Venus"
                    planet = "Venus"
                    longitude = 11.2
                    degree = 11.2
                    is_retrograde = $false
                    rasi = [PSCustomObject]@{ name = "Aries"; lord = [PSCustomObject]@{ name = "Mars"; vedic_name = "Mangala" } }
                    nakshatra = "Ashwini"
                    padam = 4
                    nakshatra_lord = "Ketu"
                    sub_lord = "Saturn"
                },
                [PSCustomObject]@{
                    name = "Saturn"
                    planet = "Saturn"
                    longitude = 276.4
                    degree = 6.4
                    is_retrograde = $false
                    rasi = [PSCustomObject]@{ name = "Capricorn"; lord = [PSCustomObject]@{ name = "Saturn"; vedic_name = "Shani" } }
                    nakshatra = "Uttarashadha"
                    padam = 3
                    nakshatra_lord = "Sun"
                    sub_lord = "Mercury"
                }
            )

            foreach ($p in $planets) {
                $tropLon = ($p.longitude + $ayanamsaVal) % 360.0
                $decObj = Calculate-Declination $tropLon
                $p | Add-Member -MemberType NoteProperty -Name "declination" -Value $decObj.formatted -Force
                $p | Add-Member -MemberType NoteProperty -Name "declination_deg" -Value $decObj.deg -Force
            }

            $resObj = [PSCustomObject]@{
                status = "success"
                data = [PSCustomObject]@{
                    planet_position = $planets
                    planetary_positions = $planets
                }
            }

            $json = $resObj | ConvertTo-Json -Depth 5
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
            $response.Close()
            continue
        }

        # Default static file handler
        $filePath = Join-Path $root ($urlPath.TrimStart('/') -replace '/', '\')
        if ($urlPath -eq "/" -or $urlPath -eq "") {
            $filePath = Join-Path $root "index.html"
        }

        if (Test-Path $filePath -PathType Leaf) {
            $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
            $mime = switch ($ext) {
                ".html" { "text/html; charset=utf-8" }
                ".css"  { "text/css; charset=utf-8" }
                ".js"   { "application/javascript; charset=utf-8" }
                ".json" { "application/json; charset=utf-8" }
                ".yaml" { "text/yaml; charset=utf-8" }
                ".svg"  { "image/svg+xml" }
                default { "application/octet-stream" }
            }
            $bytes = [System.IO.File]::ReadAllBytes($filePath)
            $response.ContentType = $mime
            $response.ContentLength64 = $bytes.Length
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
        } else {
            $response.StatusCode = 404
            $buffer = [System.Text.Encoding]::UTF8.GetBytes("404 Not Found")
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
        }
        $response.Close()
    } catch {
        Write-Host "Request handling error: $_"
        if ($response -and -not $response.IsClosed) {
            $response.StatusCode = 500
            $errJson = '{"status":"error","message":"Internal Server Error"}'
            $errBuf = [System.Text.Encoding]::UTF8.GetBytes($errJson)
            $response.ContentType = "application/json"
            $response.OutputStream.Write($errBuf, 0, $errBuf.Length)
            $response.Close()
        }
    }
}
