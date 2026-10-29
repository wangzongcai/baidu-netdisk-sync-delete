# 启动带调试端口的 Edge（独立 profile，保留登录态）
# 路径全部相对脚本所在目录，换电脑直接跑，不用改
$ErrorActionPreference = "Stop"
$port = 9222
$ud = Join-Path $PSScriptRoot "_edge_profile"
if (-not (Test-Path $ud)) { New-Item -ItemType Directory -Force -Path $ud | Out-Null }

# 自动定位 msedge.exe（64 位 / 32 位 / 默认安装位置都试一遍）
$cands = @(
    "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe"
)
$edge = $cands | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { Write-Output "ERROR: 没找到 msedge.exe，请手动确认 Edge 安装位置"; return }

# 先关掉占用同一个 profile 的旧实例，否则单实例合并会让调试端口失效
Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match [regex]::Escape($ud) } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

# 直接打开清理页：未登录会自动弹登录框，登录完成后仍回到这一页
$argsList = @("--remote-debugging-port=$port", "--user-data-dir=$ud", "--no-first-run", "https://pan.baidu.com/disk/clear")
Start-Process -FilePath $edge -ArgumentList $argsList -WindowStyle Normal

# 等待端口就绪
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $v = Invoke-RestMethod "http://127.0.0.1:$port/json/version" -TimeoutSec 2
        Write-Output "OK: 调试端口已就绪, Edge $($v.Browser)"
        return
    } catch {}
}
Write-Output "ERROR: 端口 $port 未就绪"
