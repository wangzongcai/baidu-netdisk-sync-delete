# 启动带调试端口的 Edge（每次全新临时 profile，不保存登录态）
# 路径全部相对脚本所在目录，换电脑直接跑，不用改
$ErrorActionPreference = "Stop"
$port = 9222
$prefix = "youzi_edge_profile_"
$tmpRoot = [System.IO.Path]::GetTempPath()
# 清理异常退出留下的旧临时配置；正在使用的目录因文件占用会跳过
Get-ChildItem $tmpRoot -Directory -Filter "$prefix*" -ErrorAction SilentlyContinue |
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-1) } |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
$ud = Join-Path $tmpRoot ($prefix + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $ud | Out-Null

# 自动定位 msedge.exe（64 位 / 32 位 / 默认安装位置都试一遍）
$cands = @(
    "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe"
)
$edge = $cands | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { Write-Output "ERROR: 没找到 msedge.exe，请手动确认 Edge 安装位置"; return }

# 初始窗口放在屏幕左侧，占工作区宽度 2/3；主程序启动后还会再精确搬一次窗口
Add-Type -AssemblyName System.Windows.Forms
$wa = [System.Windows.Forms.SystemInformation]::WorkingArea
$winW = [int]($wa.Width * 2 / 3)
$winH = [int]$wa.Height

# 直接打开清理页：每次全新 profile，未登录会弹登录框，登录完成后仍回到这一页
# 禁用 Edge 自己的微软账户自动登录/同步确认框，不影响百度网盘扫码登录
$edgeFlags = @("--disable-sync", "--disable-features=msEdgeAutoLogon,msEdgeAutoSignIn,msEdgeSigninInterception,msEdgeSyncConsent,msSignIn,msEdgeSignIn")
$argsList = @("--remote-debugging-port=$port", "--user-data-dir=$ud", "--no-first-run",
  "--no-default-browser-check") + $edgeFlags + @("--window-position=0,0", "--window-size=$winW,$winH",
  "https://pan.baidu.com/disk/clear")
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
