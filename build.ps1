# 打包脚本：参数固定在这里，避免每次手敲漏掉关键项
#
# 两个容易忘的参数：
#   --windowed        必须是窗口程序，否则 exe 双击时多弹一个黑色命令行窗口
#   --collect-all playwright  必须带 playwright 全部文件，否则缺 node.exe 连不上 Edge
#
# 用法：在本目录执行  powershell -ExecutionPolicy Bypass -File build.ps1
# 产物在 dist_tmp\双端同步删除\，确认无误后再复制到 dist\ 覆盖旧版。

$py = "D:\aaa程序安装目录\python\python.exe"

Set-Location $PSScriptRoot

& $py -m PyInstaller `
    --noconfirm `
    --onedir `
    --windowed `
    --name "双端同步删除" `
    --distpath dist_tmp `
    --workpath build_tmp `
    --add-data "edge_icon.png;." `
    --collect-all playwright `
    app_gui.py

if ($?) {
    Write-Output "打包完成：dist_tmp\双端同步删除\双端同步删除.exe"
} else {
    Write-Output "打包失败，检查上面的报错"
}
