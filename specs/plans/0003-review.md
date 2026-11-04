# Review 0003 — residue noise

- Spec: `specs/active/0003-residue-noise.md`
- Plan: `specs/plans/0003-plan.md`
- Round 1: 2026-11-04, `reviewer` subagent, ayrı salt-okunur oturum (AGENTS.md kural 3)
- Diff: `git diff main..HEAD` on `feature/0003-residue-noise`, 7 commit, 9 dosya
- Status: fix round 1 tamam (10 real düzeltildi, her biri kendi commit'inde) — REVIEW round 2 bekliyor

Bulgular aşağıda **olduğu gibi** kayıtlı: yumuşatılmadı, yeniden sıralanmadı, yorum eklenmedi.
Triyaj (real / noise / investigate) insana aittir ve bu dosyaya triyaj tablosu olarak eklenir.

---

## Round 1 — reviewer subagent, verbatim

### Çalıştırılan doğrulamalar (hepsi bu makinede, Windows/MINGW)

| Komut | Sonuç |
|---|---|
| `./scripts/check` | `CHECK GREEN (full, 6 steps, 7 s)` — exit 0 |
| `./scripts/doctor --strict` | `== result: 0 fail, 0 warn ==` — exit 0 |
| `./scripts/selftest` | `== selftest: 101 passed, 0 failed ==` (POSIX çekirdek-iş-parçacığı senaryosu `skip`) |
| `./scripts/residue` | `RESIDUE CLEAN (full, 2 runs)` — `0 survivor(s), 0 ignored` her iki koşumda |
| `./scripts/residue --fast` | `RESIDUE CLEAN (fast, 2 runs)` — `0 survivor(s), 0 ignored` her iki koşumda |

Üreticinin "her iki profil de bu makinede CLEAN" iddiası **doğrulandı**.

---

### F-1 — Medium — Correctness / Edge cases
**Windows'ta çok satırlı bir komut satırı, süreç olmayan bir "survivor" üretir ve koşumu yanlışlıkla kırmızıya çevirir.**

`scripts/residue:48` her süreci tek satır `pid<TAB>ppid<TAB>command` olarak yazdığını varsayar; ama
`$_.CommandLine.Trim()` gömülü satır sonlarını temizlemez. İçinde `\n` olan bir komut satırı tabloya
**birden çok satır** koyar; devam satırlarının `$1` alanı pid değil, metindir.

Bu makinede, hiçbir şey yapmadan alınan canlı tabloda 360 satırın **21'i** (ikinci ölçümde 44'ü) böyle
hayalet satırdı. Hayalet satır `base`'de yokken `run` ve `again`'de varsa, `newer`/`alive`
(`scripts/residue:68-69`) onu survivor sayar, sınıflandırıcı soyunu yürüyemediği için (`!(q in ppid)`,
`scripts/lib/classify-survivors:41`) **`counted`** der ve `found=1` olur.

