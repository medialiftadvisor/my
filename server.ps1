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
            $json = '{"status":"success","demo_mode":true,"provider":"mock"}'
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
            $response.ContentType = "application/json"
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
            $response.Close()
            continue
        }

        if ($urlPath.StartsWith("/api/astrology/natal-chart")) {
            $json = '{"status":"success","data":{"svg":"<svg width=\"350\" height=\"350\" xmlns=\"http://www.w3.org/2000/svg\"><rect width=\"100%\" height=\"100%\" fill=\"#1a1d24\"/><text x=\"50%\" y=\"50%\" fill=\"#e2e8f0\" dominant-baseline=\"middle\" text-anchor=\"middle\" font-family=\"sans-serif\" font-size=\"14\">Natal Chart Wheel</text></svg>"}}'
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

            $lat = if ($latStr) { [double]$latStr } else { 22.6757521 }
            $lng = if ($lngStr) { [double]$lngStr } else { 88.0495418 }
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
