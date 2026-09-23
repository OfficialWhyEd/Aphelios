param([string]$file)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$img = [System.Drawing.Image]::FromFile($file)
[System.Windows.Forms.Clipboard]::SetImage($img); $img.Dispose(); "appunti: $file"
