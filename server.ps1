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

    $targetLon = if ($ayanamsa -gt 0) { $vedic_ascendant } else { $tropical_ascendant }
    $nakDetails = Get-NakshatraDetails $targetLon
    $decDetails = Calculate-Declination $tropical_ascendant

    $signs = @("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
    $signIdx = [math]::Floor($targetLon / 30) % 12
    $degVal = $targetLon % 30
    $degD = [int][math]::Floor($degVal)
    $degM = [int][math]::Floor(($degVal - $degD) * 60)
    $degS = [int][math]::Round((($degVal - $degD) * 60 - $degM) * 60)
    if ($degS -eq 60) { $degM += 1; $degS = 0 }
    if ($degM -eq 60) { $degD += 1; $degM = 0 }
    $degFormatted = "{0:D2}° {1:D2}' {2:D2}""" -f $degD, $degM, $degS

    $raDeg = ($RAMC + 90.0) % 360.0
    $raH = [math]::Floor($raDeg / 15.0)
    $raM = [math]::Floor(($raDeg / 15.0 - $raH) * 60)
    $raStr = "{0:D2}h {1:D2}m ({2:F2}°)" -f [int]$raH, [int]$raM, $raDeg

    return [PSCustomObject]@{
        tropical = $tropical_ascendant
        vedic = $vedic_ascendant
        sign = $signs[$signIdx]
        degree = [math]::Round($degVal, 4)
        degree_formatted = $degFormatted
        longitude = [math]::Round($targetLon, 4)
        ramcDeg = $raDeg
        raDms = $raStr
        decDeg = $decDetails.deg
        decMag = $decDetails.mag
        decDms = $decDetails.formatted
        decDmsMag = $decDetails.formatted_mag
        altDms = "00° 00' 00`""
        azDms = "090° 00' 00`""
        nakshatra = $nakDetails.name
        nakshatra_full = "$($nakDetails.name) (Pada $($nakDetails.pada))"
        pada = $nakDetails.pada
        nakshatra_lord = $nakDetails.lord
        sub_lord = $nakDetails.sub_lord
    }
}

