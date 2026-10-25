param([Parameter(Mandatory=$true)][string]$Path)
# Local read-only Windows OCR. Invoke Windows PowerShell 5.1, not PowerShell 7.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.Streams.IRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrResult,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime] | Out-Null
function Await-Result($Operation, [Type]$ResultType) {
    $method = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    } | Select-Object -First 1
    $task = $method.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
    if (-not $task.Wait(20000)) { throw 'OCR operation timed out' }
    return $task.Result
}
$netStream = [System.IO.File]::OpenRead($Path)
$stream = [System.IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($netStream)
try {
    $decoder = Await-Result ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Await-Result ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    try {
        $language = New-Object Windows.Globalization.Language('en-US')
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($language)
        if ($null -eq $engine) { throw 'No supported local OCR language' }
        if ($bitmap.PixelWidth -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension -or
            $bitmap.PixelHeight -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension) { throw 'Image exceeds OCR dimensions' }
        $result = Await-Result ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
        $lines = @($result.Lines | ForEach-Object {
            @{text=$_.Text; words=@($_.Words | ForEach-Object {
                @{text=$_.Text; bbox=@($_.BoundingRect.X,$_.BoundingRect.Y,$_.BoundingRect.Width,$_.BoundingRect.Height)}
            })}
        })
        @{language=$engine.RecognizerLanguage.LanguageTag; width=$bitmap.PixelWidth; height=$bitmap.PixelHeight; lines=$lines} |
            ConvertTo-Json -Depth 8 -Compress
    } finally { $bitmap.Dispose() }
} finally {
    $stream.Dispose()
    $netStream.Dispose()
}
