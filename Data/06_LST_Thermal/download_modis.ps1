# Windows PowerShell Download Script for NASA MODIS LST (Patna 2019)
# Prompts for your Earthdata password safely

$Username = "ljprincekashyap_google"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " NASA MODIS LST DOWNLOAD (Patna 2019 Pre-Monsoon Heatwave)" -ForegroundColor Cyan
Write-Host " Username: $Username" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$Password = Read-Host -Prompt "Enter your Earthdata password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password)
$PlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

$TargetDir = $PSScriptRoot
if (-not $TargetDir) { $TargetDir = "." }

$NetrcPath = Join-Path $TargetDir "_netrc_temp"
"machine urs.earthdata.nasa.gov login $Username password $PlainPassword" | Out-File -FilePath $NetrcPath -Encoding ascii

$CookiePath = Join-Path $TargetDir "_cookies_temp.txt"

$Urls = @(
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019177.h25v06.061.2020355121942/MOD11A2.A2019177.h25v06.061.2020355121942.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019169.h25v06.061.2020355044455/MOD11A2.A2019169.h25v06.061.2020355044455.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019161.h25v06.061.2020354200935/MOD11A2.A2019161.h25v06.061.2020354200935.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019153.h25v06.061.2020354125423/MOD11A2.A2019153.h25v06.061.2020354125423.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019145.h25v06.061.2020354014045/MOD11A2.A2019145.h25v06.061.2020354014045.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019137.h25v06.061.2020353083911/MOD11A2.A2019137.h25v06.061.2020353083911.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019129.h25v06.061.2020353004458/MOD11A2.A2019129.h25v06.061.2020353004458.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019121.h25v06.061.2020353002435/MOD11A2.A2019121.h25v06.061.2020353002435.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019113.h25v06.061.2020353000224/MOD11A2.A2019113.h25v06.061.2020353000224.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019105.h25v06.061.2020352234040/MOD11A2.A2019105.h25v06.061.2020352234040.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019097.h25v06.061.2020352231814/MOD11A2.A2019097.h25v06.061.2020352231814.hdf",
    "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD11A2.061/MOD11A2.A2019089.h25v06.061.2020352225637/MOD11A2.A2019089.h25v06.061.2020352225637.hdf"
)

$Total = $Urls.Count
$Count = 0

foreach ($Url in $Urls) {
    $Count++
    $FileName = Split-Path -Leaf $Url
    $DestFile = Join-Path $TargetDir $FileName
    
    if (Test-Path $DestFile) {
        Write-Host "[$Count/$Total] Already exists: $FileName" -ForegroundColor Green
        continue
    }
    
    Write-Host "[$Count/$Total] Downloading $FileName..." -ForegroundColor Yellow
    & curl.exe -f -b $CookiePath -c $CookiePath -L --netrc-file $NetrcPath -g -o $DestFile $Url
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Done!" -ForegroundColor Green
    } else {
        Write-Host "  Failed to download $FileName" -ForegroundColor Red
    }
}

Remove-Item -Force $NetrcPath -ErrorAction SilentlyContinue
Remove-Item -Force $CookiePath -ErrorAction SilentlyContinue

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " All MODIS LST downloads finished!" -ForegroundColor Green
Write-Host " Target directory: $TargetDir" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

