param(
    [string]$SpecRoot = (Join-Path ([IO.Path]::GetTempPath()) '4-me-not-W30-01-spec-v04/4-me-not-collab-v0.4'),
    [string]$PackRoot = 'C:/Users/keima/.codex/.chatgpt-projects/g-p-696486f280d081918418aa6ea3658d1c/deliverables/4-me-not-v0.4-codex-task-pack'
)
# W30-01 read-only inspection of inputs; writes only this task's evidence JSON.
# Does not import application code, read .env, start a DB, or execute app tests.
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
function Read-Json($path) { Get-Content -LiteralPath $path -Raw | ConvertFrom-Json }
function Source-Ref($path, $pattern) {
    $hit = Select-String -LiteralPath $path -Pattern $pattern | Select-Object -First 1
    if (-not $hit) { throw "Missing reference: $path / $pattern" }
    return "${path}:$($hit.LineNumber)"
}
$schema = Read-Json (Join-Path $SpecRoot 'contracts/memory.schema.json')
$apis = @(Read-Json (Join-Path $SpecRoot 'contracts/api-inventory.json'))
$ops = Read-Json (Join-Path $SpecRoot 'contracts/operation-registry.json')
$features = @(Read-Json (Join-Path $SpecRoot 'contracts/feature-registry.json'))
$tasks = @(Read-Json (Join-Path $SpecRoot 'codex/task-catalog.json'))
$authority = @(Read-Json (Join-Path $SpecRoot 'contracts/api-authority-map.json'))
$openapi = Read-Json (Join-Path $SpecRoot 'contracts/openapi.json')
$requirements = @(Read-Json (Join-Path $SpecRoot 'requirements.json'))
Add-Type -AssemblyName System.IO.Compression.FileSystem
$oldZip = [IO.Compression.ZipFile]::OpenRead((Join-Path $SpecRoot 'archive/v0.3-original.zip'))
try {
    function Read-Old($suffix) {
        $entry = $oldZip.Entries | Where-Object { $_.FullName -match ('(^|/)' + [regex]::Escape($suffix) + '$') -and $_.FullName -notmatch '/archive/' } | Select-Object -First 1
        if (-not $entry) { throw "Missing old asset: $suffix" }
        $reader = [IO.StreamReader]::new($entry.Open())
        try { $reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
    }
    # The v0.3 specification ZIP predates codex/task-catalog.json.
    # The separately delivered v0.3 task pack is the source for the 107 IDs.
    $oldIndexPath = Join-Path (Split-Path $PackRoot -Parent) '4-me-not-v0.3-codex-task-pack/task-index.json'
    $oldIndex = Read-Json $oldIndexPath
    $oldTasks = @($oldIndex.order | ForEach-Object { [pscustomobject]@{id=$_} })
    $oldSchema = Read-Old 'contracts/memory.schema.json'
    $oldApis = @(Read-Old 'contracts/api-inventory.json')
} finally { $oldZip.Dispose() }
$checks = [Collections.Generic.List[object]]::new()
function Check($name, $ok, $count) {
    $checks.Add([ordered]@{name=$name; passed=[bool]$ok; count=$count})
}
$defs = @($schema.'$defs'.PSObject.Properties.Name)
Check 'schema definitions' ($defs.Count -eq 86) $defs.Count
Check 'API inventory' ($apis.Count -eq 38) $apis.Count
Check 'internal operation classes' (@($ops.PSObject.Properties).Count -eq 46) @($ops.PSObject.Properties).Count
Check 'features' ($features.Count -eq 25) $features.Count
Check 'old task IDs retained' ($oldTasks.Count -eq 107 -and @($oldTasks | Where-Object id -notin $tasks.id).Count -eq 0) $oldTasks.Count
$newTasks = @($tasks | Where-Object id -notin $oldTasks.id)
Check 'new task IDs' ($newTasks.Count -eq 23 -and @($newTasks | Where-Object id -notmatch '^W4[123]-').Count -eq 0) $newTasks.Count
Check 'unique task IDs' (@($tasks.id | Sort-Object -Unique).Count -eq 130) $tasks.Count
Check 'task tiers core/experimental/evaluation' (@($tasks | Where-Object tier -eq core).Count -eq 108 -and @($tasks | Where-Object tier -eq experimental).Count -eq 20 -and @($tasks | Where-Object tier -eq evaluation_only).Count -eq 2) 130
$httpOps = @($openapi.paths.PSObject.Properties | ForEach-Object { $_.Value.PSObject.Properties | Where-Object Name -in @('get','post','put','patch','delete') | ForEach-Object { $_.Value.operationId } })
Check 'OpenAPI operation IDs match inventory' ($httpOps.Count -eq 38 -and @($apis.operation | Where-Object { $_ -notin $httpOps }).Count -eq 0) $httpOps.Count
Check 'API request/response definitions resolve' (@($apis | Where-Object { ($_.request -and $_.request -notin $defs) -or $_.response -notin $defs }).Count -eq 0) $apis.Count
Check 'authority map covers API IDs' ($authority.Count -eq 38 -and @($apis.operation | Where-Object { $_ -notin $authority.operation_id }).Count -eq 0) $authority.Count
Check 'authority class references resolve' (@($authority.use_classes | Where-Object { $_ -notin $ops.PSObject.Properties.Name }).Count -eq 0) @($authority.use_classes).Count
Check 'operation feature references resolve' (@($ops.PSObject.Properties | Where-Object { $_.Value.feature_id -notin $features.feature_id }).Count -eq 0) 46
Check 'core does not require experimental feature' (@($features | Where-Object tier -eq core | ForEach-Object depends_on | Where-Object { $_ -in @($features | Where-Object tier -ne core).feature_id }).Count -eq 0) @($features | Where-Object tier -eq core).Count
$schemaText = Get-Content (Join-Path $SpecRoot 'contracts/memory.schema.json') -Raw
$refs = @([regex]::Matches($schemaText, '"\$ref"\s*:\s*"#/\$defs/([^"/]+)"') | ForEach-Object { $_.Groups[1].Value })
Check 'schema internal references resolve' (@($refs | Where-Object { $_ -notin $defs }).Count -eq 0) $refs.Count
$requiredFiles = @('AGENTS.md','README.md','UPDATE-v0.4.md','SPEC.md','docs/state-model.md','docs/feature-catalog.md','docs/authority-matrix.md','WORK_ITEMS.md','codex/tasks/W30-01.md','contracts/memory.schema.json','contracts/api-inventory.json','docs/api-semantics.md','acceptance/promotion.feature','acceptance/v04.feature','docs/decisions.md','docs/migration.md','contracts/feature-registry.json','docs/repository-current.md','docs/data-contract.md','docs/integration-review.md','contracts/openapi.json','contracts/operation-registry.json','contracts/api-authority-map.json','requirements.json','docs/known-open-items.md','docs/file-layout.md','docs/test-plan.md')
Check 'required specification files exist' (@($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $SpecRoot $_)) }).Count -eq 0) $requiredFiles.Count
Check 'catalog task files and reading references exist' (@($tasks | ForEach-Object { @($_.prompt_file) + @($_.reading) } | Where-Object { -not (Test-Path -LiteralPath (Join-Path $SpecRoot $_)) }).Count -eq 0) $tasks.Count
$order = @(Select-String -LiteralPath (Join-Path $PackRoot 'EXECUTION_ORDER.md') -Pattern '^\| \d+ \| \[(W\d+-\d+)\]' | ForEach-Object { $_.Matches[0].Groups[1].Value })
$seen = @(); $validOrder = $true
foreach ($id in $order) { $task = $tasks | Where-Object id -eq $id; if (@($task.depends_on | Where-Object { $_ -notin $seen }).Count) { $validOrder = $false }; $seen += $id }
Check 'execution order dependency closure and next ID' ($validOrder -and $order.Count -eq 130 -and $order[1] -eq 'W30-02') $order.Count
$packIds = @(Get-ChildItem -LiteralPath (Join-Path $PackRoot 'tasks') -Filter 'W*.md' | ForEach-Object BaseName)
Check 'pack IDs match specification catalog' ($packIds.Count -eq 130 -and @($tasks.id | Where-Object { $_ -notin $packIds }).Count -eq 0) $packIds.Count
$acceptance = @('AUTO-003','AUTO-006','AUTO-008','V04-004','V04-037')
Check 'focused acceptance requirements resolve' (@($acceptance | Where-Object { $_ -notin $requirements.acceptance_ids }).Count -eq 0) $acceptance.Count
$codePaths = @( & rg --files --hidden backend frontend/src migrations scripts tests -g '!__pycache__/**' -g '!*.pyc' )
if ($LASTEXITCODE -ne 0) { throw 'rg code scan failed' }
$files = @($codePaths | ForEach-Object { $p = Join-Path $repo $_; [ordered]@{path=$_.Replace('\','/'); sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash; lines=@(Get-Content -LiteralPath $p).Count} })
$routes = @()
foreach ($path in @('backend/app/main.py') + @($codePaths | Where-Object { $_ -match '^backend[\\/]app[\\/]api[\\/].+\.py$' })) {
    $text = Get-Content -LiteralPath (Join-Path $repo $path) -Raw
    $prefixMatch = [regex]::Match($text, 'APIRouter\(prefix="([^"]*)"')
    $prefix = $prefixMatch.Groups[1].Value
    foreach ($m in [regex]::Matches($text, '@(router|app)\.(get|post|patch|delete|put)\(\s*"([^"]*)"')) {
        $line = 1 + [regex]::Matches($text.Substring(0,$m.Index), "`n").Count
        $routePath = if ($m.Groups[1].Value -eq 'app') { $m.Groups[3].Value } else { '/api' + $prefix + $m.Groups[3].Value }
        $routes += [ordered]@{method=$m.Groups[2].Value.ToUpper(); path=$routePath; evidence=$path.Replace('\','/') + ':' + $line}
    }
}
Check 'current application API declarations (not live probing)' ($routes.Count -eq 37 -and @($routes | Where-Object path -like '/v3/*').Count -eq 0) $routes.Count
$symbols = @(); $testEntries = @()
foreach ($path in $codePaths | Where-Object { $_ -match '\.(py|ts|tsx)$' }) {
    $lines = Get-Content -LiteralPath (Join-Path $repo $path)
    for ($i=0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^class (\w+)|^export (?:type|interface) (\w+)') { $symbols += [ordered]@{name=($Matches[1]+$Matches[2]); evidence=$path.Replace('\','/')+':'+($i+1)} }
        if ($path -match '(^tests[\\/].*\.py$|\.test\.ts$)' -and $lines[$i] -match '^\s*def (test_\w+)|^\s*(?:it|test)\(') { $testEntries += [ordered]@{evidence=$path.Replace('\','/')+':'+($i+1); declaration=$lines[$i].Trim()} }
    }
}
$definitionRows = @($defs | ForEach-Object {
    $name=$_
    [ordered]@{name=$name; evidence=(Source-Ref (Join-Path $SpecRoot 'contracts/memory.schema.json') ('^    "'+[regex]::Escape($name)+'":')); same_named_symbols=@($symbols | Where-Object name -eq $name); old_contract=($name -in $oldSchema.'$defs'.PSObject.Properties.Name)}
})
$inventoryPath = Join-Path $PSScriptRoot 'W30-01-inventory.md'
if (Test-Path -LiteralPath $inventoryPath) {
    $inventory = Get-Content -LiteralPath $inventoryPath -Raw
    foreach ($group in @(
        @{name='inventory definition rows'; ids=$defs; expected=86; section='(?s)### A\..*?(?=### B\.)'},
        @{name='inventory API rows'; ids=$apis.operation; expected=38; section='(?s)### B\..*?(?=### C\.)'},
        @{name='inventory operation rows'; ids=$ops.PSObject.Properties.Name; expected=46; section='(?sm)### C\..*?(?=^\| feature \|)'},
        @{name='inventory feature rows'; ids=$features.feature_id; expected=25; section='(?sm)^\| feature \|.*?(?=### D\.)'},
        @{name='inventory task rows'; ids=$tasks.id; expected=130; section='(?s)### E\..*'}
    )) {
        $section = [regex]::Match($inventory, $group.section).Value
        $valid = @($group.ids | Where-Object { [regex]::Matches($section, ('(?m)^\| '+[regex]::Escape($_)+' \|')).Count -eq 1 }).Count
        Check $group.name ($valid -eq $group.expected) $valid
    }
    $references = @([regex]::Matches($inventory, '(?<![/\w])((?:backend|frontend|tests|scripts|tools|migrations|docs/testing)/[A-Za-z0-9_./-]+):(\d+)'))
    $badReferences = @($references | Where-Object {
        $path = Join-Path $repo $_.Groups[1].Value
        -not (Test-Path -LiteralPath $path) -or [int]$_.Groups[2].Value -gt @(Get-Content -LiteralPath $path).Count
    })
    Check 'inventory code paths and line bounds' ($badReferences.Count -eq 0) $references.Count
    $previousPath = Join-Path $PSScriptRoot 'W30-01-evidence.json'
    if (Test-Path -LiteralPath $previousPath) {
        $previous = Read-Json $previousPath
        $changedFiles = @($previous.code_files | Where-Object { (Get-FileHash -LiteralPath (Join-Path $repo $_.path)).Hash -ne $_.sha256 })
        Check 'existing code hashes unchanged from first inspection' ($changedFiles.Count -eq 0) $previous.code_files.Count
    }
}
$result = [ordered]@{
    task='W30-01'; timestamp=(Get-Date -Format o); repo=$repo; spec_root=$SpecRoot; pack_root=$PackRoot
    head=(& git -C $repo rev-parse HEAD); git_status=@(& git -C $repo status --short --untracked-files=all)
    checks=$checks; old_counts=@{definitions=@($oldSchema.'$defs'.PSObject.Properties).Count; api=$oldApis.Count; tasks=$oldTasks.Count}
    current_counts=@{definitions=$defs.Count; api=$apis.Count; operations=@($ops.PSObject.Properties).Count; features=$features.Count; tasks=$tasks.Count; app_routes=$routes.Count; backend_test_declarations=@($testEntries | Where-Object evidence -match '^tests/').Count; frontend_test_declarations=@($testEntries | Where-Object evidence -match '^frontend/').Count}
    spec_files=@($requiredFiles | ForEach-Object { $p=Join-Path $SpecRoot $_; [ordered]@{path=$_; sha256=(Get-FileHash -LiteralPath $p).Hash} })
    archive_sha256=(Get-FileHash -LiteralPath (Join-Path $PackRoot 'reference/4-me-not-collab-v0.4.zip')).Hash
    old_task_index=@{path=$oldIndexPath; sha256=(Get-FileHash -LiteralPath $oldIndexPath).Hash}
    definitions=$definitionRows; apis=$apis; operations=$ops; features=$features; tasks=$tasks; old_task_ids=$oldTasks.id; new_task_ids=$newTasks.id
    routes=$routes; symbols=$symbols; test_entries=$testEntries; code_files=$files
    scope='Static declarations and material reference checks only. No app imports, DB, network, runtime acceptance, independent review or deployed-state verification.'
}
$out = Join-Path $PSScriptRoot 'W30-01-evidence.json'
$result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $out -Encoding utf8
$checks | Format-Table -AutoSize
Write-Output "Evidence: $out"
if (@($checks | Where-Object { -not $_.passed }).Count) { exit 1 }
