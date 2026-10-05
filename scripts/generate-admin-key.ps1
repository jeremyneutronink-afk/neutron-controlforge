$bytes = New-Object byte[] 48

$rng = (
    [System.Security.Cryptography.RandomNumberGenerator]
    ::Create()
)

try {
    $rng.GetBytes(
        $bytes
    )
}
finally {
    $rng.Dispose()
}

$key = (
    [Convert]::ToBase64String(
        $bytes
    )
    .TrimEnd("=")
    .Replace("+", "-")
    .Replace("/", "_")
)

Write-Output $key
