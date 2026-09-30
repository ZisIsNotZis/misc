cd
find -regextype posix-egrep -iregex '.+\.(te?mp|bac?k|old|log[12]?|du?mp|p(ic)?k(le)?)|.+/(__pycache__|\.ipynb_checkpoints|desktop\.ini)' -print0|xargs -0 rm -r
rm -rf .nv .java .local/share/Trash .sudo_as_admin_successful .viminfo .lesshst .pki .dbus .android .ipython .jupyter .mozilla .cache
t=`bleachbit -l|grep -Pv 'm\.mem|disk|bash|apt'`;sudo bleachbit -c $t;bleachbit -c $t
docker system prune -f;docker volume prune -f
sudo powertop --autotune

cd /mnt/c/Users/z0044sab
find \( -regextype posix-egrep -iregex '.+\.(te?mp|bac?k|old|log[12]?|du?mp|p(ic)?k(le)?)|.+/(__pycache__|\.ipynb_checkpoints|desktop\.ini)' -o -empty \) -print0|xargs -0 rm -r
rm -r `echo AppData/*/*|tr ' ' '\n'|grep -Pi 'te?mp|log|bac?k|du?mp|cache|crash|icon|mpv'` AppData/*/Chrom* AppData/*/Microsoft/Edge

$filePattern = '\.(tmp|temp|bak|back|old|log\d*|dump|dmp|p(ic)?k(le)?)$'
$dirPattern = '.*\\(__pycache__|\.ipynb_checkpoints|desktop\.ini)$'
Get-ChildItem -Hidden -Recurse | Where-Object {
    (($_.PSIsContainer -eq $false) -and (($_.Name -match $filePattern) -or ($_.Length -eq 0))) -or
    (($_.PSIsContainer) -and (($_.FullName -match $dirPattern) -or 
        ($_.GetFiles().Count -eq 0 -and $_.GetDirectories().Count -eq 0)))
} | Remove-Item -Recurse -Force
$regexPattern = 'te?mp|log|bac?k|du?mp|cache|crash|icon|mpv'
Get-ChildItem -Hidden -Path AppData\*\* -Directory | Where-Object { $_.Name -match $regexPattern } | Remove-Item -Recurse -Force
Get-ChildItem -Hidden -Path AppData\*\Chrom* -Directory | Remove-Item -Recurse -Force
Get-ChildItem -Hidden -Path AppData\*\Microsoft\Edge -Directory | Remove-Item -Recurse -Force
