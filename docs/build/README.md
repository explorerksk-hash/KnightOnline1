# Derleme notları (Windows / VS 2022)

## 32-bit derleyici tuzağı — `C1060` / `C3859`

Komut satırından derlerken şu hatalar çıkıyorsa:

```
c1xx : fatal error C1060: derleyicinin yığın alanı kalmadı
c1xx : error C3859: PCH için sanal bellek oluşturulamadı
c1xx : message : sistem 1455 kodunu döndürdü: ... disk belleği dosyası çok küçük
```

bu bir bellek yetersizliği **değil**, adres alanı sınırıdır.

`VsDevCmd.bat -arch=x64` yalnızca **hedef** mimariyi 64-bit yapar; MSBuild
varsayılan olarak **32-bit** `cl.exe` (`Hostx86\x64`) kullanır ve o süreç
~3 GB adres alanına sıkışır. Bu projedeki büyük PCH'ler (N3Base, Ebenezer,
WarFare) o duvara çarpar — makinede 64 GB RAM olsa da sonuç değişmez.

Çözüm, 64-bit derleyiciyi seçmek:

```bat
call "...\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
msbuild All.slnx /p:PreferredToolArchitecture=x64 /p:Configuration=Debug /p:Platform=x64
```

Doğrulamak için: `where cl.exe` çıktısında **`Hostx64`** geçmeli.

Visual Studio arayüzünden derlerken bu sorun görülmez; VS zaten
`PreferredToolArchitecture=x64` kullanır.

## Diğer faydalı bayraklar

| Bayrak | Ne işe yarar |
|---|---|
| `/m:2` | Aynı anda derlenen proje sayısı. Belleği dar makinelerde `/m` (çekirdek sayısı) yerine kullanın. |
| `/p:UseStructuredOutput=false` | VS 2022'nin SARIF çıktı borusunu kapatır; uzun derleyici çıktısında `System.OutOfMemoryException` ile çöküyordu. |
| `/nodeReuse:false` | Derleme bitince artık MSBuild süreçleri bellekte kalmaz. |
