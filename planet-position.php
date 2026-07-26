<?php
/*
 * This file is part of Prokerala Astrology API PHP SDK
 *
 * © Ennexa Technologies <info@ennexa.com>
 *
 * This source file is subject to the MIT license that is bundled
 * with this source code in the file LICENSE.
 */

use Prokerala\Api\Astrology\Location;
use Prokerala\Common\Api\Exception\QuotaExceededException;
use Prokerala\Common\Api\Exception\RateLimitExceededException;

include 'prepend.inc.php';

/** @var \Prokerala\Common\Api\Client $client */

function calculateLagnaFromScratch($year, $month, $day, $hourUTC, $lat, $lon, $ayanamsa = 24.22) {
    if ($month <= 2) {
        $year -= 1;
        $month += 12;
    }
    $A = floor($year / 100);
    $B = 2 - $A + floor($A / 4);
    $JD = floor(365.25 * ($year + 4716)) + floor(30.6001 * ($month + 1)) + $day + ($hourUTC / 24.0) + $B - 1524.5;

    $T = ($JD - 2451545.0) / 36525.0;
    $GMST_deg = 280.46061837 + 360.98564736629 * ($JD - 2451545.0) + 0.000387933 * $T * $T - ($T * $T * $T) / 38710000.0;
    
    $GMST_deg = fmod($GMST_deg, 360.0);
    if ($GMST_deg < 0) $GMST_deg += 360.0; 

    $RAMC = fmod($GMST_deg + $lon, 360.0);
    if ($RAMC < 0) $RAMC += 360.0;

    $obliquity = 23.4392911;

    $ramc_rad = deg2rad($RAMC);
    $obliq_rad = deg2rad($obliquity);
    $lat_rad = deg2rad($lat);

    $y = cos($ramc_rad);
    $x = -sin($ramc_rad) * cos($obliq_rad) - tan($lat_rad) * sin($obliq_rad);

    $asc_rad = atan2($y, $x);
    $asc_deg = rad2deg($asc_rad);

    $tropical_ascendant = fmod($asc_deg, 360.0);
    if ($tropical_ascendant < 0) $tropical_ascendant += 360.0;

    $vedic_ascendant = fmod($tropical_ascendant - $ayanamsa, 360.0);
    if ($vedic_ascendant < 0) $vedic_ascendant += 360.0;

    $sign_index = floor($vedic_ascendant / 30);
    $degrees_remaining = $vedic_ascendant - ($sign_index * 30);
    $degrees = floor($degrees_remaining);
    $minutes = floor(($degrees_remaining - $degrees) * 60);

    $zodiac_signs = [
        "Mesh (Aries)", "Vrishabha (Taurus)", "Mithun (Gemini)", 
        "Kark (Cancer)", "Simha (Leo)", "Kanya (Virgo)", 
        "Tula (Libra)", "Vrishchika (Scorpio)", "Dhanu (Sagittarius)", 
        "Makar (Capricorn)", "Kumbh (Aquarius)", "Meen (Pisces)"
    ];

    return [
        'raw_degree' => round($vedic_ascendant, 4),
        'sign' => $zodiac_signs[$sign_index],
        'degree' => $degrees,
        'minute' => $minutes
    ];
}

$input = [
    'datetime' => '2020-05-12T09:20:00+05:30',
    'latitude' => '22.6757521',
    'longitude' => '88.0495418', // Kolkata
];

if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['date'], $_POST['time'])) {
    $input_date = $_POST['date'];
    $input_time = $_POST['time'];
    $lat = (float)$_POST['lat'];
    $lon = (float)$_POST['lon'];

    $dateTimeString = $input_date . ' ' . $input_time;
    $localDateTime = new DateTime($dateTimeString, new DateTimeZone('Asia/Kolkata'));
    $localDateTime->setTimezone(new DateTimeZone('UTC'));

    $year = (int)$localDateTime->format('Y');
    $month = (int)$localDateTime->format('n');
    $day = (int)$localDateTime->format('j');
    
    $hour = (int)$localDateTime->format('G');
    $minute = (int)$localDateTime->format('i');
    $hourUTC = $hour + ($minute / 60.0);

    $ayanamsa = 24.22;
    $ascResult = calculateLagnaFromScratch($year, $month, $day, $hourUTC, $lat, $lon, $ayanamsa);
} else {
    $localDateTime = new DateTime($input['datetime']);
    $localDateTime->setTimezone(new DateTimeZone('UTC'));
    $year = (int)$localDateTime->format('Y');
    $month = (int)$localDateTime->format('n');
    $day = (int)$localDateTime->format('j');
    $hour = (int)$localDateTime->format('G');
    $minute = (int)$localDateTime->format('i');
    $hourUTC = $hour + ($minute / 60.0);
    $ascResult = calculateLagnaFromScratch($year, $month, $day, $hourUTC, (float)$input['latitude'], (float)$input['longitude'], 24.22);
}

$datetime = new DateTimeImmutable($input['datetime']);
$tz = $datetime->getTimezone();

$location = new Location($input['latitude'], $input['longitude'], 0, $tz);

try {
    $method = new \Prokerala\Api\Astrology\Service\PlanetPosition($client);
    $result = $method->process($location, $datetime);
    $planets = $result->getPlanetPosition();
    $planetPositionResult = [];
    
    // Add Ascendant (Lagna) calculated from scratch first
    $planetPositionResult[] = [
        'id' => 100,
        'name' => 'Ascendant / Lagna',
        'longitude' => $ascResult['raw_degree'],
        'isRetrograde' => false,
        'position' => 1,
        'degree' => $ascResult['degree'] + ($ascResult['minute'] / 60.0),
        'rasi' => [
            'id' => 0,
            'name' => $ascResult['sign'],
            'lord' => [
                'id' => 0,
                'name' => 'N/A',
                'vedicName' => 'N/A',
            ],
        ],
    ];

    foreach ($planets as $position) {
        $rasi = $position->getRasi();
        $rasiLord = $rasi->getLord();
        $planetPositionResult[] = [
            'id' => $position->getId(),
            'name' => $position->getName(),
            'longitude' => $position->getLongitude(),
            'isRetrograde' => $position->isRetrograde(),
            'position' => $position->getPosition(),
            'degree' => $position->getDegree(),
            'rasi' => [
                'id' => $rasi->getId(),
                'name' => $rasi->getName(),
                'lord' => [
                    'id' => $rasiLord->getId(),
                    'name' => $rasiLord->getName(),
                    'vedicName' => $rasiLord->getVedicName(),
                ],
            ],
        ];
    }
    print_r($planetPositionResult);
} catch (QuotaExceededException $e) {
    echo "Quota Exceeded: " . $e->getMessage() . "\n";
} catch (RateLimitExceededException $e) {
    echo "Rate Limit Exceeded: " . $e->getMessage() . "\n";
}