function Calculate-Declination($tropicalLon) {
    $obliqRad = 23.4392911 * [math]::PI / 180.0
    $lonRad = ($tropicalLon % 360.0) * [math]::PI / 180.0
    $sinDec = [math]::Sin($obliqRad) * [math]::Sin($lonRad)
    $decRad = [math]::Asin([math]::Max(-1.0, [math]::Min(1.0, $sinDec)))
    $decDeg = $decRad * 180.0 / [math]::PI

    $decAbs = [math]::Abs($decDeg)
    $d = [math]::Floor($decAbs)
    $m = [math]::Floor(($decAbs - $d) * 60)
    $s = [math]::Round((($decAbs - $d) * 60 - $m) * 60)
    if ($s -eq 60) { $m += 1; $s = 0 }
    if ($m -eq 60) { $d += 1; $m = 0 }
    $decSign = if ($decDeg -ge 0) { "+" } else { "-" }
    $decStr = "{0}{1:D2}° {2:D2}' {3:D2}""" -f $decSign, [int]$d, [int]$m, [int]$s
    $decMagStr = "{0:D2}° {1:D2}' {2:D2}""" -f [int]$d, [int]$m, [int]$s

    return [PSCustomObject]@{
        deg = [math]::Round($decDeg, 4)
        mag = [math]::Round($decAbs, 4)
        formatted = $decStr
        formatted_mag = $decMagStr
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

$global:nakshatrasList = @("Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati")
$global:nakLordsList = @("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
$global:vimshottariYears = @{ "Ketu" = 7; "Venus" = 20; "Sun" = 6; "Moon" = 10; "Mars" = 7; "Rahu" = 18; "Jupiter" = 16; "Saturn" = 19; "Mercury" = 17 }

function Get-NakshatraDetails($lonDeg) {
    $normLon = ($lonDeg % 360.0 + 360.0) % 360.0
    $nakSpan = 360.0 / 27.0
    $nakIdx = [math]::Floor($normLon / $nakSpan) % 27
    $nakName = $global:nakshatrasList[$nakIdx]
    $nakLord = $global:nakLordsList[$nakIdx]

    $padaSpan = $nakSpan / 4.0
    $pada = [math]::Floor(($normLon % $nakSpan) / $padaSpan) + 1

    $remInNak = $normLon % $nakSpan
    $startIdx = $nakIdx % 9
    $order = @()
    for ($i = 0; $i -lt 9; $i++) { $order += $global:nakLordsList[($startIdx + $i) % 9] }

    $currPos = 0.0
    $subLord = $order[0]
    foreach ($l in $order) {
        $spanL = $nakSpan * ($global:vimshottariYears[$l] / 120.0)
        if ($remInNak -ge $currPos -and $remInNak -lt ($currPos + $spanL + 0.000001)) {
            $subLord = $l
            break
        }
        $currPos += $spanL
    }

    return [PSCustomObject]@{
        name = $nakName
        pada = $pada
        lord = $nakLord
        sub_lord = $subLord
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

                $history += [PSCustomObject]@{
                    datetime = $stepDt.ToString("yyyy-MM-dd HH:mm")
                    sign = $ascObj.sign
                    degree = $ascObj.degree
                    degree_formatted = $ascObj.degree_formatted
                    longitude = $ascObj.longitude
                    right_ascension = $ascObj.raDms
                    ra_deg = $ascObj.ramcDeg
                    declination = $ascObj.decDms
                    declination_deg = $ascObj.decDeg
                    declination_mag = $ascObj.decMag
                    altitude = $ascObj.altDms
                    azimuth = $ascObj.azDms
                    nakshatra = $ascObj.nakshatra_full
                    nakshatra_name = $ascObj.nakshatra
                    pada = $ascObj.pada
                    nakshatra_lord = $ascObj.nakshatra_lord
                    sub_lord = $ascObj.sub_lord
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

            $utf8NoBOM = New-Object System.Text.UTF8Encoding($false)
            $json = $resObj | ConvertTo-Json -Depth 5
            $buffer = $utf8NoBOM.GetBytes($json)
            $response.ContentType = "application/json; charset=utf-8"
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

            $utf8NoBOM = New-Object System.Text.UTF8Encoding($false)
            $json = $resObj | ConvertTo-Json -Depth 5
            $buffer = $utf8NoBOM.GetBytes($json)
            $response.ContentType = "application/json; charset=utf-8"
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

            $eph = Calculate-EphemerisPlanets $year $month $day $hourUTC $ayanamsaVal

            $makePlanetObj = {
                param($name, $lon, $isRetro)
                $pLon = [math]::Round($lon, 4)
                $pSignIdx = [math]::Floor($pLon / 30) % 12
                $pDeg = [math]::Round($pLon % 30, 4)
                $pNak = Get-NakshatraDetails $pLon
                $tropLon = ($pLon + $ayanamsaVal) % 360.0
                $decObj = Calculate-Declination $tropLon

                return [PSCustomObject]@{
                    name = $name
                    planet = $name
                    longitude = [math]::Round($pLon, 2)
                    degree = [math]::Round($pDeg, 2)
                    is_retrograde = $isRetro
                    rasi = [PSCustomObject]@{
                        name = $signs[$pSignIdx]
                        lord = [PSCustomObject]@{
                            name = $lords[$pSignIdx]
                            vedic_name = $vedicLords[$pSignIdx]
                        }
                    }
                    nakshatra = $pNak.name
                    padam = $pNak.pada
                    nakshatra_lord = $pNak.lord
                    sub_lord = $pNak.sub_lord
                    right_ascension = ""
                    ra_deg = [math]::Round($tropLon, 4)
                    declination = $decObj.formatted
                    declination_deg = $decObj.deg
                    declination_mag = $decObj.mag
                    altitude = "00° 00' 00`""
                    azimuth = "90° 00' 00`""
                }
            }

            $planets = @(
                [PSCustomObject]@{
                    name = "Ascendant"
                    planet = "Ascendant"
                    longitude = [math]::Round($ascObj.longitude, 2)
                    degree = [math]::Round($ascObj.degree, 2)
                    is_retrograde = $false
                    rasi = [PSCustomObject]@{
                        name = $ascObj.sign
                        lord = [PSCustomObject]@{
                            name = $lords[$ascSignIdx]
                            vedic_name = $vedicLords[$ascSignIdx]
                        }
                    }
                    nakshatra = $ascObj.nakshatra
                    padam = $ascObj.pada
                    nakshatra_lord = $ascObj.nakshatra_lord
                    sub_lord = $ascObj.sub_lord
                    right_ascension = $ascObj.raDms
                    ra_deg = [math]::Round($ascObj.ramcDeg, 4)
                    declination = $ascObj.decDms
                    declination_deg = [math]::Round($ascObj.decDeg, 4)
                    declination_mag = [math]::Round($ascObj.decMag, 4)
                    altitude = $ascObj.altDms
                    azimuth = $ascObj.azDms
                },
                (& $makePlanetObj "Sun" $eph.Sun $false),
                (& $makePlanetObj "Moon" $eph.Moon $false),
                (& $makePlanetObj "Mars" $eph.Mars $false),
                (& $makePlanetObj "Mercury" $eph.Mercury $false),
                (& $makePlanetObj "Jupiter" $eph.Jupiter $false),
                (& $makePlanetObj "Venus" $eph.Venus $false),
                (& $makePlanetObj "Saturn" $eph.Saturn $false),
                (& $makePlanetObj "Uranus" $eph.Uranus $false),
                (& $makePlanetObj "Neptune" $eph.Neptune $false),
                (& $makePlanetObj "Pluto" $eph.Pluto $false),
                (& $makePlanetObj "Rahu" $eph.Rahu $true),
                (& $makePlanetObj "Ketu" $eph.Ketu $true),
                (& $makePlanetObj "Spashth Rahu" (($eph.Rahu + 0.9) % 360) $true),
                (& $makePlanetObj "Spashth Ketu" (($eph.Ketu + 0.9) % 360) $true),
                (& $makePlanetObj "Earth" (($eph.Sun + 180.0) % 360) $false)
            )

            $resObj = [PSCustomObject]@{
                status = "success"
                data = [PSCustomObject]@{
                    planet_position = $planets
                    planetary_positions = $planets
                }
            }

            $utf8NoBOM = New-Object System.Text.UTF8Encoding($false)
            $json = $resObj | ConvertTo-Json -Depth 5
            $buffer = $utf8NoBOM.GetBytes($json)
            $response.ContentType = "application/json; charset=utf-8"
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
            $response.Close()
            continue
        }

        if ($urlPath.StartsWith("/api/astrology/lagna-2yr-matches") -or $urlPath.StartsWith("/api/astrology/lagna-4yr-matches")) {
            $query = Parse-QueryString $request.Url.PathAndQuery
            $dtStr = $query["datetime"]
            $latStr = $query["latitude"]
            $lngStr = $query["longitude"]
            $ayanamsaStr = $query["ayanamsa"]

            $lat = if ($latStr) { [double]$latStr } else { 19.0655 }
            $lng = if ($lngStr) { [double]$lngStr } else { 72.8644 }
            $ayanamsaVal = if ($ayanamsaStr -eq "1") { 24.22 } else { 0.0 }

            $baseDt = [DateTimeOffset]::Now
            if ($dtStr) {
                try { $baseDt = [DateTimeOffset]::Parse($dtStr) } catch {}
            }

            # Generate current planets
            $utcObj = $baseDt.ToUniversalTime()
            $ascObj = Calculate-Lagna $utcObj.Year $utcObj.Month $utcObj.Day ($utcObj.Hour + $utcObj.Minute / 60.0 + $utcObj.Second / 3600.0) $lat $lng $ayanamsaVal
            $eph = Calculate-EphemerisPlanets $utcObj.Year $utcObj.Month $utcObj.Day ($utcObj.Hour + $utcObj.Minute / 60.0 + $utcObj.Second / 3600.0) $ayanamsaVal

            $targetPlanets = @(
                [PSCustomObject]@{ name = "Ascendant"; longitude = $ascObj.vedic }
                [PSCustomObject]@{ name = "Sun"; longitude = $eph.Sun }
                [PSCustomObject]@{ name = "Moon"; longitude = $eph.Moon }
                [PSCustomObject]@{ name = "Mars"; longitude = $eph.Mars }
                [PSCustomObject]@{ name = "Mercury"; longitude = $eph.Mercury }
                [PSCustomObject]@{ name = "Jupiter"; longitude = $eph.Jupiter }
                [PSCustomObject]@{ name = "Venus"; longitude = $eph.Venus }
                [PSCustomObject]@{ name = "Saturn"; longitude = $eph.Saturn }
                [PSCustomObject]@{ name = "Uranus"; longitude = $eph.Uranus }
                [PSCustomObject]@{ name = "Neptune"; longitude = $eph.Neptune }
                [PSCustomObject]@{ name = "Pluto"; longitude = $eph.Pluto }
                [PSCustomObject]@{ name = "Rahu"; longitude = $eph.Rahu }
                [PSCustomObject]@{ name = "Ketu"; longitude = $eph.Ketu }
                [PSCustomObject]@{ name = "Spashth Rahu"; longitude = (($eph.Rahu + 0.9) % 360) }
                [PSCustomObject]@{ name = "Spashth Ketu"; longitude = (($eph.Ketu + 0.9) % 360) }
                [PSCustomObject]@{ name = "Earth"; longitude = (($eph.Sun + 180) % 360) }
            )

            $signs = @("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
            $matches = @()

            foreach ($p in $targetPlanets) {
                $pName = $p.name
                $targetLon = ($p.longitude % 360.0 + 360.0) % 360.0
                $tNak = Get-NakshatraDetails $targetLon
                $tSign = $signs[[math]::Floor($targetLon / 30) % 12]
                $tDeg = $targetLon % 30.0
                $tDegD = [int][math]::Floor($tDeg)
                $tDegM = [int][math]::Floor(($tDeg - $tDegD) * 60)
                $tDegFormatted = "{0:D2}° {1:D2}'" -f $tDegD, $tDegM

                $pMatches = @()
                $yearsBack = @(1.0, 2.0, 0.5, 1.5)
                foreach ($yr in $yearsBack) {
                    if ($pMatches.Count -ge 3) { break }
                    $candDay = $baseDt.AddDays(-[int]($yr * 365.25))

                    # Quick 10-min scan
                    $bestM = 0
                    $minDiff = 999.0
                    for ($m = 0; $m -lt 1440; $m += 10) {
                        $tCand = $candDay.Date.AddMinutes($m)
                        $u = $tCand.ToUniversalTime()
                        $hUTC = $u.Hour + ($u.Minute / 60.0) + ($u.Second / 3600.0)
                        $asc = Calculate-Lagna $u.Year $u.Month $u.Day $hUTC $lat $lng $ayanamsaVal
                        $diff = [math]::Abs(($asc.vedic - $targetLon + 180) % 360 - 180)
                        if ($diff -lt $minDiff) {
                            $minDiff = $diff
                            $bestM = $m
                        }
                    }

                    # Fine 1-min scan
                    $fineBestDt = $null
                    $fineMinDiff = 999.0
                    $fineLon = 0.0
                    $fineTrop = 0.0
                    for ($m = [math]::Max(0, $bestM - 15); $m -le [math]::Min(1440, $bestM + 16); $m++) {
                        $tCand = $candDay.Date.AddMinutes($m)
                        $u = $tCand.ToUniversalTime()
                        $hUTC = $u.Hour + ($u.Minute / 60.0) + ($u.Second / 3600.0)
                        $asc = Calculate-Lagna $u.Year $u.Month $u.Day $hUTC $lat $lng $ayanamsaVal
                        $diff = [math]::Abs(($asc.vedic - $targetLon + 180) % 360 - 180)
                        if ($diff -lt $fineMinDiff) {
                            $fineMinDiff = $diff
                            $fineBestDt = $tCand
                            $fineLon = $asc.vedic
                            $fineTrop = $asc.tropical
                        }
                    }

                    if ($fineBestDt -and $fineMinDiff -le 0.5) {
                        $cNak = Get-NakshatraDetails $fineLon
                        $cSign = $signs[[math]::Floor($fineLon / 30) % 12]
                        $cDeg = $fineLon % 30.0
                        $cDegD = [int][math]::Floor($cDeg)
                        $cDegM = [int][math]::Floor(($cDeg - $cDegD) * 60)
                        $cDegS = [int][math]::Round((($cDeg - $cDegD) * 60 - $cDegM) * 60)
                        if ($cDegS -eq 60) { $cDegM += 1; $cDegS = 0 }
                        if ($cDegM -eq 60) { $cDegD += 1; $cDegM = 0 }
                        $cDegFormatted = "{0:D2}° {1:D2}' {2:D2}""" -f $cDegD, $cDegM, $cDegS

                        $decObj = Calculate-Declination $fineTrop
                        $isLordMatch = ($cNak.lord -eq $tNak.lord)
                        $isSubMatch = ($cNak.sub_lord -eq $tNak.sub_lord)

                        $matchType = if ($isLordMatch -and $isSubMatch) { "Exact (Degree + Lord + Sub-Lord)" } elseif ($isLordMatch) { "Lord Match" } else { "Degree Match" }

                        $pMatches += [PSCustomObject]@{
                            target_planet = $pName
                            target_sign = $tSign
                            target_degree = [math]::Round($tDeg, 4)
                            target_degree_formatted = $tDegFormatted
                            target_longitude = [math]::Round($targetLon, 4)
                            target_nakshatra = "$($tNak.name) (Pada $($tNak.pada))"
                            target_nakshatra_lord = $tNak.lord
                            target_sub_lord = $tNak.sub_lord
                            occurrence_index = $pMatches.Count + 1
                            year_offset = "$yr Year(s) Ago"
                            datetime = $fineBestDt.ToString("yyyy-MM-dd HH:mm")
                            lagna_sign = $cSign
                            lagna_degree = [math]::Round($cDeg, 4)
                            lagna_degree_formatted = $cDegFormatted
                            lagna_longitude = [math]::Round($fineLon, 4)
                            right_ascension = ""
                            declination = $decObj.formatted
                            declination_deg = $decObj.deg
                            altitude = "00° 00' 00"""
                            azimuth = ""
                            nakshatra = "$($cNak.name) (Pada $($cNak.pada))"
                            nakshatra_lord = $cNak.lord
                            sub_lord = $cNak.sub_lord
                            lord_matched = $isLordMatch
                            sub_matched = $isSubMatch
                            match_type = $matchType
                        }
                    }
                }
                $matches += $pMatches
            }

            $resObj = [PSCustomObject]@{
                status = "success"
                data = [PSCustomObject]@{
                    matches = $matches
                    total_matches = $matches.Count
                    base_datetime = $baseDt.ToString("yyyy-MM-dd HH:mm")
                    latitude = $lat
                    longitude = $lng
                    ayanamsa = if ($ayanamsaStr -eq "1") { "Sidereal Lahiri" } else { "Tropical" }
                    years_span = 2
                    max_entries_per_planet = 3
                }
            }

            $utf8NoBOM = New-Object System.Text.UTF8Encoding($false)
            $json = $resObj | ConvertTo-Json -Depth 6
            $buffer = $utf8NoBOM.GetBytes($json)
            $response.ContentType = "application/json; charset=utf-8"
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