Yeniden üretim (scratchpad'de, repoya yazmadan — `$S` scratchpad dizini):

```sh
snap() { powershell.exe -NoProfile -NonInteractive -Command '
  $me = $PID; $all = Get-CimInstance Win32_Process
  $stub = ($all | Where-Object { $_.ProcessId -eq $me }).ParentProcessId
  $all | Where-Object { $_.ProcessId -ne $me -and $_.ProcessId -ne $stub -and $_.ParentProcessId -ne $me } |
    ForEach-Object { "{0}`t{1}`t{2}" -f $_.ProcessId, $_.ParentProcessId, $(if ($_.CommandLine) { $_.CommandLine.Trim() } else { $_.Name }) }
' </dev/null 2>/dev/null | tr -d '\r'; }
snap > "$S/base"
nohup powershell.exe -NoProfile -NonInteractive -Command 'Start-Sleep -Seconds 45
# anew-phantom-marker-xyz' >/dev/null 2>&1 &
sleep 4; snap > "$S/run"; sleep 4; snap > "$S/again"
awk -F'\t' 'NR==FNR{s[$1]=1;next} !($1 in s)' "$S/base" "$S/run" > "$S/new"
awk -F'\t' 'NR==FNR{n[$1]=1;next} ($1 in n)' "$S/again" "$S/new" > "$S/surv"
sh scripts/lib/classify-survivors windows "$S/again" < "$S/surv"
```

Çıktı (ilgili satır):

```
counted	# anew-phantom-marker-xyz"	
```

Yani `scripts/residue:120` şunu basardı: `  survivor  # anew-phantom-marker-xyz  ` ve exit 1.

**Impact:** CB-1 "çıkış kodunu yalnızca check'in başlatmış olabileceği süreçler belirler" diyor; bir metin
parçası süreç değildir. Spec'in ortadan kaldırmak için var olduğu belirsizliğin aynısı Windows'ta duruyor —
üstelik bu depoda betiği en sık çalıştıran şey, komut satırlarında gömülü satır sonu taşıyan ajan
kabuklarıdır. Kusurun **kökeni değişiklikten önceye dayanıyor** (main'de de hayalet satır survivor sayılırdı),
ama CB-1/PB-5 bunu bu spec'in kapsamına alıyor ve üretici tam bu satıra (`:48`) dokundu.

**Recommended action:** Ölçümü satır bazında güvenli hâle getirin — PowerShell tarafında
`($_.CommandLine -replace '\s+',' ')`, ve/veya her iki platform dalının sonunda savunma amaçlı
`awk -F'\t' '$1 ~ /^[0-9]+$/'` süzgeci. Aynı korumanın ikinci yarısı `classify-survivors` içinde olmalı
(sayısal olmayan pid'li satırı reddet/işaretle). Selftest'te sentetik tabloya bozuk bir satır ekleyerek
sınanabilir — bu zaten yardımcının ayrı dosya olma gerekçesi (plan R-7).

---

### F-2 — Medium — Tests
**Plan'ın criterion↔test haritasındaki PB-1 satırı, var olmayan bir teste işaret ediyor.**

`specs/plans/0003-plan.md:90` şöyle diyor: *"PB-1 (bellek toleransı) | `scripts/selftest`: tolerans
satırının biçimi (`… MB vs baseline`) ve aşıldığında kırmızı"*.

`scripts/selftest` içinde böyle bir iddia **yok**:

```
$ grep -n "MB\|tolerance\|baseline" scripts/selftest
76:residue() { run env ANEW_RESIDUE_SETTLE=1 ANEW_RESIDUE_MB=1000000 ... }
87:has "baseline: " ...
121,131: ANEW_RESIDUE_MB=1000000 ...
```

`has "baseline: "` yalnızca baseline **başlık** satırını görür; `… MB vs baseline` biçimi hiç iddia
edilmiyor ve toleransın aşıldığı tek bir senaryo yok (her çağrıda `ANEW_RESIDUE_MB=1000000`). Yeni eklenen
`matches` ifadesi (`scripts/selftest:95`) `… ignored` ile bitip `([;]|$)` ile duruyor — bellek kısmını
kasten kapsam dışı bırakıyor.

**Impact:** AGENTS.md Kural 4 ("Evidence over claims") ve `docs/testing.md` "The contract" ilk maddesi
ihlal ediliyor: harita kanıt gösteriyor, kanıt yok. `scripts/residue:107-112`'deki tolerans mantığı
(örn. karşılaştırmanın ters çevrilmesi) hiçbir testle korunmuyor.

**Ek (aynı dimension, daha küçük):** Spec PB-4 "`ANEW_RESIDUE_SETTLE`/`ANEW_RESIDUE_MB`'nin sayı olmayan
değeri de 2 döndürür" diyor; `scripts/selftest:96-97` yalnızca `SETTLE`'ı sınıyor, `ANEW_RESIDUE_MB=x`
senaryosu yok (`scripts/residue:31`'deki dal kapsanmıyor).

**Recommended action:** (a) Deterministik olan yarısını ekleyin — `matches '[0-9]+ MB available
\(-?[0-9]+ MB vs baseline\)'`; (b) "aşıldığında kırmızı" yarısı sentetikleştirilemiyorsa harita satırını
dürüstçe düzeltin ("review + elle gözlem"), çünkü haritada duran her ad gerçekten var olmalı; (c) tek
satırlık `ANEW_RESIDUE_MB=x → exit 2` senaryosunu ekleyin.

---

### F-3 — Medium-low — Correctness / Edge cases (fail-open)
**`classify-survivors` boş bir süreç tablosuyla çağrıldığında TÜM survivor'ları sessizce yutar.**

`scripts/lib/classify-survivors:37` klasik `NR == FNR` ayrımını kullanıyor ve `:55` girdileri
`"$table" -` olarak veriyor. Birinci dosya **hiç kayıt üretmezse** `NR` ile `FNR` stdin boyunca eşit kalır;
dolayısıyla her survivor satırı "tablo satırı" sanılıp tabloya yazılır ve hiçbir çıktı üretilmez.

Yeniden üretim:

```sh
: > "$S/empty-table"
printf '500\t1\tpython leaked\n501\t1\tsecond leaked\n' > "$S/surv1"
sh scripts/lib/classify-survivors posix "$S/empty-table" < "$S/surv1"; echo "rc=$?"
```

Çıktı: **hiçbir satır**, `rc=0`. İki kalıntı süreç izsiz kayboldu.

**Impact:** Dosyanın kendi başlık yorumu (`:18-19`) "açıklayamadığını sessizce düşüren araç, bu yardımcının
kaldırmak için yazıldığı arıza biçimidir" diyor; bu kod yolu tam olarak onu yapıyor. `scripts/residue`
üzerinden **bugün erişilebilir değil** (`scripts/residue:65`'teki `[ -s "$1" ]` boş tabloyu
`fail_measure`'a çevirir), ama yardımcı kendi usage'ı, kendi argüman doğrulaması ve kendi sözleşmesi olan
bağımsız çağrılabilir bir arayüz; `:25` okunabilirliği denetliyor ama doluluğu denetlemiyor.

**Recommended action:** `:25`'teki kontrolü `[ -s "$table" ]` yapın (veya awk'ta `FILENAME != "-"`
ayrımına geçin). Selftest'e "boş tablo → exit 2 ya da her survivor `counted`" senaryosu ekleyin.

---

### F-4 — Low — Tests
**CB-2'nin asıl iddiası ("her satır kendi sebebini taşır, toplu dipnot değil") residue çıktısı
seviyesinde kanıtlanmıyor.**

`scripts/selftest:124-126` üç ayrı `has` çağrısı kullanıyor:

```
has "ignored — check cannot have started these" ...
has "[kworker/R-selftest]" ...
has "(kernel thread)" ...
```

`has` satır bazlı değil, çıktının herhangi bir yerinde arıyor (`scripts/selftest:18`). Senaryoda
ignored süreç **bir tane** olduğu için, `scripts/residue:116` tek bir toplu dipnot bassaydı
(spec CB-2'nin açıkça yasakladığı biçim) bu üç iddia da geçerdi.

Satır-başına-sebep yalnızca sınıflandırıcı seviyesinde (`scripts/selftest:144-146`,
`has "ignored${T}kernel thread${T}77"`) kanıtlanıyor — ki orası da ayrı bir arayüz, kullanıcının gördüğü
çıktı değil.

**Impact:** Senaryo, davranış bozukken geçebilir. Küçük, ama CB-2'nin tam da ayırt etmek istediği durum bu.

**Recommended action:** Tek satırlık regex'e geçin —
`matches '^ +777 +\[kworker/R-selftest\] +\(kernel thread\)$'` — ve fake tabloya **ikinci, farklı
sebepli** bir ignored süreç ekleyin (POSIX'te ikinci sebep yok, o yüzden alternatif: sınıflandırıcı
senaryosunda Windows tablosuna iki farklı sebepli satırın **aynı çıktıda** ayrı ayrı göründüğü iddiası —
bu zaten `:155-157`'de var, sadece residue çıktısına taşınması gerekiyor).

---

### F-5 — Low — Tests
**CB-3'ün ana kanıtındaki iddia gereğinden gevşek.**

`scripts/selftest:94`: `has "$LEAK" "the survivor is named with its command line"` — marker çıktının
**herhangi** bir yerinde geçse yeter, `ignored` başlığının altında geçse bile. Hemen üstteki negatif
senaryoda (`:89-90`) üretici doğru deseni kullanmış: `grep '^  survivor  ' | grep -qF "$LEAK"`.

Pratikte `exits 1` + `RESIDUE FOUND` birlikte bunu büyük ölçüde telafi ediyor (counted > 0 olmalı), ama
"kırmızılığı başka bir süreç sağlarken leak ignored'a düşmüş" hâli hâlâ yeşil geçer.

**Recommended action:** `:94`'ü `:89-90`'daki desenle aynı hâle getirin.

---

### F-6 — Low — Maintainability / Correctness
**`image()` içinde ölü bir `sub()` ve onu yanlış anlatan bir yorum; boşluk içeren yoldaki
`services.exe` tanınmıyor.**

`scripts/lib/classify-survivors:31`:

```awk
sub(/^"[^"]*"/, "&", s)                     # a quoted path keeps its spaces
```

`&` eşleşmenin kendisidir — bu satır **hiçbir şey yapmıyor**. Yorumun vaat ettiği davranış yok: bir sonraki
`gsub(/"/, "", s)` tırnakları atıyor, sonra `sub(/[ \t].*$/, "", s)` ilk boşlukta kesiyor.

```sh
printf '10\t0\tSystem\n20\t10\t"C:\\Program Files\\Weird\\services.exe" -k\n30\t20\tchild.exe\n' > "$S/t3"
printf '30\t20\tchild.exe\n' > "$S/s3"
sh scripts/lib/classify-survivors windows "$S/t3" < "$S/s3"
# → counted	30	child.exe      (beklenen: ignored OS service)
```

Normal yolla (`C:\WINDOWS\system32\services.exe`) doğru çalışıyor ve gerçek `services.exe` her zaman
system32'dedir — bu makinede `Win32_Process` onun `CommandLine`'ını null döndürüp `Name` yedeğiyle
`services.exe` yazıyor, yani pratik etki şu an sıfır. Bulgunun ağırlığı ölü kod + yanıltıcı yorumda.

**Recommended action:** Ya tırnaklı yolu gerçekten ele alın (önce tırnak içini ayıkla, sonra argümanları
at), ya da satırı ve yorumu silin. İkincisini öneriyorum: davranışı değiştirmez, yalanı kaldırır.

---

### F-7 — Low — Security / Privacy
**`ignored` listesi işletim sistemi süreçlerinin tam komut satırlarını basıyor; bu çıktı kanıt olarak
PR'a yapıştırılmak üzere tasarlanmış.**

`scripts/residue:116` her ignored süreci komut satırıyla basıyor. Bu makinede canlı tabloda böyle bir satır:

```
19284	9804	"C:\WINDOWS\System32\SearchProtocolHost.exe" Global\UsGthrFltPipeMssGthrPipe_S-1-5-21-213581113-3291899650-2438827068-21304214_ ...
```

— makine SID'i açıkta. `docs/testing.md` Evidence policy md. 3 ve planın PB-5 satırı
(`specs/plans/0003-plan.md:94`, "gözlem PR'a yazılır") bu çıktının PR açıklamasına gitmesini öngörüyor.
Eski davranışta yalnızca hayatta kalan birkaç süreç basılıyordu; artık meşgul bir makinede onlarca OS
süreci (kullanıcı adları, profil yolları, bazen argümandaki token'lar) listeleniyor.

**Impact:** `docs/security.md` tehdit modeli "makinenin kendisi ve verilen dosyalar" diyor, bu bir kod
açığı değil; ama kanıt akışıyla birleşince gereksiz bir sızma yüzeyi.

**Recommended action:** `docs/commands.md`'deki `scripts/residue` bölümüne tek cümle: "ignored listesi tam
komut satırlarını içerir (kullanıcı adı, SID); PR'a yapıştırmadan önce kısaltın." Alternatif (daha güçlü):
ignored satırlarında komut satırını ilk ~80 karaktere kırpmak.

---

### F-8 — Low — Correctness / Docs
**Windows'ta servis/COM etkinleştirmesiyle başlayan her süreç, check'in sebep olduğu hâlde ölçüt gereği
daima `ignored` — bu kör nokta belgelenmemiş.**

Ölçüt "soy `services.exe`'ye iniyor mu" olduğundan, DCOM/COM etkinleştirmesiyle doğan her süreç SCM soyuna
düşer. Ölçtüm (70 sn boyunca yoklama):

```
15680:RuntimeBroker.exe <- 1752:svchost.exe <- 1504:services.exe <- 1408:wininit.exe
(9 örneğin hepsi aynı zincirde)
```

Aynı şey `WmiPrvSE.exe` için de geçerli — ki onu başlatan şey **residue'nun kendi ölçümüdür**
(`scripts/residue:43`). Yani aracın kendi kalıntısı artık warm-up ile baseline'a alınmanın yanı sıra
sınıflandırıcı tarafından da otomatik affediliyor.

Bu projede check yalnızca uv/ruff/mypy/pytest çalıştırıyor, hiçbiri uzun ömürlü bir COM nesnesi
etkinleştirmiyor — **bugün için pratik etkisi yok**. Ama `docs/testing.md` pid yeniden kullanımını
dürüstçe yazmışken bu ikinci kör noktayı yazmıyor, ve ikisi aynı sınıftan.

**Recommended action:** `docs/testing.md` Resource hygiene rule 2'deki pid-reuse cümlesinin yanına bir
cümle: "Windows'ta servis/COM etkinleştirmesiyle doğan bir süreç, onu check tetiklemiş olsa da SCM soyuna
düşer ve yok sayılır." Kod değişikliği önermiyorum; ölçütün bilinçli maliyeti.

---

### F-9 — Low — Tests
**`scripts/selftest` atlanan senaryoları özet satırında saymıyor.**

`scripts/selftest:104` Windows'ta `skip  residue: kernel-thread scenario is POSIX only …` basıyor, ama
`passed`/`failed` sayaçlarına dokunmuyor (`:15-17`). Windows'ta özet `== selftest: 101 passed, 0 failed ==`
diyor; Linux'ta aynı özet 7 senaryo daha sayar ve ikisi arasında hiçbir uyarı yok.

**Impact:** Küçük. AGENTS.md Kural 5'in ("tests are protected / skip yasak") ihlali **değil** — bu
platform koşullu, meşru bir atlama ve CI `doctor` job'ı `ubuntu-latest`'te koştuğu için senaryo her
push'ta gerçekten çalışıyor, çürümesi mümkün değil (aşağıdaki "Üreticinin işaretledikleri" bölümüne bakın).
Ama "N passed, 0 failed" satırı, atlananları gizleyerek Windows'taki kapsamı olduğundan geniş gösteriyor.

**Recommended action:** `skipped` sayacı ekleyip özete yazdırın (`== selftest: N passed, 0 failed, 1 skipped ==`).

---

### F-10 — Low — Maintainability
**`scripts/lib/classify-survivors` çalıştırılabilir bit'i olmadan commit edilmiş.**

```
$ git ls-files -s scripts/
100755 … scripts/check
100755 … scripts/doctor
100755 … scripts/init
100644 … scripts/lib/classify-survivors   ← tek istisna
100755 … scripts/residue
100755 … scripts/selftest
```

Dosyanın `#!/bin/sh` shebang'i ve kendi usage satırı var (`scripts/lib/classify-survivors:1,7,23`), yani
doğrudan çağrılmak üzere tasarlanmış; POSIX'te `./scripts/lib/classify-survivors …` permission denied verir.
`scripts/residue:99` ve selftest `sh <dosya>` ile çağırdığı için bugün çalışıyor.

**Recommended action:** `git update-index --chmod=+x scripts/lib/classify-survivors`.

---

### F-11 — Info — Portability (kapsam dışı, kayda geçsin)
POSIX dalında tek OS kökü pid 2. macOS'ta (ve orphan'ları bir subreaper'a devreden kurulumlarda) sistem
daemon'ları `launchd` (pid 1) soyundadır; pid 1 bilinçli olarak kök sayılmadığı için ölçüm sırasında
beliren `mdworker`/`XProtect` gibi süreçler `counted` olur — yani bu değişikliğin Linux ve Windows'ta
kaldırdığı kararsızlık macOS'ta aynen durur. Spec "Out of scope" listesi platform kapsamını genişletmeyi
dışarıda bıraktığı için **bulgu değil**; ancak `docs/testing.md`'nin yeni metni ölçütü "POSIX" diye
genelleştiriyor. İsterseniz "Linux" demek daha dürüst olur. Aksiyon önermiyorum.

---

## Dimension özetleri

**Correctness (CB-1..CB-4, PB-1..PB-6):**
- CB-1 — **büyük ölçüde karşılanıyor, F-1 ile çekinceli.** İki küme var, çıkış kodunu yalnız `counted`
  belirliyor (`scripts/residue:104,118-121`). Ölçüt soy zinciri; bu makinede canlı tablonun 360 satırının
  209'u `OS service`, 6'sı `system process` olarak ayrıldı — ölçüt gerçekten ayırıyor. Çekince: Windows'ta
  süreç olmayan bir metin satırı `counted` olabiliyor (F-1).
- CB-2 — kod doğru (`scripts/residue:114-117`, satır başına sebep), **testi zayıf** (F-4).
- CB-3 — karşılanıyor: `$LEAK` senaryosu exit 1 + `RESIDUE FOUND (full)` + komut satırı; selftest'te
  bu makinede geçti. İddia gevşek (F-5).
- CB-4 — **clean.** `docs/testing.md:72-90` rule 1 ve rule 2 aynı ölçütü söylüyor, betikle ve
  `docs/commands.md:94-107` ile tutarlı; pid yeniden kullanımı dürüstçe yazılmış.
- PB-1 — kod korunmuş (`scripts/residue:107-112`, `:77` notu), **kanıtı yok** (F-2).
- PB-2 — clean (selftest `:84`, bu makinede geçti).
- PB-3 — clean (`scripts/residue:87,91-97`; selftest `:88-90`).
- PB-4 — clean; `--fsat → 2`, `SETTLE=x → 2` doğrulandı. `ANEW_RESIDUE_MB=x` kapsanmıyor (F-2 eki).
- PB-5 — Windows'ta iki profil de CLEAN (yukarıdaki tablo); Linux CI job'ı değişmedi. Platform
  tespiti ve `fail_measure` yolu korunmuş (`scripts/residue:38,67`).
- PB-6 — clean. `scripts/doctor`, `workflows/bootstrap.md` diffte yok; `./scripts/doctor --strict` 0 fail;
  `.github/workflows/check.yml` yalnızca yorum değişti.

**Plan conformance — clean.** `git diff --name-only main..HEAD` tam olarak planın dosya listesi: 9 dosya,
fazlası yok, eksiği yok. Plan'ın "`scripts/doctor` değişmez" gerekçesi de doğru: `scripts/doctor:215`
sabit `init doctor check residue selftest` listesini dolaşıyor, `scripts/lib/` oraya girmiyor; `doctor`'ın
core-file listesi (`scripts/doctor:20-31`) zaten yalnızca `scripts/check`'i içeriyor.
*Not (bulgu değil):* dosya listesi onaydan sonra `fa160ec` ile genişletildi (spec dosyasının kendisi
eklendi). R-6 kararı zaten spec'in düzeltilmesini onayladığı için bu kayıt tutma; yine de onaylı bir planın
dosya listesi değiştiğinde onay satırının altına tarihli bir not düşmek izlenebilirliği artırır.

**Security — F-7 dışında clean.** Ağ yok, secret yok, SQL yok, kullanıcı içeriği yok. Yeni betik
`awk`'ı sabit program metniyle çağırıyor, veriyi `-v` ve dosya argümanıyla geçiriyor — komut satırı
içeriği `eval`/shell'e girmiyor. `classify-survivors` argümanları whitelist'le doğrulanıyor
(`:21-24`), tablo yolu yalnızca okunuyor. Geçici dizin `mktemp -d` + `trap … EXIT INT TERM`
(`scripts/residue:33-34`) korunmuş. Repoya hiçbir çıktı yazılmıyor (Evidence policy md. 2 ✓).

**Edge cases — F-1, F-3, F-6 dışında clean.** Bizzat sınadım:
- Soy döngüsü (A↔B): sonsuz döngüye girmiyor, 64 adımdan sonra `counted` (`:40`). ✓
- Kendi ebeveyni olan süreç: `counted`, takılmıyor (`:49`). ✓
- Boş stdin: çıktı yok, rc=0. ✓
- Eksik alanlı survivor satırı: çöküyor değil, boş komutla basıyor.
- Tabloda olmayan ata: `counted` (fail-closed). ✓
- Soy 64 seviyeden derinse: `counted` (fail-closed). ✓

**Performance — clean.** Ölçtüm: `./scripts/residue` 47.8 s, `--fast` 45.2 s duvar saati; bunun
~40 saniyesi `check`'in iki koşumu + 3×5 s settle. Eklenen iş koşum başına ~350 satırlık bir awk geçişi;
ölçülebilir bir maliyeti yok. N+1 yok, gereksiz materyalizasyon yok.

**Tests — F-2 (asıl), F-4, F-5, F-9.** Haritadaki diğer tüm adlar `scripts/selftest`'te gerçekten var ve
bu makinede geçiyor (101/101). Sentetik tablo senaryoları davranışı iddia ediyor, çıkış kodunu değil
(`counted`/`ignored` + sebep + pid tek tek kontrol ediliyor). Fake-`ps` senaryo çifti iyi kurulmuş:
tek başına her iki yön de kandırılabilirdi, ama "hepsi ignored" senaryo 2'de, "hepsi counted" senaryo 1'de
düşer — tamamlayıcılar. `$LEAK`, abort ve `--fsat` senaryoları olduğu gibi korunmuş (AGENTS.md Kural 5 ✓).

**Maintainability — F-6, F-10 dışında clean.** Adlandırma açık (`counted`/`ignored`, `measure`,
`newer`/`alive`), yorumlar *niçin*'i anlatıyor. POSIX `/bin/sh` taşınabilirliği doğru: `local` yok,
bashism yok, `$(( ))`/`case`/`trap`/heredoc standart; `$(printf '\t')` doğru kullanım. Ölü kod yalnızca
F-6'daki satır. Katman ihlali yok (uygulama koduna dokunulmadı). Commit'ler `docs/git.md` ile uyumlu:
Conventional Commits + `[plan 0003/N]`, branch `feature/0003-residue-noise`.

---

## Üreticinin kendi işaretledikleri (bağımsız doğrulama)

**1. POSIX çekirdek-iş-parçacığı senaryosunun Windows'ta atlanması — kabul edilebilir, çürümez.**
CI'daki `doctor` job'ı `ubuntu-latest` üzerinde `./scripts/selftest` çalıştırıyor
(`.github/workflows/check.yml:8,15-16`), yani senaryo her push ve her PR'da gerçekten koşuyor. Fark edilmeden
çürümesi mümkün değil. Kalan boşluk iki tane ve ikisi de küçük: (a) özet satırı atlananı saymıyor (F-9);
(b) Windows **ölçüm dalının** (PowerShell tablo kurulumu) hiçbir otomatik testi yok — Windows yalnızca
sentetik tablolarla sınanıyor. Tam da bu boşluk F-1'in fark edilmemesine yol açtı. F-1'in önerdiğim
düzeltmesi (sayısal pid süzgeci) bu dalı sentetikleştirilebilir hâle de getirir.

**2. Windows ölçümünün kendini, çocuklarını ve shell stub'ını tablodan çıkarması — soy yürüyüşünü
sessizce bozmuyor.** `$stub`'ın ne olduğunu ölçtüm: `stub is: sh.exe` — yani residue betiğinin **kendi
kabuğu** tablodan düşüyor. Bunun yönü güvenli: tablodan satır **çıkarmak** yalnızca soy yürüyüşünün daha
erken kırılmasına yol açar, kırılma da `counted` demektir (`classify-survivors:41`). Yani dışlama en kötü
ihtimalle **yanlış kırmızı** üretir, asla yanlış yeşil. Pratikte ise dışlanan pid'lerin çocuğu olan bir
kalıntı yok: check `sh scripts/check` olarak residue kabuğunun altında koşuyor ve ölen bir ebeveyni olan
kalıntı zaten `counted` oluyor. Dışlama her ölçümde tutarlı (aynı `sh`), dolayısıyla baseline/run farkına
gürültü de katmıyor. **Bu konuda bulgu yok.**

**3. Yürünemeyen soyun "counted" sayılması (fail-closed) — doğru uygulanmış; gerçekçi bir check
kalıntısının sessizce yok sayıldığı tek yol belgelenmiş olanlar.** Testlerim fail-closed davranışını
doğruladı (tabloda olmayan ata, döngü, 64 seviye, kendi ebeveyni — hepsi `counted`). Sessiz yok sayma için
bulduğum yollar: (a) pid yeniden kullanımı — plan R-4'te ve `docs/testing.md`'de yazılı, kabul edilmiş;
(b) Windows'ta servis/COM etkinleştirmesi — **yazılı değil**, F-8; (c) boş tablo — F-3, bugün residue
üzerinden erişilemez. POSIX'te check'in yetimi pid 1'e devredilir ve pid 1 kök sayılmadığı için
`counted` olur; bunu hem sentetik tabloda hem fake-`ps` senaryosunda doğruladım.

**4. "İki profil de CLEAN" ve "`backgroundTaskHost.exe`, `services.exe` soyundan" iddiaları.**
Birincisini **yeniden ölçtüm ve doğruladım** (yukarıdaki tablo; her iki profil, her iki koşum
`0 survivor(s), 0 ignored`). Ne var ki benim koşumlarımda hiç `ignored` süreç belirmedi — yani gerçek
makine koşumu "ignore" yolunu **hiç çalıştırmadı**; CLEAN sonucu ölçütün doğruluğunu değil yalnızca
regresyon olmadığını gösteriyor.

İkincisini **birebir yeniden üretemedim**: 70 saniyelik yoklama boyunca `backgroundTaskHost.exe` ve
`updater.exe` bu makinede hiç çalışmadı. Dolaylı doğrulama yaptım ve ölçüt sağlam çıktı:
`services.exe` pid 1504 ← `wininit.exe` 1408; `SearchProtocolHost.exe` 19284 ← `SearchIndexer.exe` 9804 ←
`services.exe` 1504; aynı aileden `RuntimeBroker.exe`'nin dokuz örneği
`svchost.exe 1752 ← services.exe 1504` zincirinde; canlı tablonun 209 satırı `OS service` olarak ayrıldı.
`backgroundTaskHost.exe` de UWP arka plan görevlerini DcomLaunch/RuntimeBroker üzerinden başlatıldığı için
aynı zincire düşer. **R-5'in kapanışı inandırıcı ama benim turumda doğrudan yeniden üretilemedi** —
triyajda bunu "kanıt üreticinin tek seferlik gözlemi" olarak işaretlemenizi öneririm; CB-1 bu tek sürece
bağlı değil, ölçütün kendisi 215 süreçte bağımsız olarak doğrulandı.

---

## Verdict

Değişiklik planına birebir uyuyor, spec'in asıl derdini (süreç sayısı → sahiplik) doğru çözüyor,
dokümanlar betikle aynı şeyi söylüyor ve tüm doğrulama komutları bu makinede yeşil. Ciddi hiçbir mimari
veya güvenlik sorunu yok.

Triyaja giden iki şey öne çıkıyor: **F-1** (Windows'ta hayalet survivor — spec'in kaldırmaya çalıştığı
kararsızlığın Windows'taki kalıntısı) ve **F-2** (plan haritası var olmayan bir teste işaret ediyor,
AGENTS.md Kural 4). Gerisi küçük sertleştirme ve belgeleme işleri.

**STOP — segment burada bitiyor.** Triyaj (real / noise / investigate) insana ait; "investigate" çıkanlar
R-05 ile QA'ya minimal yeniden üretim için gider, doğrudan düzeltmeye değil.

---

## Triage — round 1

Triyaj: MuaddibL, 2026-11-04. 10 real, 1 noise, 0 investigate — hiçbiri `investigate` değil, çünkü
her bulgu ya yeniden üretim komutuyla ya da doğrudan `grep`/`git ls-files` çıktısıyla geldi;
R-05'e gidecek belirsiz bir gözlem kalmadı.

| # | Severity | Dimension | Verdict | Karar / gerekçe |
|---|---|---|---|---|
| F-1 | Medium | Correctness | **real** | Yeniden üretildi; hayalet satır koşumu kırmızıya çeviriyor. Ölçüm satır bazında güvenli hâle gelir: sayısal pid süzgeci (her iki dal) + classifier'da sayısal olmayan pid reddi + sentetik bozuk satır senaryosu. |
| F-2 | Medium | Tests | **real** | Harita var olmayan bir teste işaret ediyor — AGENTS.md kural 4. Deterministik yarısı test edilir (`… MB vs baseline` biçimi, `ANEW_RESIDUE_MB=x → 2`), edilemeyen yarısı için harita satırı dürüstçe düzeltilir. |
| F-3 | Medium-low | Correctness | **real** | Fail-open, dosyanın kendi başlık yorumunun yasakladığı biçim. Bugün `residue` üzerinden erişilemez ama yardımcının kendi arayüzü var. `-r` → `-s` + senaryo. |
| F-4 | Low | Tests | **real** | Senaryo, davranış bozukken (toplu dipnot) geçer — CB-2'nin ayırt etmek için var olduğu durum. Satır bazlı `matches`. |
| F-5 | Low | Tests | **real** | Aynı sınıf; doğru desen hemen üstteki senaryoda zaten var. |
| F-6 | Low | Maintainability | **real** | Ölü `sub()` + onu yanlış anlatan yorum. Reviewer'ın ikinci seçeneği: satırı ve yorumu sil, davranış değişmez. |
| F-7 | Low | Security | **real** | Çıktı PB-5 gereği PR'a gidiyor ve SID/kullanıcı adı taşıyor. Kırpma **değil** — kırpmak teşhisi bozar; `docs/commands.md`'ye tek cümlelik uyarı. |
| F-8 | Low | Docs | **real** | pid yeniden kullanımı yazılıyken aynı sınıftan ikinci kör noktayı yazmamak tutarsız. Kod değişikliği yok, `docs/testing.md` rule 2'ye tek cümle. |
| F-9 | Low | Tests | **real** | "101 passed, 0 failed" Windows'ta kapsamı olduğundan geniş gösteriyor. `skipped` sayacı + özet satırı. |
| F-10 | Low | Maintainability | **real** | Shebang'i ve usage'ı olan dosya POSIX'te çalıştırılamıyor; `scripts/` altındaki tek istisna. |
| F-11 | Info | Portability | **noise** | Reviewer'ın kendisi "bulgu değil" diyor; macOS spec'in "Out of scope" listesinde. Aksiyon yok. |

### Triyajdan çıkan, bulgu olmayan iki kayıt
- **R-5'in kanıtı**: reviewer `backgroundTaskHost.exe`/`updater.exe` gözlemini kendi turunda yeniden
  üretemedi (o süreçler çalışmıyordu), ölçütü 215 süreç üzerinden dolaylı doğruladı. Planın R-5
  satırına kanıtın tek seferlik gözlem olduğu not düşülür.
- **Dosya listesinin onaydan sonra genişlemesi** (`fa160ec`): planın onay satırının altına tarihli
  bir not. İzlenebilirlik, kusur değil.

### Fix round 1 — sıra
F-1 → F-3 → F-6 (kod) → F-2 → F-4 → F-5 → F-9 (testler) → F-7 → F-8 (dokümanlar) → F-10 (mod biti).
Her real bulgu kendi commit'inde, `[review 0003/F-n]` referansıyla; her commit sonrası
`./scripts/check --fast`, tur sonunda tam yeşil + `scripts/selftest` + iki residue profili
(`prompts/build.md` §fixes). Sonra fix diff'i yeniden REVIEW'a gider.

### Fix round 1 — sonuç (2026-11-04)

| # | Commit | Ne değişti |
|---|---|---|
| F-1 | `1ee5456` | Ölçüm satır sonlarını/sekmeleri boşluğa katlıyor, yalnız sayısal pid'li satırlar kalıyor (iki platform); sınıflandırıcı bozuk satırı reddediyor (exit 2); fake-`ps` senaryosuna sarılmış komut satırı, sentetik tabloya reddedilen satır eklendi |
| F-2 | `9d03e0b` | `… MB vs baseline` biçimi iddia ediliyor (bellek ölçülemiyorsa `skip`), `ANEW_RESIDUE_MB=x → 2` senaryosu eklendi; PB-1 harita satırı eşik dalının testi olmadığını yazıyor |
| F-3 | `ffefb7c` | Boş süreç tablosu reddediliyor (`-s`), senaryosuyla |
| F-4 | `290d9ba` | `ignored` satırı tek satırlık regex'le çivilendi (iki fake-`ps` senaryosunda da) |
| F-5 | `764cd73` | `$LEAK` artık `^  survivor  ` başlığının altında aranıyor |
| F-6 | `8bc4571` | Ölü `sub()` ve yanlış yorum silindi, gerçek davranış yazıldı |
| F-7 | `d4ac2e2` | `docs/commands.md`: ignored listesi PR'a kısaltılmadan yapıştırılmaz (tam komut satırı, SID) |
| F-8 | `3295aeb` | `docs/testing.md` rule 2: Windows'ta servis/COM etkinleştirmesi ikinci kör nokta olarak yazıldı |
| F-9 | `9326494` | `skipped` sayacı + özet satırı + `docs/commands.md` "Stops at" |
| F-10 | `b3f6cb2` | Çalıştırılabilir bit |
| F-11 | — | noise, aksiyon yok |
| kayıt | `0564e99` | R-5'in kanıtı tek seferlik gözlem olarak işaretlendi; onay sonrası dosya listesi değişikliği not edildi |

Doğrulama (bu makinede, fix turu bitiminde): `./scripts/check` → `CHECK GREEN (full, 6 steps, 8 s)` ·
`./scripts/doctor --strict` → `0 fail, 0 warn` · `./scripts/selftest` → `107 passed, 0 failed, 1 skipped` ·
`./scripts/residue` → `RESIDUE CLEAN (full, 2 runs)` · `./scripts/residue --fast` → `RESIDUE CLEAN (fast, 2 runs)`.
Fast profil iki koşumda önce kırmızıydı: tek survivor her ikisinde de ölçüm sırasında tarayıcının
başlattığı bir Chrome renderer'ıydı — ölçütün doğru davranışı (tarayıcı OS servisi değil), makinenin
boşta olmaması. Üçüncü koşum temiz.

**Sıradaki: REVIEW round 2** — fix diff'i (`ec4a91c..HEAD`) bağımsız bir incelemeye gider; üretici
kendi işini doğrulamaz.
