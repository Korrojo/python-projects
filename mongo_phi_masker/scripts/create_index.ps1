<#
PowerShell helper to copy indexes from one collection to another using mongosh.
Usage (PowerShell):
  powershell -ExecutionPolicy Bypass -File .\create_index.ps1

If you want to override any value at runtime, pass parameters as usual:
  -Uri, -Db, -Source, -Target, -DryRun

Requirements: mongosh available on PATH. The script writes a temp JS file and executes it with mongosh.
Logs appended to scripts\create_index_ps.log
#>
param(
    [string]$Uri = "mongodb+srv://dabebe:ddemes@ubiquitystg.uniwl.mongodb.net",
    [string]$Db = "UbiquitySTG3",
    [string]$Source = "Container",
    [string]$Target = "Container_20250819",
    [switch]$DryRun
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logFile = Join-Path $scriptDir "create_index_ps.log"
function Log($m){ $line = "$(Get-Date -Format o) $m"; Add-Content -Path $logFile -Value $line; Write-Output $m }

Log "--- PS index copy started ---"
Log "Connect: $Uri | DB: $Db | source: $Source -> target: $Target | dryRun=$($DryRun.IsPresent)"

if ($PSBoundParameters.Count -eq 0) {
    Log "No command-line parameters supplied; using embedded defaults in the script."
}

# create temporary JS file
$tempJs = [System.IO.Path]::GetTempFileName() + ".js"
$dryFlag = $DryRun.IsPresent -eq $true

# Build JS using a single-quoted here-string to avoid PowerShell expanding JS $-expressions like `${indexes.length}`.
# Use placeholders for values that must be injected, then replace them literally.
$js = @'
(function(){
  const dryRun = {DRYRUN};
  const src = db.getCollection("{SOURCE}");
  const tgt = db.getCollection("{TARGET}");
  const indexes = src.getIndexes();
  print(`FOUND_INDEXES:${indexes.length}`);
  indexes.forEach(function(idx){
    try{
      if(idx.name === '_id_') { print('SKIP:_id_'); return; }
      const key = idx.key || idx.keys || idx.keyDocument;
      const opts = Object.assign({}, idx);
      delete opts.key; delete opts.keys; delete opts.keyDocument; delete opts.v; // remove internal fields

      if(dryRun){
        print('DRY-RUN: would create index ' + (opts.name||'<unnamed>') + ' keys=' + JSON.stringify(key) + ' opts=' + JSON.stringify(opts));
        return;
      }

      print('CREATE_START:' + (opts.name||'<unnamed>'));
      tgt.createIndex(key, opts);
      print('CREATE_DONE:' + (opts.name||'<unnamed>'));
    }catch(e){
      print('CREATE_ERROR:' + (idx.name||'<unnamed>') + ':' + e);
    }
  });
})();
'@

# perform literal replacements for placeholders
$js = $js.Replace('{DRYRUN}', $dryFlag.ToString().ToLower())
$js = $js.Replace('{SOURCE}', $Source)
$js = $js.Replace('{TARGET}', $Target)

Set-Content -Path $tempJs -Value $js -Encoding UTF8

try{
    # invoke mongosh
    $mongosh = "mongosh"
    $argList = @("$Uri/$Db", "--quiet", "--file", "$tempJs")
    Log "Running: $mongosh $($argList -join ' ')"

    # Use a separate stderr temp file because Start-Process does not allow stdout and stderr to be the same path
    $errLog = "$logFile.err"
    if (Test-Path $errLog) { Remove-Item $errLog -ErrorAction SilentlyContinue }

    # Run mongosh with real-time streaming output instead of Start-Process (which buffers until completion)
    Log "Starting mongosh with streaming output..."
    & $mongosh $argList[0] $argList[1] $argList[2] $argList[3] 2>&1 | ForEach-Object {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $line = "[$timestamp] $_"
        Add-Content -Path $logFile -Value $line
        Write-Output $line
    }
    $exitCode = $LASTEXITCODE

    # No need to handle separate stderr file since we used 2>&1 above
    # Use a separate stderr temp file because Start-Process does not allow stdout and stderr to be the same path
    $errLog = "$logFile.err"
    if (Test-Path $errLog) { Remove-Item $errLog -ErrorAction SilentlyContinue }

    # Run mongosh with real-time streaming output instead of Start-Process (which buffers until completion)
    Log "Starting mongosh with streaming output..."
    & $mongosh $argList[0] $argList[1] $argList[2] $argList[3] 2>&1 | ForEach-Object {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $line = "[$timestamp] $_"
        Add-Content -Path $logFile -Value $line
        Write-Output $line
    }
    $exitCode = $LASTEXITCODE

    # No need to handle separate stderr file since we used 2>&1 above

    Log "mongosh exit code: $exitCode"
    Log "--- PS index copy finished ---"
} catch {
    Log "FATAL: $_"
} finally {
    Remove-Item -Path $tempJs -ErrorAction SilentlyContinue
}
