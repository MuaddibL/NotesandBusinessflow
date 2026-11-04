# Review 0003 — residue noise

- Spec: `specs/active/0003-residue-noise.md`
- Plan: `specs/plans/0003-plan.md`
- Round 1: 2026-11-04, `reviewer` subagent, ayrı salt-okunur oturum (AGENTS.md kural 3)
- Diff: `git diff main..HEAD` on `feature/0003-residue-noise`, 7 commit, 9 dosya
- Status: round 4 triyajı tamam (3 real; R-06 insan kararıyla aşıldı) — fix round 4 sürüyor

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

---

## Round 2 — reviewer subagent, verbatim (fix diff `ec4a91c..HEAD`)

- 2026-11-04, `reviewer` subagent, ayrı salt-okunur oturum (AGENTS.md kural 3)
- Aşağısı **olduğu gibi** kayıtlı: yumuşatılmadı, yeniden sıralanmadı, yorum eklenmedi.

# Review 0003 — round 2 (fix diff `ec4a91c..HEAD`)

- Rol: Reviewer (`docs/roles/reviewer.md`), ayrı salt-okunur oturum, AGENTS.md kural 3
- Diff: `git diff ec4a91c..HEAD` (13 commit, 7 dosya) · bağlam: `git diff main..HEAD` (10 dosya)
- Depoya hiçbir şey yazılmadı; `git status --porcelain` boş. Geçici dosyalar yalnızca scratchpad'de:
  `C:\Users\BERK~1.CEN\AppData\Local\Temp\claude\C--Projeler-notesandbusinessflow\256c79e0-c378-4bb4-9cbd-8dab5b43fe6e\scratchpad`

## Çalıştırılan doğrulamalar (bu makinede, Windows/MINGW)

| Komut | Sonuç | Üreticinin iddiası |
|---|---|---|
| `./scripts/check` | `CHECK GREEN (full, 6 steps, 7 s)` — exit 0 | doğrulandı (8 s → 7 s, yalnız süre) |
| `./scripts/doctor --strict` | `== result: 0 fail, 0 warn ==` | doğrulandı |
| `./scripts/selftest` | `== selftest: 107 passed, 0 failed, 1 skipped ==` | doğrulandı |
| `./scripts/residue --fast` | `RESIDUE CLEAN (fast, 2 runs)` — ilk denemede | doğrulandı |
| `./scripts/residue` (1. koşum) | **`RESIDUE FOUND (full)`** — iki `msedgewebview2.exe --type=renderer` (MSTeams) survivor | **çürütüldü** (aşağıda F-12) |
| `./scripts/residue` (2. koşum) | `RESIDUE CLEAN (full, 2 runs)` | — |
| `git ls-files -s scripts/` | `100755 scripts/lib/classify-survivors` | doğrulandı (F-10 kapandı) |

Ek olarak, POSIX-only senaryoları Linux'ta koşamadığım için **gerçek davranışa karşı** doğruladım:
scriptleri scratchpad'e kopyalayıp PATH'e sahte `ps` + `echo Linux` yazan sahte `uname` koyarak
`scripts/residue`'yu POSIX dalına zorladım (depoya dokunmadan):

```
# $S = scratchpad;  $S/w = scripts/{check,residue,lib/classify-survivors} kopyası,
# $S/fakeps/ps = selftest'teki sahte tablo (sarılmış satır dâhil), $S/fakeps/uname = "echo Linux"
PATH="$S/fakeps:$PATH" FAKEPS_CALLS="$S/fakeps/calls" ANEW_RESIDUE_SETTLE=1 \
  ANEW_RESIDUE_MB=1000000 sh "$S/w/scripts/residue" --fast
```

Çıktı (`cat -A` ile, sondaki boşluk yok):
```
after run 2: 4 processes, 0 survivor(s), 1 ignored$
  ignored — check cannot have started these; they do not decide the result:$
    777  [kworker/R-selftest]  (kernel thread)$
RESIDUE CLEAN (fast, 2 runs)$
```
FAKEPS_LEAK=1 ile: exit 1, `  survivor  888  python -m pytest (orphaned by check)` + aynı ignored satırı.

→ `scripts/selftest:146,155`'teki `^ +777 +\[kworker/R-selftest\] +\(kernel thread\)$`,
`:147`'deki `after run 2: … 0 survivor\(s\), 1 ignored`, `:148`'deki `hasnt`, `:154`'teki
`survivor  888 …` **gerçek çıktıyla birebir eşleşiyor**. Sarılmış satır çıktıda hiç görünmüyor.

Testin gücünü de ölçtüm: `scripts/residue:67`'deki süzgeci kaldırılmış bir kopyayla aynı senaryo
`rc=2` + `classify-survivors: malformed survivor line …` + `residue: cannot classify survivors`
veriyor, yani senaryonun `exits 0` iddiası regresyonu gerçekten yakalıyor. İki yarım (süzgeç +
sınıflandırıcı reddi) birbirini kontrol ediyor.

**Yapamadığım doğrulama:** ad-hoc PowerShell probu bu ortamın izin sınıflandırıcısı tarafından
**iki kez reddedildi** (hem round-1'in tablo anlık görüntüsü, hem de yalnızca `-split/-join`
ifadesini bir sabit metin üzerinde deneyen zararsız sürümü). Bu yüzden `scripts/residue:48`'deki
satır-sonu/sekme katlamasını **doğrudan ölçemedim**; yalnızca dolaylı kanıtım var (iki gerçek
residue koşumu başarıyla tablo üretti — ifade sözdizimsel olarak geçerli — ve ~2 KB'lik bir Teams
komut satırı çıktıda tek satır olarak basıldı). Bkz. F-14.

---

## Findings

### F-12 — Medium — Correctness / Edge cases
**Ölçüm penceresinde doğan yabancı bir kullanıcı süreci hâlâ koşumu kırmızıya çeviriyor: aynı
commit'te bir koşum FOUND, bir sonraki CLEAN.**

Evidence — arka arkaya iki `./scripts/residue` (full) koşumu, aynı HEAD:
```
after run 2: 369 processes, 2 survivor(s), 1 ignored; 41529 MB available (-454 MB vs baseline)
  survivor  23372  "C:\Program Files (x86)\Microsoft\EdgeWebView\…\msedgewebview2.exe" --type=renderer … MSTeams …
  survivor  35020  "…\msedgewebview2.exe" --type=renderer … MSTeams …
RESIDUE FOUND (full): …
```
sonraki koşum: `after run 2: 365 processes, 0 survivor(s), 0 ignored` → `RESIDUE CLEAN (full, 2 runs)`.
Üretici de aynı sınıfı kendi kaydında yazmış (`specs/plans/0003-review.md:489-491`: fast profil iki
kez kırmızı, bir Chrome renderer'ı). Yani üç gözlem, iki profil, iki oturum.

Impact — Spec'in Intent paragrafı (`specs/active/0003-residue-noise.md:15-20`) bu işin varlık
sebebini "aynı commit'in bir koşumda geçip birinde düşmesi" ve ondan doğan "bir daha koştur"
alışkanlığı olarak tanımlıyor; meşgul bir Windows masaüstünde bu semptom **aynen duruyor**, yalnız
sebebi değişti (arama/servis süreçleri yerine kullanıcı oturumundaki uygulamaların çocukları).
CB-1'in sözü ("çıkış kodunu yalnızca **check'in başlatmış olabileceği** süreçler belirler") ile
uygulanan ölçüt arasında da bir aralık var: bir Teams renderer'ı check'in başlatmış olabileceği bir
şey değil, ama soy zinciri bir OS köküne inmediği için `counted`. Plan R-3 bu maliyeti yalnızca
"soyu **yürünemeyen**" süreç için kabul ediyor (`specs/plans/0003-plan.md:55-58`); bu vaka soyu
yürünebilen ama OS kökü olmayan üçüncü kategori ve hiçbir yerde yazılı değil.

Recommended action — bu dalda kod değişikliği **önermiyorum** (fail-closed doğru taraf). Üç adım:
(a) `docs/testing.md` Resource hygiene rule 2'ye tek cümle: bellek gibi süreç yarısının da boşta
bir makine istediği, ölçüm penceresinde doğan yabancı bir sürecin bilinçli olarak sayıldığı;
`docs/commands.md`'deki "Common mistake"e aynı uyarı. (b) VERIFY'ın PB-5 kanıtı yalnız temiz
koşumları değil, kırmızı koşumları da yazsın — "CLEAN" bu makinenin o anki durumu, betiğin bir
özelliği değil. (c) Yanlış kırmızı oranı kabul edilemez bulunursa ayrı bir CR (ör. ölçütü "check'in
pid alt ağacı + OS kökleri" ile genişletmek); bu spec'in kapsamına sokulmamalı.

---

### F-13 — Medium-low — Correctness / Edge cases
**F-1'in POSIX yarısı yarım kapandı: devam satırı bir sayıyla başlayan sarılmış komut satırı hâlâ
hayalet survivor üretiyor.**

`scripts/residue:67` yalnız `$1`'in sayısal olmasını arıyor; POSIX dalında (`:60-62`) devam satırı
`"<ilk sözcük>\t<ikinci sözcük>\t<satırın tamamı>"` olarak yazılıyor, yani ilk sözcük rakamsa
süzgeçten geçiyor. Windows dalı katlandığı için (`:48`) oradan etkilenmiyor — asimetri burada.

Evidence — sahte `ps`'e `"  4242 and the rest of the wrapped command line"` satırı koyup aynı
zorlanmış-POSIX koşumunu yaptım:
```
after run 1: 4 processes, 1 survivor(s), 0 ignored
  survivor  4242    4242 and the rest of the wrapped command line
RESIDUE FOUND (fast): …
```
Selftest'teki yeni senaryo (`scripts/selftest:131`) devam satırını `"  and a second line …"` diye
kurduğu için tam bu varyantı kaçırıyor.

Impact — F-1'in sınıfı (metin parçası = süreç) POSIX'te açık kalıyor. Pratik olasılık düşük (argv
içinde satır sonu + devamının rakamla başlaması), ama düzeltme bir karakterlik.

Recommended action — süzgeci iki alana genişletin: `scripts/residue:67` →
`awk -F'\t' '$1 ~ /^[0-9]+$/ && $2 ~ /^[0-9]+$/'` (gerçek `ps`/`Win32_Process` çıktısında ppid her
zaman sayı, hiçbir gerçek süreç düşmez); isteğe bağlı olarak aynı kontrol
`scripts/lib/classify-survivors:44-45`'te. Sahte `ps` tablosundaki devam satırını rakamla başlayan
biçime çevirin ya da ikincisini ekleyin.

---

### F-14 — Medium-low — Tests
**F-1'in vahşi doğada **gerçekten gözlenmiş** yarısı (Windows ölçümü) hâlâ tek bir otomatik testle
bile korunmuyor.**

Round 1'in kanıtı Windows'taydı (canlı tabloda 360 satırın 21'i/44'ü hayalet). Düzeltmenin o
yarısı `scripts/residue:48`'deki katlama; onu iddia eden hiçbir senaryo yok. `scripts/selftest`'in
sarılmış-satır senaryosu (`:131`) POSIX dalında koşuyor ve bu makinede `skip` ediliyor
(`== selftest: … 1 skipped ==`), CI de yalnız Linux (`.github/workflows/check.yml:47,61-64`).
Round-1 raporu bu boşluğu zaten işaretlemişti ("Windows ölçüm dalının hiçbir otomatik testi yok —
tam da bu boşluk F-1'in fark edilmemesine yol açtı", `specs/plans/0003-review.md:381-384`); fix
turu boşluğu kapatmadı.

Impact — AGENTS.md kural 4 anlamında zayıf: düzeltmenin en çok kanıta dayanan parçası yalnızca
"bu makinede yeşil gördüm" ile destekleniyor. Katlama ifadesi bir gün bozulursa Windows'ta kimse
görmez; CI hiç görmez. (Ben de doğrulayamadım: PowerShell probu reddedildi, yukarı bkz.)

Recommended action — kod değişikliği şart değil, kanıt kaydı şart: (a) planın criterion↔test
haritasında PB-5 satırına "Windows ölçümünün satır katlaması yalnız gerçek koşumla kanıtlanır"
notu; (b) VERIFY round-1'in yeniden üretim komutunu (`specs/plans/0003-review.md:44-58`) bu
makinede tekrarlayıp hayalet satır sayısının 0 olduğunu kanıt tablosuna yazsın. Daha güçlü
alternatif: katlamayı `measure` dışına, sentetik girdiyle sınanabilir bir yere taşımak — bu spec'in
değdiği değeri aşar, önermiyorum.

---

### F-15 — Low — Tests
**Yeni bellek `skip`'i, sınanan betiğin kendi çıktısına bakarak karar veriyor; ve PB-1'in ikinci
yarısı ("ölçülemiyor" notu korunur) hiçbir yerde iddia edilmiyor.**

`scripts/selftest:105-109`:
```sh
if printf '%s\n' "$out" | grep -q 'memory is not measurable'; then
  skip "residue: memory line (not measurable on this platform)"
else
  matches 'MB available \(-?[0-9]+ MB vs baseline\)' …
fi
```
Dal, `scripts/residue:81`'in bastığı notla seçiliyor. Bellek ölçümü bozulursa (ör. Windows dalında
`MEM` ayrıştırması, `scripts/residue:50`) betik notu basar, selftest **kırmızı değil skip** verir —
başarısız olması gereken bir iddia sessizce kaybolur. İkincisi: spec PB-1
(`specs/active/0003-residue-noise.md:47-49`) notun korunmasını açıkça istiyor; `grep -q` yalnız
`if` koşulunda kullanılıyor, `report` edilmiyor, yani not hiçbir senaryoda iddia edilmiyor
(`grep -n "not measurable" scripts/selftest` → yalnız :105).

Impact — Küçük ama AGENTS.md kural 5'in ruhuna değiyor (skip, kırmızının yerini alabiliyor) ve
PB-1'in bir yarısı kanıtsız. Bu makinede dal `else`'e düştü (`ok residue: the run line reports
memory against the baseline`), yani bugün maskelenen bir şey yok.

Recommended action — dalı dış bir olguyla seçin (`[ -r /proc/meminfo ] || command -v vm_stat ||
[ windows ]`), ve "ölçülemiyor" dalında skip yerine gerçek bir iddia koyun:
`matches '^note: memory is not measurable on this platform; processes only$'` — senaryo o
platformda da koşabiliyor, yalnızca diğer dalı iddia ediyor. Harita satırındaki "atlanır" ifadesi
de buna göre güncellenir.

---

### F-16 — Low — Plan conformance (R-07)
**Değişen dosya sayısı planın listesini bir dosya aşıyor: `specs/plans/0003-review.md`.**

`git diff --name-only main..HEAD` → 10 dosya; planın "Files to change or add" listesi
(`specs/plans/0003-plan.md:9-24`) 9 dosya sayıyor ve review raporunu içermiyor. Round 1'de liste
birebir uyuyordu; fix turunda `c4413dc` ve `70c599f` ile review dosyası da diff'e girdi.

Impact — Süreç kaydı, kusur değil: review raporu zaten segmentin zorunlu çıktısı
(`workflows/segments.md:34`). Ama ekip tam bu durum için bir hafta önce bir not düşmüş
(`specs/plans/0003-plan.md:6-7`, spec dosyasının listeye eklenmesi); aynı titizliğin burada da
uygulanması tutarlılık meselesi.

Recommended action — planın dosya listesine `specs/plans/0003-review.md` satırını eklemek yerine,
onay satırının altındaki mevcut "Onay sonrası değişiklik" notunu bir cümleyle genişletin (review
raporu REVIEW segmentinin çıktısı olarak diff'e girer). Alternatif: bunu "drift değil" diye
triyajda noise işaretlemek — ben kaydı tercih ediyorum.

---

### F-17 — Low — Maintainability / Docs
**`skip()`'in açıklaması ile çağrıldığı yerler uyuşmuyor: üç çağrının ikisi platformla değil, depo
şekliyle ilgili.**

`scripts/selftest:23` — `# a scenario that cannot run on this platform`; `docs/commands.md:117-119`
— "A skipped scenario is one this platform cannot run (the POSIX measurement on Windows, for
instance)". Oysa `scripts/selftest:305` ve `:313` "no adapters/ in this repo" diyor — bu bir
platform değil, çalışma alanı şekli (ANEW şablonunda adapters yoksa tetiklenir; bu depoda
tetiklenmiyor, bu yüzden bu makinede skipped=1).

Impact — Yeni yazılmış bir cümle, ilk günden kendi çağrı yerlerini yanlış anlatıyor; F-6'da
düzeltilen hatanın (yorum ≠ davranış) aynı sınıfı.

Recommended action — her iki yerde "this platform" → "this platform or this workspace" (ör.
"bu koşumun kuramadığı senaryo: platform ya da depo şekli").

---

### F-18 — Info — Docs
**F-8'in kanıtının ikinci yarısı (aracın kendi ölçümünün COM etkinleştirmesi) yazıya geçmedi.**

`docs/testing.md:90-93` yalnız "check" öznesiyle konuşuyor: "Nothing check runs here activates a
long-lived COM object". Round-1 F-8'in kanıtı buna ek olarak `WmiPrvSE.exe`'nin **residue'nun kendi
ölçümü** (`scripts/residue:43`, `Get-CimInstance`) tarafından doğduğunu ve artık sınıflandırıcı
tarafından da affedildiğini söylüyordu (`specs/plans/0003-review.md:254-256`). Cümle yazıldığı
hâliyle **yanlış değil**, eksik.

Kendi koşumumda kör noktanın kuramsal olmadığını gördüm: full profilin 1. koşumunda ölçüm
penceresinde `19748  C:\Windows\System32\RuntimeBroker.exe -Embedding  (OS service)` belirdi ve
sessizce ignored'a düştü — yani eklenen cümle isabetli, sadece yarım.

Recommended action — isteğe bağlı yarım cümle: "…— ölçümün kendi WMI/COM yardımcıları dâhil".
Kod değişikliği yok.

---

### F-19 — Info — Docs / Contract
**Yardımcının yeni iki `exit 2` yolu, residue'nun "2 = usage" sözleşmesini biraz daha az doğru
kılıyor.**

`scripts/lib/classify-survivors:31` (boş tablo) ve `:46,66` (bozuk survivor satırı) exit 2 veriyor;
`scripts/residue:103-104` bunu `residue: cannot classify survivors` + exit 2 olarak yüzeye
çıkarıyor. Oysa `scripts/residue:7` ve `docs/commands.md:102` ("Stops at" yalnız 0 ve 1'i,
"Refusal" yalnız ABORTED'ı anıyor) 2'yi "usage" diye tarif ediyor. Her iki yol bugün residue
üzerinden **erişilemez** (tablo `measure`'ın `[ -s "$1" ]` garantisiyle dolu, survivor satırları
`:67`'de süzülüyor) — ölçtüm: süzgeci kaldırınca gerçekten `rc=2` + "cannot classify survivors"
çıkıyor, yani yol canlı.

Impact — Yok denecek kadar az; yalnız dokümanla betik arasındaki küçük bir aralık (CB-4'ün
"ikisi aynı şeyi söyler" iddiası).

Recommended action — `docs/commands.md`'nin `scripts/residue` "Stops at" satırına bir ek cümle:
"exit 2 = kullanım hatası ya da güvenilemeyen bir ölçüm (`residue: cannot list processes…`,
`residue: cannot classify survivors`)".

---

## Soru soru cevaplar

**1. Her düzeltme bulgusunu gerçekten kapatıyor mu?**
F-3, F-4, F-5, F-6, F-7, F-9, F-10 **tam kapandı** (kanıtlar aşağıdaki özetlerde). F-2 **özünde
kapandı** (biçim iddiası gerçekten koşuyor ve geçiyor; `ANEW_RESIDUE_MB=x → 2` var; harita satırı
artık var olmayan bir teste işaret etmiyor) ama bir artığı var: F-15. F-8 kapandı, yarım kalan
kanıt için F-18. F-1 **kısmen**: Windows yarısı için makul bir düzeltme var ama testi yok (F-14),
POSIX yarısının bir varyantı hâlâ açık (F-13).

**2. Regresyon / yeni kenar durum?**
- Sayısal-pid süzgeci (`scripts/residue:67`) **gerçek bir süreci düşürmüyor**: POSIX'te ilk awk
  (`:60-62`) `$1`'i `ps -o pid=`'ten alıyor, Windows'ta `ProcessId` — ikisi de her zaman sayı.
  Zorlanmış-POSIX koşumunda tablo 3→4 satır, hiçbir gerçek süreç kaybolmadı. Tek kusuru eksik
  sıkılık (F-13). Küçük not: `awk … > "$TMP/rows" && mv` — awk başarısız olursa süzgeç sessizce
  atlanır; "defence in depth" olduğu için kabul edilebilir.
- Sınıflandırıcının bozuk satırda `exit 2`'si: residue bunu `exit 2` + "cannot classify survivors"
  diye yüzeye çıkarıyor. **Doğru sonuç** — sessizce saymak ya da yok saymak ikisi de yanlış olurdu,
  ve yol bugün residue'dan erişilemez (süzgeç önce davranıyor). Tek pürüz sözleşme metni (F-19).
  Ayrıca awk, bozuk satırdan önce üretilmiş `counted/ignored` satırlarını stdout'a yazmış oluyor;
  residue o dosyayı kullanmadan çıktığı için zararsız.
- `-s` boş tablo reddi: residue'nun geçtiği tablo `measure`'ın `[ -s "$1" ]` garantisiyle hep dolu;
  `[ -r ]` kontrolü önce geldiği için var olmayan dosyanın mesajı da değişmedi (selftest'te ikisi
  de ayrı ayrı yeşil). Regresyon görmedim.
- Bu turda hiçbir iddia zayıflatılmadı (AGENTS.md kural 5): F-4 ve F-5 `has` → satır-çapalı
  `matches`/`grep '^  survivor  '` ile **sıkılaştırma**; senaryo sayısı 101 → 107.

**3. Yeni/değişen selftest iddiaları gerçek davranışı mı iddia ediyor, POSIX-only olanlar gerçek
biçimle uyuşuyor mu?** Evet — yukarıdaki zorlanmış-POSIX koşumuyla dördünü de gerçek çıktıya karşı
doğruladım (`^ +777 +\[kworker/R-selftest\] +\(kernel thread\)$`, `after run 2: … 1 ignored`,
`hasnt "a second line…"`, `survivor  888 …`). Bellek iddiası (`MB available \(-?[0-9]+ MB vs
baseline\)`) bu makinedeki gerçek çıktıyla eşleşti: `41958 MB available (0 MB vs baseline)`. Hepsi
durum kodu değil davranış iddia ediyor. Tek yapısal itiraz F-15.

**4. Plan conformance:** F-16 dışında temiz. Her real bulgu kendi commit'inde, `[review 0003/F-n]`
referanslı (`prompts/build.md §fixes`), hiçbiri ilgisiz dosyaya dokunmamış (commit başına
`--stat` ile kontrol ettim). `scripts/doctor`, `workflows/bootstrap.md` diffte yok (PB-6).

**5. Plan/spec/doküman metinleri doğru mu?** PB-1 harita satırı
(`specs/plans/0003-plan.md:94`) artık **doğru**: `… MB vs baseline` iddiası gerçekten var
(`scripts/selftest:108`, bu makinede `ok`), eşik dalının testi gerçekten yok
(`grep -n "over the" scripts/selftest` → yalnız yorum satırı). PB-4 satırı doğru
(`ANEW_RESIDUE_MB=x` senaryosu `:112-113`). `docs/testing.md` rule 2'nin yeni cümlesi ölçütün
davranışını doğru anlatıyor (F-18 eksiklik, yanlışlık değil). `docs/commands.md`'nin F-7 cümlesi
doğru; F-9 cümlesi F-17'de yazdığım kadarıyla eksik. R-5 notu ve onay-sonrası dosya listesi notu
round-1 raporundaki ifadeyle uyumlu.

**6. Hâlâ açık olanlar:** round-1'in "Windows ölçüm dalı sınanmıyor" uyarısı (F-14), F-11 (macOS /
pid 1 — triyajda noise, değişmedi; `docs/testing.md:83` hâlâ "POSIX" diyor). Fix turunun
yakalaması gerekip yakalamadığı şey: F-13 (kendi düzeltmesinin POSIX varyantı) ve F-15 (kendi
eklediği skip'in sınanan çıktıya bağlı olması).

## Dimension özeti

- **Correctness:** F-12 (orta), F-13. CB-2/CB-3/CB-4 ve PB-2/PB-3/PB-4/PB-6 bu turda temiz.
- **Security:** clean. Yeni kod yok sayılabilir; F-7'nin dokümantasyon düzeltmesi yerinde.
  `docs/security.md` tehdit modeline aykırı bir şey eklenmedi; depoya çıktı yazılmıyor.
- **Edge cases:** F-13, F-19; boş tablo ve bozuk satır yolları artık kapalı ve sınanıyor.
- **Performance:** clean — eklenen iş ölçüm başına bir awk geçişi; `--fast` 2 koşum ~50 s,
  round 1'deki ölçümle aynı mertebe.
- **Tests:** F-14, F-15; gerisi sıkılaştı (101 → 107, hiçbir iddia zayıflamadı).
- **Maintainability:** F-17; ölü kod kalmadı (F-6 kapandı), mod biti düzeldi (F-10).
- **Plan conformance:** F-16.

## Verdict

Fix turu, round 1'in on real bulgusunun hepsine gerçek ve dar bir karşılık vermiş; yedisi tam,
üçünde artık var (F-13/F-14 → F-1, F-15 → F-2, F-18 → F-8). Yeni regresyon bulamadım; sayısal-pid
süzgeci gerçek süreç düşürmüyor, classifier'ın `exit 2`'si doğru yere çıkıyor, `-s` reddi residue'yu
etkilemiyor. Triyaja giden asıl yeni şey **F-12**: ölçüt, spec'in ortadan kaldırmak için yazıldığı
"aynı commit, bir kırmızı bir yeşil" semptomunu meşgul bir Windows masaüstünde kaldırmıyor —
bunu bu turda birebir gözledim ve üreticinin kendi kaydı da iki kez aynı şeyi söylüyor. Kod
düzeltmesi değil, dürüst bir kayıt (ve gerekirse ayrı bir CR) öneriyorum.

**STOP — segment burada bitiyor.**
Next: TRIAGE — human (real / noise / investigate); sonra Developer fix rounds, sonra VERIFY.

---

## Triage — round 2

Triyaj: MuaddibL, 2026-11-04. 8 real, 0 noise, 0 investigate — investigate yok, çünkü sekiz
bulgunun da kanıtı raporda duruyor (yeniden üretim komutu ya da dosya referansı); R-05'e gidecek
belirsiz bir gözlem kalmadı. Bu turda tek kod değişikliği F-13'ün bir koşulu; gerisi test dalı,
doküman ve plan kaydı.

| # | Severity | Dimension | Verdict | Karar / gerekçe |
|---|---|---|---|---|
| F-12 | Medium | Correctness | **real — yalnız (a) ve (b)** | Gözlem doğru, üreticinin kendi kaydı da aynısını söylüyor. Ölçüt yanlış tarafta değil (fail-closed); bir Teams renderer'ını affetmenin tek yolu soy ölçütünden vazgeçmek. Yapılacak şey kod değil dürüst kayıt: `docs/testing.md` rule 2 + `docs/commands.md`. **(c) açılmıyor:** asıl ağrı CI'daydı (Linux, boş runner) ve orada çözüldü; masaüstündeki yanlış kırmızı oranı rahatsız ederse ayrı CR. Spec değişmiyor — CB-1 zaten ölçütü plana bırakıyor. |
| F-13 | Medium-low | Correctness | **real** | F-1'in POSIX yarısının açık varyantı, birebir üretildi. `$2 ~ /^[0-9]+$/` eklenir; gerçek `ps`/`Win32_Process` çıktısında ppid her zaman sayı, hiçbir gerçek süreç düşmez. Sahte tabloya rakamla başlayan devam satırı eklenir. |
| F-14 | Medium-low | Tests | **real (kayıt olarak)** | Katlamayı sentetikleştirmek bu spec'in değerini aşar (reviewer da önermiyor). Yapılacak: PB-5 satırına kanıtın niteliği ("yalnız gerçek koşumla"), ve üreticinin bu makinede PowerShell probunu çalıştıramadığının kaydı; gözlem VERIFY'a kalır. |
| F-15 | Low | Tests | **real** | Sınanan betiğin kendi çıktısına bakarak hangi iddianın koşacağına karar vermek yanlış yön: bozulma kırmızı yerine skip üretebilir. Dal dış olguyla seçilir, "ölçülemiyor" dalında da gerçek iddia konur. |
| F-16 | Low | Plan conformance | **real (kayıt)** | Gerçek drift değil — review raporu segmentin zorunlu çıktısı — ama onay satırının altında zaten aynı türden bir not var; tutarlılık için bir cümle. Triyajda en savunulabilir "noise" adayı buydu, kayıt tercih edildi. |
| F-17 | Low | Maintainability | **real** | F-6'da düzeltilen hatanın aynısı: yeni yazılan cümle kendi çağrı yerlerini yanlış anlatıyor. |
| F-18 | Info | Docs | **real** | F-8'in cümlesi yanlış değil, yarım: aracın kendi WMI/COM yardımcıları da aynı affın içinde. |
| F-19 | Info | Docs / Contract | **real** | CB-4 "doküman ve betik aynı şeyi söyler" diyor; exit 2'nin iki yeni anlamı var, doküman hâlâ yalnız "usage" diyor. |

### Fix round 2 — sıra
F-13 (kod) → F-15 (test) → F-17 → F-12a → F-18 → F-19 (dokümanlar) → F-14 → F-16 (plan kayıtları).
Her real bulgu kendi commit'inde, `[review 0003/F-n]` referansıyla; her commit sonrası
`./scripts/check --fast`, tur sonunda tam yeşil + `scripts/selftest` + iki residue profili — bu kez
kırmızı koşumlar da kayda geçer (F-12b). Sonra fix diff'i yeniden REVIEW'a gider.

### Fix round 2 — sonuç (2026-11-04)

| # | Commit | Ne değişti |
|---|---|---|
| F-13 | `5c098f2` | Süzgeç ppid'nin de sayı olmasını arıyor (`scripts/residue`), sınıflandırıcı ebeveyn haritasını aynı kuralla kuruyor; sahte tabloya rakamla başlayan ikinci sarılmış satır + `hasnt` |
| F-15 | `b0ea784` | Bellek dalını platform seçiyor (sınanan çıktı değil); "ölçülemiyor" dalında skip yerine `note: memory is not measurable…` iddiası; PB-1 satırı güncellendi |
| F-17 | `a946876` | `skip()` yorumu ve `docs/commands.md`: "platform **ya da çalışma alanı**" |
| F-12 | `520b033` | `docs/testing.md` rule 2 + `docs/commands.md`: süreç yarısı da boşta makine ister; ölçüm penceresinde doğan yabancı çocuk bilinçli olarak sayılır, cevabı daha sessiz makine — kural genişletmek değil. **Kod değişikliği yok** (F-12c ayrı CR'a bırakıldı) |
| F-18 | `523a79d` | Ölçümün kendi WMI host'u da aynı affın içinde — yarım cümle |
| F-19 | `33d085f` | exit 2'nin iki yeni anlamı hem betik başlığında hem `docs/commands.md`'de |
| F-14 | `b357515` | PB-5 satırı: Windows katlamasının sentetik testi yok, kanıt gerçek koşum; ad-hoc PowerShell probunun bu ortamda hem üretici hem reviewer tarafından çalıştırılamadığı kayda geçti |
| F-16 | `7dc81a3` | Onay sonrası notu: review raporu REVIEW segmentinin çıktısı, plan dosya listesine ait değil |

Doğrulama (tur bitiminde, bu makinede): `./scripts/check` → `CHECK GREEN (full, 6 steps, 8 s)` ·
`./scripts/doctor --strict` → `0 fail, 0 warn` · `./scripts/selftest` → `107 passed, 0 failed, 1 skipped`.

Residue — **kırmızı koşumlar dâhil** (F-12b):

| Koşum | Sonuç |
|---|---|
| `./scripts/residue` (1) | `RESIDUE FOUND (full)` — 1 survivor: Chrome Beta renderer, `after run 2: 378 processes, 1 survivor(s), 2 ignored` |
| `./scripts/residue` (2) | `RESIDUE FOUND (full)` — 1 survivor: yine bir Chrome Beta renderer |
| `./scripts/residue --fast` | `RESIDUE CLEAN (fast, 2 runs)` — ilk denemede |
| `./scripts/residue` (3) | `RESIDUE CLEAN (full, 2 runs)` |

İki kırmızı koşumun ikisinde de tek survivor, ölçüm sırasında tarayıcının başlattığı bir renderer'dı
— F-12'nin tam olarak belgelediği durum, ölçütün doğru (fail-closed) davranışı. Bu tablo spec'in
PB-5 kanıtına ve PR açıklamasına bu hâliyle girer: "CLEAN" makinenin o anki durumudur, betiğin
özelliği değil.

F-13'ün düzeltmesi ayrıca zorlanmış-POSIX koşumuyla doğrulandı (scratchpad'de sahte `ps` + sahte
`uname`, depoya dokunmadan): düzeltmeyle `RESIDUE CLEAN`, `1543720` (= `5c098f2^`) öncesi
residue ile aynı tablo `survivor  4242  4242 and the rest of a wrapped command line` + exit 1
veriyor. Sızıntı yarısı (`FAKEPS_LEAK=1`) hâlâ exit 1 + `survivor  888`.

**Sıradaki: REVIEW round 3** — fix diff'i (`1543720..HEAD`) bağımsız incelemeye gider.

---

## REVIEW round 3 — 2026-11-04

- Round 3: 2026-11-04, `reviewer` subagent, ayrı salt-okunur oturum (AGENTS.md kural 3)
- Diff: `git diff 1543720..HEAD` — 7 dosya, 85+/24−, 9 commit (fix round 2'nin tamamı)
- Kapsam notu: F-12c (ölçütü check'in pid alt ağacıyla genişletmek) bilinçli olarak kapsam
  dışı, ayrı CR'a bırakıldı — reviewer'a da böyle bildirildi.

Rapor aşağıda **olduğu gibi** kayıtlı: yumuşatılmadı, yeniden sıralanmadı, yorum eklenmedi.

### Çalıştırılan doğrulamalar (reviewer, bu makinede, Windows/MINGW)

| Komut | Sonuç |
|---|---|
| `./scripts/check` | `CHECK GREEN (full, 6 steps, 8 s)` — exit 0 |
| `./scripts/doctor --strict` | `== result: 0 fail, 0 warn ==` — exit 0 |
| `./scripts/selftest` | `== selftest: 107 passed, 0 failed, 1 skipped ==` — exit 0 |
| `./scripts/residue --fast` | `RESIDUE FOUND (fast)` — 1 survivor: Chrome Beta renderer (aşağıda gözlem) |
| `./scripts/residue` (full) | `RESIDUE FOUND (full)` — 1 survivor: Chrome Beta renderer (pid 34760, iki koşumda da aynı) |
| `git ls-files -s scripts/` | `100755` hepsi, `scripts/lib/classify-survivors` dâhil (F-10 hâlâ kapalı) |
| `git diff --name-only 1543720..HEAD` | 7 dosya; `main..HEAD` 10 dosya |

Üreticinin tur sonu iddiaları (`check` yeşil, `doctor` 0 fail, `selftest` 107/0/1) **birebir doğrulandı**.

Bu turda, önceki iki turda izin sınıflandırıcısının reddettiği PowerShell probu **çalıştı**; onunla iki ölçüm yapıldı:

- `@(Get-CimInstance Win32_Process).Count` = 380, bunların `ParentProcessId`'si sayı olmayan **0** tanesi → `scripts/residue:68`'deki yeni `$2 ~ /^[0-9]+$/` süzgeci bu makinede **tek bir gerçek süreci bile düşürmüyor** (F-13 düzeltmesinin regresyon riski ölçülerek elendi).
- `scripts/residue:49`'daki katlama ifadesi sentetik bir metinle sınandı: `"prog.exe --a=1`r`n# marker`tand more"` → `prog.exe --a=1 # marker and more`, sonuçta `[\r\n\t]` yok. İfade doğru (F-14'ün doğrudan ölçülemeyen yarısı — bkz. F-24).
- Şu an canlı tabloda gömülü satır sonu/sekme taşıyan komut satırı yok (0 süreç), yani round-1'in vahşi doğa gözlemi bu turda yeniden üretilemedi.

POSIX dalı bu makinede koşmuyor (`skip`); zorlanmış-POSIX koşumu için dosya yazmak gerekirdi, bunun yerine `scripts/residue:61-68`'in boru hattı birebir elle çalıştırıldı:

```sh
printf '%s\n' "    1     0 /sbin/init" "    2     0 [kthreadd]" "  100     1 /bin/sh scripts/check" \
  "  and a second line of the previous command" "  4242 and the rest of a wrapped command line" |
awk '{ pid=$1; parent=$2; sub(/^[ \t]*[0-9]+[ \t]+[0-9]+[ \t]+/,"")
       if ($0 !~ /^ps -e -o pid= -o ppid= -o args=/) print pid "\t" parent "\t" $0 }' |
awk -F'\t' '$1 ~ /^[0-9]+$/ && $2 ~ /^[0-9]+$/'
```
→ yalnız `1`, `2`, `100` kalıyor; **her iki sarılmış satır da düşüyor** (F-13 kapandı).

### 1. Round-2 bulgularının kapanış durumu

| # | Durum | Kanıt |
|---|---|---|
| F-12 (a+b) | **tam kapandı** (kapsamdaki haliyle) | `docs/testing.md:95-99` ve `docs/commands.md:111-115` süreç yarısının da boşta makine istediğini, pencerede doğan yabancı çocuğun bilinçli olarak sayıldığını yazıyor; kırmızı koşumlar `specs/plans/0003-review.md:876-888`'de kayda geçmiş. Kod değişikliği yok — doğru. (F-12c kapsam dışı, ayrı CR.) Yalnız ifade üzerine bir çekince var: F-22. |
| F-13 | **özünde kapandı, artığı var** | `scripts/residue:68` iki alanı da sayı istiyor (yukarıdaki yeniden üretim); `scripts/selftest:137,158` rakamla başlayan sarılmış satır + `hasnt`. Artık: sınıflandırıcı yarısı (`classify-survivors:44`) sınanmıyor ve simetrik durum açık → **F-20**. |
| F-14 | **tam kapandı (kayıt olarak)** | `specs/plans/0003-plan.md:101` Windows katlamasının sentetik testi olmadığını ve kanıtın yalnız gerçek koşum olduğunu yazıyor. Kayıt artık bir parça eskidi → **F-24** (Info). |
| F-15 | **özünde kapandı, artığı var** | `scripts/selftest:108-116`: dal `uname`/`/proc/meminfo`/`vm_stat` ile seçiliyor, sınanan çıktıyla değil; "ölçülemiyor" dalında skip yerine gerçek iddia var; `plan:97` güncellendi. Artık: o dal **desteklenen hiçbir platformda koşmuyor** → **F-21**. |
| F-16 | **tam kapandı** | `specs/plans/0003-plan.md:6-10` review raporunun neden diffte olduğunu yazıyor; `git diff --name-only main..HEAD` 10 dosya = planın 9 dosyası + açıklanmış review raporu. |
| F-17 | **tam kapandı** | `scripts/selftest:5-7,24` ve `docs/commands.md:123-125` "bu platform **ya da** bu çalışma alanı" diyor; üç `skip` çağrısının gerçekten ikisi depo şekliyle ilgili (`scripts/selftest:127,315,323`) — cümle artık çağrı yerlerini doğru anlatıyor. |
| F-18 | **tam kapandı** | `docs/testing.md:92-93`: "…and is ignored — the WMI host the measurement itself activates included". |
| F-19 | **tam kapandı** | `docs/commands.md:104-106` ve `scripts/residue:7-8` exit 2'nin iki anlamını aynı sözcüklerle söylüyor; her iki hata metni de betikte birebir var (`scripts/residue:72,105`). CB-4'ün "doküman ve betik aynı şeyi söyler" iddiası bu noktada tutuyor. |

### 2. Regresyon taraması

Regresyon **bulunmadı**. Tek tek bakıldı:

- **Daha sıkı süzgeç gerçek süreç düşürmüyor**: Windows'ta ölçüldü (380 sürecin 0'ında sayı olmayan ppid); POSIX'te `ps -o ppid=` her zaman sayı veriyor ve yukarıdaki boru hattı yeniden üretiminde üç gerçek satırın üçü de kaldı.
- **`classify-survivors:44`'ün yeni koşulu residue üzerinden davranış değiştirmiyor**: residue'nun verdiği tablo (`$TMP/again`) zaten `measure`'ın süzgecinden geçmiş durumda, yani tüm satırlarda $1 ve $2 sayı. Yön güvenli: eksik ebeveyn satırı = soy daha erken kırılır = `counted` (fail-closed).
- **Round-1 düzeltmeleri yerinde**: boş tablo reddi (`/dev/null` ile denendi → `empty process table`, rc=2), bozuk survivor satırı reddi (→ `malformed survivor line`, rc=2), mod biti `100755`, ölü `sub()` yok.
- **Hiçbir iddia zayıflatılmadı** (AGENTS.md kural 5): diffte silinen tek şey `skip` dalı, yerine gerçek bir `matches` geldi; bir `hasnt` eklendi. Windows'ta sayım 107 passed / 1 skipped — round 2 ile aynı, çünkü eklenen iddia POSIX dalında.
- **Commit hijyeni temiz**: dokuz commit'in her biri yalnız kendi bulgusunun dosyalarına dokunuyor (`git log --stat 1543720..HEAD`), hepsi Conventional Commits + `[review 0003/F-n]`; handoff commit'i `[review 0003]`.
- **PB-6**: `scripts/doctor`, `workflows/bootstrap.md`, `.github/workflows/check.yml` bu turun diffinde yok; `doctor --strict` 0 fail.

Round-1'den kalıp round-2'nin dokunmadığı bir şey bulunmadı; F-11 (macOS / pid 1) triyajda noise işaretlenmişti ve `docs/testing.md:83` hâlâ "POSIX" diyor — karar gereği, bulgu değil.

### 3. Plan conformance (R-07) — clean

Round-2 diffinin 7 dosyasının 6'sı planın "Files to change or add" listesinde (`docs/commands.md`, `docs/testing.md`, `scripts/lib/classify-survivors`, `scripts/residue`, `scripts/selftest`, `specs/plans/0003-plan.md`); 7.'si `specs/plans/0003-review.md` ve artık planın onay-sonrası notuyla (`specs/plans/0003-plan.md:6-10`) açıklanmış durumda. Drift yok.

### Findings

#### F-20 — Low — Tests / Correctness
**F-13'ün sınıflandırıcı yarısı sınanmadan girdi, ve yardımcının kendi arayüzünde aynı sınıfın simetrik hâli hâlâ açık.**

Evidence — (a) `scripts/lib/classify-survivors:44` bu turda değişti (`$2 ~ /^[0-9]+$/` eklendi) ama onu iddia eden hiçbir senaryo yok: `scripts/selftest:188-229`'daki sentetik tabloların hiçbirinde ppid'si sayı olmayan bir **tablo** satırı yok; tek bozuk-satır senaryosu survivor tarafında (`:226-229`). (b) Survivor tarafındaki kontrol hâlâ yalnız `$1`'e bakıyor (`scripts/lib/classify-survivors:45`), yani pid'i rakamla başlayan sarılmış satır yardımcının kendi arayüzünde süreç sanılmaya devam ediyor:

```sh
printf '4242\tand\t4242 and the rest of a wrapped command line\n' | \
  sh scripts/lib/classify-survivors posix README.md
# → counted	4242	4242 and the rest of a wrapped command line   (rc=0)
```

Impact — `scripts/residue` üzerinden **erişilemez** (ölçüm süzgeci önce davranıyor) ve yön fail-closed, yani yanlış yeşil değil olsa olsa yanlış kırmızı. Ağırlığı iki yerde: (1) dosyanın kendi başlık sözleşmesi (`scripts/lib/classify-survivors:12-14`, "A survivor line whose pid is not a number is not a process… It is refused (exit 2), never guessed at") artık eksik — çünkü F-13 tam olarak "kayıp satır sonu **sayıyla da** başlayabilir" demekti; bu, F-6 ve F-17'de iki kez düzeltilen "yorum ≠ davranış" sınıfının üçüncüsü. (2) Plan adım 1 yardımcının ayrı dosya olma gerekçesini "sınıflandırma mantığı sentetik girdiyle sınanabilsin" diye yazıyor (`specs/plans/0003-plan.md:33-36`); bu turun sınıflandırıcı değişikliği o gerekçeyi kullanmadı.

Recommended action — tek satır + tek senaryo: `scripts/lib/classify-survivors:45`'i `$1 !~ /^[0-9]+$/ || $2 !~ /^[0-9]+$/` yapın (gerçek çağrıda ppid her zaman sayı — bu makinede 380/380 ölçüldü, hiçbir gerçek süreç düşmez), başlık cümlesini "pid'i ya da ppid'si sayı olmayan satır" diye düzeltin, ve `scripts/selftest:226` senaryosuna `"4242${T}and${T}4242 and the rest…"` satırını ekleyin (aynı `exits 2` iddiası kapsar). Alternatif (daha ucuz, savunulabilir): kod değişikliği yok, yalnız başlık cümlesini "residue bu satırları ölçümde süzer; yardımcı yalnız pid alanına bakar" diye dürüstleştirin. Birincisi öneriliyor: iki satır, davranış riski ölçülerek sıfırlandı.

#### F-21 — Low — Tests
**F-15'in "ölçülemiyor" dalı artık bir iddia taşıyor ama desteklenen iki platformun hiçbirinde koşmuyor; PB-1'in ikinci yarısı pratikte hâlâ kanıtsız.**

Evidence — `scripts/selftest:108-116`:
```sh
mem_readable=no
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) mem_readable=yes ;; esac
[ -r /proc/meminfo ] && mem_readable=yes
command -v vm_stat >/dev/null 2>&1 && mem_readable=yes
```
Windows'ta birinci satır, Linux CI'da ikinci satır her zaman `yes` yapıyor; `else` dalındaki `matches '^note: memory is not measurable on this platform; processes only$'` (`:115`) ne bu makinede ne CI'da (`.github/workflows/check.yml`, `ubuntu-latest`) koşabilir. Bu turda koşan iddia `ok residue: the run line reports memory against the baseline` (selftest çıktısı satır 44); `note:` iddiası hiç görünmüyor.

Impact — Küçük ama planın PB-1 satırı (`specs/plans/0003-plan.md:97`) "belleği okunamayan bir platformda **bunun yerine** `note: …` satırı iddia edilir" diyor; okuyan, o yarının bir yerde koştuğunu sanır. Gerçekte `scripts/residue:82`'nin notu hâlâ yalnız review okumasıyla korunuyor — F-2'nin kapatıldığı sanılan yarısının aynısı, bir seviye yukarı taşınmış hâli. F-15'in asıl derdi (bozulma skip değil kırmızı üretmeli) **çözüldü**; bu yalnız kanıt kaydı meselesi.

İkinci, daha ince nokta aynı satırda: Windows'ta `mem_readable=yes` sabit kabul ediliyor, oysa `scripts/residue:47`'nin `Win32_PerfFormattedData_PerfOS_Memory` sorgusu perf sayaçları bozuk/olmayan bir Windows host'unda boş dönebilir ve betik **doğru** davranıp notu basar; selftest o durumda kırmızı olur. Bu, F-15'in bilinçli tercihi ("ölçüm bozulursa kırmızı") ile PB-1'in "not korunur" güvencesi arasındaki ufak bir aralık; bugün gözlenmedi, aksiyon önerilmiyor, kayıt için yazıldı.

Recommended action — kod değişikliği önerilmiyor. PB-1 satırına yarım cümle: "bu dal desteklenen iki platformda da koşmaz (Windows ve Linux'ta bellek her zaman okunur); varlığı regresyona karşı, kanıtı review okumasıdır" — F-14'te aynı dürüstlükle yapılanın eşi.

#### F-22 — Low — Docs
**F-12'nin dokümantasyonu doğru ama bir yarısı eksik: spec'in "zararlı" dediği alışkanlığı, onu zararsız kılan tek korumayı yazmadan normalleştiriyor.**

Evidence — `docs/testing.md:99`: *"the answer is a quieter machine, not a wider rule. **On a desktop, expect to rerun.**"* ve `docs/commands.md:114`: *"**Rerun on a quieter machine.**"* Spec'in Intent paragrafı (`specs/active/0003-residue-noise.md:18-20`) ise bu işin varlık sebebini şöyle yazıyor: *"her PR'da 'bir daha koştur' alışkanlığı doğuyor; o alışkanlık, testin yakalamak için var olduğu **gerçek kalıntıyı da görünmez kılar**."*

Impact — İki metin aynı davranışı anlatıyor ama normatif dosya (`docs/testing.md` Resource hygiene, CB-4'ün yazdığı kural) okuyucuya kırmızıyı nasıl ayırt edeceğini söylemeden "yeniden koş" diyor. Oysa ayırt etmek bedava: betik her survivor'ı komut satırıyla adlandırıyor (`scripts/residue:125`) — bu turda bastığı satır `"C:\Program Files\Google\Chrome Beta\Application\chrome.exe" --type=renderer …` idi, bir bakışta check'in olmadığı belli. Koruma cümlesi olmadan kural, spec'in kaldırmak için yazıldığı refleksi yazıya geçirmiş oluyor.

Recommended action — her iki yerde tek yan cümle: "…önce adlandırılan survivor'ın komut satırını okuyun — `uv`/`pytest`/`python` görüyorsanız yeniden koşmak kalıntıyı gizler; tarayıcı/sohbet istemcisi görüyorsanız makine meşguldür." Kod değişikliği yok. (Reviewer'ın kendi notu: "Bunun en savunulabilir 'noise' adayı olduğunu kabul ediyorum: metin yanlış değil, eksik.")

#### F-23 — Info — Docs / Evidence
**Kalıcı review kaydındaki bir kanıt cümlesi yanlış commit'e işaret ediyor; yazıldığı hâliyle yeniden üretilemez.**

Evidence — `specs/plans/0003-review.md:890-893`: *"F-13'ün düzeltmesi ayrıca zorlanmış-POSIX koşumuyla doğrulandı …: düzeltmeyle `RESIDUE CLEAN`, **`b357515` öncesi residue** ile aynı tablo `survivor 4242 …` + exit 1 veriyor."* Oysa `b357515` planın F-14 notu, yalnız `specs/plans/0003-plan.md`'e dokunuyor ve F-13 düzeltmesinden **sonra** geliyor:
```sh
git show --stat --oneline b357515      # → specs/plans/0003-plan.md | 2 +-
git log --oneline 1543720..HEAD        # 5c098f2 (F-13) en eski, b357515 sondan ikinci
```
Yani "b357515 öncesi residue" zaten düzeltilmiş residue'dur ve `RESIDUE CLEAN` verir; cümlenin kastettiği referans `5c098f2^` = `1543720`.

Impact — Yok denecek kadar az, ama bu dosya VERIFY'ın okuyacağı kalıcı kanıt kaydı ve AGENTS.md kural 4 kanıtın kontrol edilebilir olmasını istiyor. Bir sonraki okuyan komutu tekrarlarsa karşıt sonuç alır.

Recommended action — cümledeki `b357515` → `1543720` (ya da `5c098f2^`). Tek sözcük.

#### F-24 — Info — Docs / Evidence
**PB-5 satırındaki "reviewer da doğrulayamadı" kaydı bu turda eskidi: ad-hoc PowerShell probu round 3'te çalıştı.**

Evidence — `specs/plans/0003-plan.md:101`: *"Üretici ad-hoc PowerShell probunu bu ortamda çalıştıramadı (izin sınıflandırıcısı reddetti); **reviewer da aynı nedenle doğrulayamadı** — VERIFY bunu kanıt tablosuna gözlem olarak yazar."* Bu turda prob çalıştı ve `scripts/residue:49`'un katlama ifadesi sentetik bir girdi üzerinde doğrulandı (yukarıdaki "Çalıştırılan doğrulamalar"): `"prog.exe --a=1`r`n# marker`tand more"` → `prog.exe --a=1 # marker and more`, sonuçta satır sonu/sekme yok. Ayrıca ölçüldü: şu anda bu makinede gömülü satır sonu taşıyan komut satırı yok (0/380), yani round-1'in vahşi gözlemi tekrarlanamadı; `ParentProcessId`'si sayı olmayan süreç de yok (0/380).

Impact — Yok; kanıtın niteliği hakkında. Katlama ifadesinin **kendisi** artık ölçülmüş durumda; sınanmayan şey yalnızca ifadenin `measure()` içinde uçtan uca doğru yerde durduğu (bu, gerçek koşumla kanıtlanıyor — iki residue koşumu tablo üretti).

Recommended action — VERIFY kanıt tablosuna bu iki ölçüm yazılsın; istenirse PB-5 satırındaki "reviewer da aynı nedenle doğrulayamadı" ifadesi "round 3'te ifade sentetik girdiyle doğrulandı, uçtan uca kanıt hâlâ gerçek koşum" diye güncellensin. Dosya listesi ve kapsam değişmez.

### Gözlem (bulgu değil, talimat gereği)

`./scripts/residue` ve `./scripts/residue --fast` bu turda **ikisi de ilk denemede kırmızı** bitti; her ikisinde de tek survivor ölçüm penceresinde doğan bir tarayıcı renderer'ıydı:

```
after run 1: 375 processes, 1 survivor(s), 0 ignored; 40923 MB available (-188 MB vs baseline)
  survivor  34760  "C:\Program Files\Google\Chrome Beta\Application\chrome.exe" --type=renderer … --renderer-client-id=1820 …
RESIDUE FOUND (full): stop what survived inside the step that starts it
```
(fast profilinde pid 42924, aynı aile.) Bu, `docs/testing.md:95-99`'un yeni yazdığı ve F-12'nin belgelediği durum; ölçütün fail-closed tarafı, kusur değil. Sayısal kayıt olarak: round 2'de 4 koşumun 2'si, bu turda 2 koşumun 2'si kırmızı. F-12c'yi (ölçütü check'in pid alt ağacıyla genişletmek) ayrı bir CR'a bırakma kararı için insana veri olsun diye yazıldı — kendi başına bir bulgu olarak **sunulmuyor**.

Ayrıca `ignored` listesi bu turda hiç dolmadı (`0 ignored`), yani gerçek koşum yine "ignore" yolunu çalıştırmadı — round 1'deki aynı sınırlama duruyor: CLEAN/FOUND sonucu ölçütün doğruluğunu değil regresyonsuzluğu gösteriyor; ölçütün kanıtı sentetik senaryolar.

### Dimension özeti

- **Correctness:** clean. F-13 residue tarafında kapandı (ölçülerek), F-12 kod değişikliği istemiyordu. Açık tek şey yardımcının kendi arayüzündeki simetri (F-20), erişilemez ve fail-closed.
- **Security:** clean. Yeni kod yok sayılabilir; `awk` programları sabit, veri `-v` ve dosya argümanıyla geçiyor, `eval` yok, depoya çıktı yazılmıyor. F-7'nin uyarı cümlesi yerinde duruyor ve bu turda eklenen "üçüncü yanlış" cümlesi onu zayıflatmıyor.
- **Edge cases:** clean. Boş tablo, bozuk satır, sarılmış satır (iki varyant), soy döngüsü, kendi ebeveyni — hepsi reddediliyor ya da `counted`.
- **Performance:** clean. Eklenen iş süzgece bir alan karşılaştırması; full profil ~70 s, round 1-2 ile aynı mertebe.
- **Tests:** F-20, F-21. Sayım 107 passed / 0 failed / 1 skipped; hiçbir iddia zayıflatılmadı, bir `hasnt` eklendi, bir `skip` gerçek iddiaya dönüştü.
- **Maintainability:** F-20'nin (1) numaralı yarısı (başlık yorumu). F-17 ile iki yer düzeldi, ölü kod yok, katman ihlali yok.
- **Plan conformance:** clean (R-07 ihlali yok).
- **Docs:** F-22, F-23, F-24 — hepsi düşük/bilgi; CB-4'ün "doküman ve betik aynı şeyi söyler" iddiası tutuyor.

### Verdict (reviewer)

Fix round 2, round 2'nin sekiz real bulgusunun **beşini tam** (F-12 kapsamdaki hâliyle, F-16, F-17, F-18, F-19), **ikisini özünde** (F-13, F-15) ve **birini kayıt olarak** (F-14) kapatmış. **Regresyon yok** — en riskli değişiklik olan daha sıkı ppid süzgeci bu makinede 380 süreç üzerinde ölçülerek elendi. Yeni bulguların hepsi Low/Info ve hiçbiri kodun davranışını bugün bozmuyor: ikisi kanıt kaydı (F-21, F-23/F-24), biri yarım kalan savunma katmanı + yanlış anlatan yorum (F-20), biri doküman tonu (F-22).

Reviewer'ın okumasıyla bu değişiklik seti **gönderilebilir durumda**; F-20 (iki satır + bir senaryo) ve F-23 (tek sözcük) kapatılması öneriliyor, F-21/F-22/F-24 ise VERIFY'ın kanıt tablosunda da halledilebilir.

**STOP — segment burada bitiyor.**
Next: TRIAGE — insan (real / noise / investigate); "investigate" çıkan olursa R-05 ile QA'ya minimal yeniden üretim için gider, doğrudan düzeltmeye değil.

### Triyaj — round 3, 2026-11-04 (insan: MuaddibL)

**5 real · 0 noise · 0 investigate.** Hiçbir bulgu reddedilmedi.

| # | Verdict | Karar gerekçesi |
|---|---|---|
| F-20 | **real** | Reviewer'ın A seçeneği uygulanır (koşul + başlık cümlesi + senaryo). Davranış riski ölçülerek sıfırlandı (bu makinede 380/380 süreçte ppid sayı); dosyanın kendi başlık sözleşmesi şu an yanlış söylüyor ve bu "yorum ≠ davranış" sınıfının üçüncü örneği (F-6, F-17'den sonra). |
| F-21 | **real** | Yalnız plan PB-1 satırına yarım cümle, kod değişikliği yok. Kanıt kaydı: o dalın desteklenen iki platformda da koşmadığı yazılmazsa okuyan koştuğunu sanar. |
| F-22 | **real** | Reviewer bunu "en savunulabilir noise adayı" diye işaretledi; yine de real: spec'in Intent paragrafı bu işin var olma sebebini "bir daha koştur" refleksi diye yazıyor, normatif doküman ayırt etme yolunu söylemeden o refleksi öğretemez. İki dosyaya birer yan cümle. |
| F-23 | **real** | Tek sözcük. Kanıt kaydı yanlış commit'e işaret ediyor ve yazıldığı hâliyle karşıt sonuç veriyor; VERIFY'ın okuyacağı dosyada yanlış bırakılmaz (AGENTS.md kural 4). |
| F-24 | **real** | PB-5'teki "reviewer da aynı nedenle doğrulayamadı" artık doğru değil. Düzeltme kayıt niteliğinde; kapsam ve dosya listesi değişmez. |

Kapsam sınırı değişmedi: **F-12c** (ölçütü check'in pid alt ağacıyla genişletmek) hâlâ bu spec'in dışında, ayrı bir CR'a ait. Fix round 3 yalnız yukarıdaki beş bulguya dokunur.

Fix round limiti: bu üçüncü fix turu, `workflows/feature-development.md:25`'in sınırı içinde (> 3 olsaydı R-06).

### Fix round 3 — sonuç (2026-11-04)

| # | Commit | Ne değişti |
|---|---|---|
| F-20 | `8409977` | `classify-survivors` survivor süzgeci ppid'yi de arıyor (`$1 !~ … \|\| $2 !~ …`), hata mesajı hangi alanın bozuk olduğunu söylüyor, başlık sözleşmesi düzeltildi; `scripts/selftest`'e rakamla başlayan sarılmış satır senaryosu + mesaj iddiası |
| F-21 | `ca22ebd` | PB-1: `note:` dalı desteklenen iki platformun hiçbirinde koşmuyor, varlığı regresyona karşı, kanıtı review okuması. Kod değişikliği yok |
| F-22 | `7546af4` | `docs/testing.md` ve `docs/commands.md`: yeniden koşmadan önce adlandırılan survivor'ın komut satırı okunur — `uv`/`pytest`/`python` kalıntıyı gizler, tarayıcı/sohbet istemcisi makinenin meşguliyetidir |
| F-23 | `5c01801` | Zorlanmış-POSIX kanıt cümlesi `b357515` yerine `1543720` (= `5c098f2^`) diyor; yazıldığı hâliyle yeniden üretilebilir |
| F-24 | `ca50640` | PB-5: prob round 3'te koştu, katlama ifadesi sentetik girdiyle doğrulandı; "otomatik testi yok" iddiası daraltıldı, sınanmayan şey ifadenin `measure()` içindeki yeri |

Doğrulama (tur bitiminde, bu makinede): `./scripts/check` → `CHECK GREEN (full, 6 steps, 8 s)` ·
`./scripts/doctor --strict` → `0 fail, 0 warn` · `./scripts/selftest` → `109 passed, 0 failed, 1 skipped`
(107 → 109: F-20'nin iki yeni iddiası, adlarıyla yeşil).

F-20'nin davranışı reviewer'ın verdiği repro ile iki yönlü doğrulandı:

```
printf '4242\tand\t4242 and the rest of a wrapped command line\n' | sh scripts/lib/classify-survivors posix README.md
# önce: counted  4242  …   rc=0
# sonra: classify-survivors: malformed survivor line (pid or ppid is not a number): …   rc=2
printf '55\t40\tuv run pytest\n' | …   → counted  55  uv run pytest   rc=0   (gerçek survivor hâlâ sınıflanıyor)
```

Residue:

| Koşum | Sonuç |
|---|---|
| `./scripts/residue` (full) | `RESIDUE CLEAN (full, 2 runs)` — ilk denemede; `0 survivor(s), 4 ignored` |
| `./scripts/residue --fast` | `RESIDUE CLEAN (fast, 2 runs)` — ilk denemede; `0 survivor(s), 0 ignored` |

Bu turda full profil **ignore yolunu gerçekten çalıştırdı**: dört OS servisi (iki
`backgroundTaskHost.exe`, `RuntimeBroker.exe`, `svchost.exe`) `(OS service)` gerekçesiyle
listelendi ve sonucu belirlemedi. Round 1 ve round 3 review'larının "gerçek koşum ignore yolunu
hiç çalıştırmadı" sınırlaması bu koşumla kapandı — ölçütün ignore yarısı artık yalnız sentetik
senaryolarla değil, bir gerçek ölçümle de görülmüş durumda.

**Sıradaki: REVIEW round 4** — fix diff'i (`ae9ac65..HEAD`) bağımsız incelemeye gider.

---

## REVIEW round 4 — 2026-11-04

- Round 4: 2026-11-04, `reviewer` subagent, ayrı salt-okunur oturum (AGENTS.md kural 3)
- Diff: `git diff ae9ac65..HEAD` — 6 dosya, 251+/14−, 8 commit (fix round 3); bunların 3'ü yalnız
  bu dosyaya round 3'ün bulgularını/triyajını/sonuç tablosunu ekliyor, esas iş beş fix commit'inde
- Kapsam notu: F-12c hâlâ kapsam dışı, ayrı CR

Rapor aşağıda **olduğu gibi** kayıtlı: yumuşatılmadı, yeniden sıralanmadı, yorum eklenmedi.

### Çalıştırılan doğrulamalar (reviewer, bu makinede, Windows/MINGW)

| Komut | Sonuç |
|---|---|
| `./scripts/check` | `CHECK GREEN (full, 6 steps, 8 s)` — exit 0 |
| `./scripts/doctor --strict` | `== result: 0 fail, 0 warn ==` — exit 0 |
| `./scripts/selftest` | `== selftest: 109 passed, 0 failed, 1 skipped ==` — exit 0 |
| `./scripts/selftest` (ad doğrulaması) | `ok classify: a survivor line whose ppid is not a number (exit 2)` ve `ok classify: says which field left the line malformed` — **ikisi de adıyla yeşil** |
| `./scripts/residue --fast` | `RESIDUE CLEAN (fast, 2 runs)` — ilk denemede; her iki koşumda `0 survivor(s), 0 ignored` |
| `./scripts/residue` (full) | `RESIDUE FOUND (full)` — 1 survivor, Chrome Beta renderer (aşağıda gözlem); `0 ignored` |
| PowerShell probu (canlı tablo) | `total=373`, `nonnumeric_ppid=0`, `nullppid=0`, `embedded_nl_or_tab=0` |
| `git ls-files -s scripts/` | hepsi `100755`, `scripts/lib/classify-survivors` dâhil (F-10 kapalı) |
| `git status --porcelain` | boş — çalışma ağacı temiz |

Üreticinin tur sonu iddiaları **birebir doğrulandı**: `check` yeşil, `doctor --strict` 0 fail,
`selftest` **109 passed / 0 failed / 1 skipped** ve iki yeni iddia adlarıyla geçiyor.

Üreticinin "yeni süzgeç hiçbir gerçek süreci düşürmüyor" iddiası da **bağımsız olarak ölçüldü**:
bu makinede 373 canlı sürecin 373'ünde `ParentProcessId` sayı, null yok. POSIX tarafında
`ps -e -o ppid=` tanım gereği sayı veriyor. F-20'nin davranışı iki yönlü yeniden üretildi:

```sh
printf '4242\tand\t4242 and the rest of a wrapped command line\n' | sh scripts/lib/classify-survivors posix README.md
# → classify-survivors: malformed survivor line (pid or ppid is not a number): …   rc=2
printf '55\t40\tuv run pytest\n' | sh scripts/lib/classify-survivors posix README.md
# → counted  55  uv run pytest   rc=0      (gerçek survivor hâlâ sınıflanıyor)
```

F-23'ün düzeltilmiş referansı da doğrulandı: `git rev-parse --short 5c098f2^` → `1543720`, ve
`git show 1543720:scripts/residue | sed -n '67p'` o commit'te süzgecin gerçekten yalnız `$1`'e
baktığını gösteriyor (`awk -F'\t' '$1 ~ /^[0-9]+$/'`) — yani cümle artık yazıldığı hâliyle
yeniden üretilebilir.

### 1. Round-3 bulgularının kapanış durumu

| # | Durum | Kanıt |
|---|---|---|
| **F-20** | **tam kapandı** (triyajın onayladığı A biçiminde) | Koşul: `scripts/lib/classify-survivors:46` (`$1 !~ … \|\| $2 !~ …`); hata mesajı hangi alanın bozuk olduğunu söylüyor (`:47`); başlık sözleşmesi düzeltildi (`:12-15`); senaryo `scripts/selftest:231-236`, rakamla başlayan sarılmış satırı (`4242<TAB>and<TAB>…`) özellikle ppid dalından geçiriyor. Yukarıdaki iki yönlü repro + 373/373 ölçümü. Kalan tek şey bulgunun (a) yarısı (tablo tarafı sınanmıyor) → **F-26** |
| **F-21** | **tam kapandı (kayıt olarak)** | `specs/plans/0003-plan.md:97` reviewer'ın önerdiği cümleyi birebir taşıyor: `note:` dalı desteklenen iki platformda da koşmuyor, varlığı regresyona karşı, kanıtı review okuması. Kod değişikliği yok — doğru |
| **F-22** | **özünde kapandı, bir kesinlik açığı var** | Ayırt etme cümlesi istenen iki dosyada da var (`docs/testing.md:99-101`, `docs/commands.md:114-115`). Ama öğrettiği ayrım check'in kendi envanterinden dar ve aynı bölümdeki rule 1 ile sürtüşüyor → **F-25** |
| **F-23** | **tam kapandı** | `specs/plans/0003-review.md:891` artık `1543720` (= `5c098f2^`) diyor; referans doğru (yukarıda `git show` ile doğrulandı). Bulgu metnindeki `b357515` alıntısı (`:1016`) yerinde kalmış — alıntı olduğu için doğru |
| **F-24** | **tam kapandı** | `specs/plans/0003-plan.md:101` artık "review round 3'te prob koştu ve ifadenin kendisi sentetik girdiyle doğrulandı … uçtan uca kanıt hâlâ gerçek koşum" diyor; "reviewer da doğrulayamadı" ifadesi kalkmış. Bu turda bağımsız olarak yine ölçüldü: gömülü satır sonu/sekme taşıyan komut satırı 0/373 |

### 2. Regresyon taraması — regresyon bulunmadı

- **Daha sıkı survivor guard'ı gerçek süreç düşürmüyor.** Guard süreç *düşürmüyor* zaten: satırı
  reddedip exit 2 veriyor, sessizce elemiyor. `scripts/residue` üzerinden **erişilemez**, çünkü
  `measure()` (`scripts/residue:68`) tabloyu ve dolayısıyla survivor'ları zaten iki alanı da
  sayı olacak şekilde süzüyor; classify'a yalnız iyi biçimli satır gidiyor. Erişilebilir olsa
  bile bu makinede 373/373 süreçte ppid sayı, POSIX'te `ps -o ppid=` her zaman sayı.
  `4<TAB>0<TAB>System` gibi `ppid=0` olan gerçek satır da sorunsuz geçiyor (yukarıda denendi).
- **Doküman yeniden yazımı `scripts/residue` çıktısıyla çelişmiyor.** Betik her `counted`
  survivor'ı komut satırıyla adlandırıyor (`scripts/residue:125`), yani "önce adlandırılan
  survivor'ın komut satırını oku" talimatının karşılığı çıktıda var. (Tek incelik: Windows'ta
  `CommandLine` okunamayan bir süreç için `$_.Name` basılıyor — `scripts/residue:49` — o durumda
  "komut satırı" yerine yalnız imaj adı görülür; bu turun getirdiği bir şey değil.)
- **Spec ile çelişki yok**; CB-1..CB-4 ve PB-1..PB-6'nın hiçbirinin anlamı bu diffte değişmiyor.
- **Hiçbir iddia zayıflatılmadı** (AGENTS.md kural 5): diffte silinen iddia yok, iki iddia eklendi
  (107 → 109), hiçbir `skip` eklenmedi, eşik/regex gevşetilmedi.
- **Round 1–2'nin düzeltmeleri yerinde:** boş tablo reddi, bozuk-satır reddi, `100755` mod bitleri,
  eski hata metnine atıf yapan bayat referans yok
  (`grep -rn "pid is not a number" --include="*.md" .` → yalnız betiklerin kendi güncel metni).
- **Commit hijyeni temiz:** `git log --stat ae9ac65..HEAD` — her commit yalnız kendi bulgusunun
  dosyalarına dokunuyor, hepsi Conventional Commits + `[review 0003/F-n]`, handoff `[review 0003]`.
- **PB-6:** `scripts/doctor`, `scripts/residue`, `workflows/bootstrap.md`, `.github/workflows/check.yml`
  bu turun diffinde **yok**; `doctor --strict` 0 fail.

Round 1 ve 2'den kalıp sonraki turların dokunmadığı açık bir iş bulunmadı. Bilinçli açık
bırakılanlar (kayıtlı): F-11 noise, F-12c ayrı CR, F-2'nin eşik-aşımı dalının testsizliği
(`specs/plans/0003-plan.md:97`'de yazılı).

### 3. Plan conformance (R-07) — clean

Bu turun 6 dosyasının 5'i planın listesinde (`docs/commands.md`, `docs/testing.md`,
`scripts/lib/classify-survivors`, `scripts/selftest`, `specs/plans/0003-plan.md`); 6.'sı
`specs/plans/0003-review.md`, planın onay sonrası notuyla (`specs/plans/0003-plan.md:6-10`)
açıklanmış durumda. Dal genelinde `git diff --name-only main..HEAD` = 10 dosya = planın 9'u +
açıklanmış review raporu. Drift yok.

### Findings

#### F-25 — Low — Docs / Correctness
**F-22'nin ayırt etme cümlesi, check'in kendi envanterinden dar ve aynı bölümdeki rule 1 ile
çelişiyor: "tarayıcı gördüysen makine meşguldü" tam olarak rule 1'in check kalıntısı saydığı
şeylerden biri.**

Evidence —
- `docs/testing.md:99-101` (normatif kural, CB-4'ün yazdığı metin): *"Read the survivor the run
  names before you rerun: `uv`, `pytest` or `python` in that command line means a rerun would hide
  residue; a browser or a chat client means the machine was busy."* Aynısı
  `docs/commands.md:114-115`.
- Aynı bölümün rule 1'i (`docs/testing.md:71-74`) check'in bırakabileceklerini sayarken
  **tarayıcıyı ve test altındaki uygulamayı** açıkça listeliyor: *"build/compile daemons,
  package-manager services, test hosts and parallel workers, watch modes, **browsers, the
  application under test**, containers or emulators started for the run."*
- Check'in bu depodaki süreç envanteri üç değil dört araç: `scripts/check.conf:3` — *"uv, ruff,
  mypy and pytest are run-once processes"*; adımlar `scripts/check.conf:8-18`. `ruff` ve `mypy`
  alt süreçleri `uv run --frozen ruff|mypy` ile doğrudan `.venv\Scripts\*.exe` olarak doğuyor;
  komut satırlarında `uv`/`pytest`/`python` jetonlarının hiçbiri geçmek zorunda değil.

Reproduce — `sed -n '71,74p;99,101p' docs/testing.md` · `sed -n '3p;8,18p' scripts/check.conf` ·
`sed -n '114,115p' docs/commands.md`

Impact — Cümle iki dalla kurulmuş ve ikilik gibi okunuyor: "uv/pytest/python → kalıntı" vs.
"tarayıcı/sohbet istemcisi → makine meşgul". İkisine de uymayan bir survivor (sızmış `ruff.exe`,
`mypy.exe`, bir E2E tarayıcısı, test altındaki uygulama) için okuyucuya cevap kalmıyor; en
yakın dal "makine meşguldü" olduğu için refleks yeniden koşmak oluyor — spec'in Intent paragrafının
(`specs/active/0003-residue-noise.md:18-20`) bu işin varlık sebebi diye yazdığı tam o refleks,
üstelik bu kez normatif dokümanın cümlesiyle meşrulaşmış hâlde. `docs/testing.md` ANEW şablonuyla
başka depolara da gidiyor; check'i tarayıcı başlatan bir projede cümle doğrudan yanlış
yönlendirir. Bugünkü bu deponun `check.conf`'u tarayıcı başlatmadığı ve UI adımı offscreen
`python.exe` olduğu için **bugün** somut bir yanlış yeşile yol açmıyor — ağırlığı bu yüzden Low.

Recommended action — kod değişikliği yok, iki dosyada birer yarım cümle:
(1) ilk dalı jeton listesi yerine envantere bağlayın — *"check'in adımlarından biri
(`scripts/check.conf`; bugün uv, ruff, mypy, pytest) ya da onların bir çocuğu"*;
(2) ikinci dalı sahiplenmeyle sınırlayın — *"**sizin** açıklayabildiğiniz bir uygulama
(tarayıcınız, sohbet istemciniz)"*; ve (3) ikiliği kapatan fail-closed varsayılanı yazın:
*"ikisine de uymuyorsa check'in sayın — ölçüt zaten o tarafa yanılmak üzere kurulu."*
Bu üçü rule 1 ile rule 2'yi yeniden aynı şeyi söyler hâle getirir (CB-4'ün iddiası).

#### F-26 — Info — Tests
**F-20'nin (a) yarısı açık kaldı: fix round 2'de eklenen tablo-tarafı süzgecini (`$2` sayı olmalı)
hâlâ hiçbir senaryo iddia etmiyor.**

Evidence — `scripts/lib/classify-survivors:45`
(`NR == FNR { if ($1 ~ /^[0-9]+$/ && $2 ~ /^[0-9]+$/) { ppid[$1] = $2; cmd[$1] = $3 }; next }`)
F-13 için eklendi; `scripts/selftest`'teki sentetik tabloların (POSIX `:196-201`, Windows
`:212-223`) **her satırında** ppid sayı, yani o koşulun ikinci yarısı hiçbir senaryoda
tetiklenmiyor. Bu turun yeni senaryosu (`:231-236`) survivor tarafını sınıyor, tabloyu değil.

Reproduce — `sed -n '45p' scripts/lib/classify-survivors` · `sed -n '196,201p;212,223p' scripts/selftest`

Impact — Düşük ve yönü güvenli: bozuk bir tablo satırı sessizce atılınca soy zinciri daha erken
kırılır → `counted` (fail-closed), yani olsa olsa yanlış kırmızı. `scripts/residue` üzerinden
erişilemez (`scripts/residue:68` tabloyu önceden süzüyor). Önemi, planın 1. adımının yardımcıyı
ayrı dosya yapma gerekçesini "sınıflandırma mantığı sentetik girdiyle sınanabilsin"
(`specs/plans/0003-plan.md:33-36`) diye yazması: o gerekçe bu satır için hâlâ kullanılmadı.
Rakamla başlayan sarılmış bir **tablo** satırı gerçek bir pid ile çakışırsa o pid'in ppid/cmd
kaydını ezebilir — bugün erişilemez ama yardımcının kendi arayüzünde mümkün.

Recommended action — **Bunun için ayrı bir fix turu açılmasını önermiyorum** (bkz. aşağıdaki
R-06 notu). İki savunulabilir yol: (a) başka bir sebeple commit açılırsa POSIX tablosuna tek satır
(`"  ve bu satır sarıldı"` gibi ppid'si sayı olmayan bir satır) eklenip mevcut `exits 0` +
`counted 99` iddialarının değişmediği gösterilsin — davranış riski yok; (b) kod ve test
değişmeden, bu açık VERIFY'ın kanıt tablosunda CB-1 satırına "tablo-tarafı süzgeci review
okumasıyla korunuyor" diye yazılsın. Daha ucuz ve tutarlı olduğu için **(b)** öneriliyor —
F-14/F-21'de aynı dürüstlükle yapılanın eşi.

#### F-27 — Info — Evidence record
**Fix round 3 kaydı, doğası gereği tekrarlanamayan tek bir gözlemle bir sınırlamayı "kapandı"
ilan ediyor; bu turun üç ölçümünün üçünde de `ignored` yolu yine hiç çalışmadı.**

Evidence — `specs/plans/0003-review.md:1109-1113`: *"Bu turda full profil **ignore yolunu
gerçekten çalıştırdı** … Round 1 ve round 3 review'larının 'gerçek koşum ignore yolunu hiç
çalıştırmadı' sınırlaması bu koşumla kapandı."* Bu turda (reviewer, aynı makine, aynı commit):
`./scripts/residue --fast` → iki koşumda da `0 survivor(s), 0 ignored`; `./scripts/residue` (full)
→ run 1 `1 survivor(s), 0 ignored`, run 2 `0 survivor(s), 0 ignored`. Yani kayıt **yanlış değil**
(o koşum olmuş olabilir), ama talep üzerine yeniden üretilemiyor ve bunu üretici kendi işi için
yazmış (AGENTS.md kural 3'ün ayırdığı rol).

Reproduce — `./scripts/residue` ve `./scripts/residue --fast` (sonuç makinenin o anki durumuna bağlı)

Impact — Yok denecek kadar az; kanıt kaydının niteliği hakkında. Planın R-5 notunda aynı sınıftaki
tek seferlik gözlem için zaten bir kayıt deseni var (`specs/plans/0003-plan.md:72-74`: *"bu kanıt
üreticinin tek seferlik gözlemi — reviewer kendi turunda … bulamadı"*); burada o niteleyici yok,
dolayısıyla VERIFY'ın okuyacağı kayıt, ölçütün ignore yarısının artık gerçek koşumla istenildiğinde
gösterilebildiği izlenimini verebilir. Gösterilemiyor: ignore yolu ancak ölçüm penceresinde doğup
settle'ı atlatan bir OS-servis soyu varsa dolar.

Recommended action — Kod ve test değişikliği yok. VERIFY kanıt tablosuna iki satır yazılsın:
üreticinin koşumu (`0 survivor(s), 4 ignored`, dört OS servisi) **ve** review round 4'ün koşumları
(`0 ignored`, 3 ölçüm); ölçütün ignore yarısının deterministik kanıtının hâlâ sentetik senaryolar
olduğu cümlesi korunsun. İstenirse review kaydındaki "sınırlaması kapandı" ifadesi "bir kez
gözlendi; talep üzerine yeniden üretilemiyor" diye niteliklendirilsin — ama **bunun için fix turu
açılmasın**.

### Gözlem (bulgu değil, talimat gereği)

`./scripts/residue` (full) bu turda ilk denemede kırmızı bitti; tek survivor ölçüm penceresinde
doğan bir tarayıcı renderer'ıydı:

```
after run 1: 373 processes, 1 survivor(s), 0 ignored; 41189 MB available (-106 MB vs baseline)
  survivor  26792  "C:\Program Files\Google\Chrome Beta\Application\chrome.exe" --type=renderer
            --gpu-client-id=1933 --extension-process … --renderer-client-id=1933 … /prefetch:9
after run 2: 371 processes, 0 survivor(s), 0 ignored; 41165 MB available (-130 MB vs baseline)
RESIDUE FOUND (full): stop what survived inside the step that starts it
```

`--fast` aynı turda ilk denemede `RESIDUE CLEAN (fast, 2 runs)`. Bu, `docs/testing.md:95-101`'in
yazdığı ve F-12'nin belgelediği fail-closed davranış — kusur değil, bulgu olarak **sunulmuyor**.
Sayısal kayıt: round 2'de 4 koşumun 2'si, round 3'te 2 koşumun 2'si, fix round 3'te 2 koşumun 0'ı,
bu turda 2 koşumun 1'i kırmızı. (İroni olarak kayda değer: bu survivor, F-25'in işaret ettiği
"tarayıcı → makine meşguldü" cümlesinin doğru çalıştığı durum; cümlenin açığı tersi durumda.)

İkinci not: `ignored` listesi bu turda hiç dolmadı → F-27.

### Dimension özeti

- **Correctness:** clean. F-20 kodda tam kapandı, davranışı iki yönlü üretildi; `residue` ve
  `classify-survivors` arasındaki sözleşme tutarlı.
- **Security:** clean. Yeni kod yok denecek kadar az (bir awk koşulu + bir mesaj değişkeni);
  `eval` yok, veri `-v` ve dosya argümanıyla geçiyor, depoya yazım yok. F-7'nin uyarı cümlesi
  (`docs/commands.md:108-111`) yerinde; bu turun eklediği cümle onu zayıflatmıyor.
- **Edge cases:** clean. Boş tablo, bozuk pid, bozuk ppid (yeni), `ppid=0`, soy döngüsü, kendi
  ebeveyni, yürünemeyen soy — hepsi ya reddediliyor ya `counted`.
- **Performance:** clean. Eklenen iş satır başına bir alan karşılaştırması; full profil bu turda
  da aynı mertebede (~75 s).
- **Tests:** F-26. Sayım 109 passed / 0 failed / 1 skipped; iki yeni iddia adıyla yeşil, hiçbir
  iddia zayıflatılmadı veya atlanmadı.
- **Maintainability:** clean. Başlık sözleşmesi (`classify-survivors:12-15`) artık davranışı doğru
  anlatıyor — "yorum ≠ davranış" sınıfının (F-6, F-17, F-20) bu örneği kapandı. Ölü kod yok.
- **Plan conformance:** clean (R-07 ihlali yok).
- **Docs:** F-25, F-27. CB-4'ün "doküman ve betik aynı şeyi söyler" iddiası betik tarafında
  tutuyor; F-25 dokümanın **kendi içindeki** (rule 1 ↔ rule 2) sürtüşmesi.

### Verdict (reviewer)

Fix round 3, round 3'ün beş real bulgusunun **dördünü tam** (F-20 triyajın onayladığı A biçiminde,
F-21 ve F-24 kayıt olarak, F-23 birebir) ve **birini özünde** (F-22) kapatmış. **Regresyon yok**:
en riskli değişiklik olan daha sıkı survivor guard'ı bu makinede 373 süreç üzerinde bağımsız
ölçülerek elendi, üstelik guard süreç düşürmüyor (reddedip exit 2 veriyor) ve `scripts/residue`
üzerinden erişilemez. Üreticinin üç sayısal iddiasının (109/0/1, iki yeni iddia adıyla yeşil,
ppid daima sayı) **üçü de doğrulandı**.

Yeni bulguların üçü de Low/Info ve hiçbiri bugün kodun davranışını bozmuyor: biri doküman kesinliği
(F-25), ikisi kanıt kaydı/test kapsamı (F-26, F-27). Reviewer'ın okumasıyla bu değişiklik seti
**gönderilebilir durumda**.

#### R-06 notu (insanın triyajına girdi)

Bu üçüncü fix turuydu; `workflows/feature-development.md:25` *"Rounds > 3 → R-06"* diyor, yani
**dördüncü bir fix turu R-06'yı tetikler** (`prompts/recovery/fix-loop-limit.md`: kod yazma, yalnız
analiz — kök neden spec'te mi plan'da mı?). Benim bulgularımın **hiçbiri kod değişikliği
gerektirmiyor**; F-25 iki dosyada birer yarım cümle, F-26/F-27 kayıt işi.

Önerim: **dördüncü fix turu açılmasın.** Üç tur boyunca `scripts/residue` ve
`classify-survivors`'ın davranışı round 2'den beri tek bir jeton dışında sabit kaldı; turlar arası
iş hep "yeni yazdığımız cümle yarım kaldı" sınıfındaydı (F-6 → F-17 → F-18 → F-22 → F-25) — bu,
R-06'nın aramasını istediği türden bir spec/plan kök nedeni **değil**; ölçüt doğru, plan doğru,
yalnız doküman düzyazısı tur başına bir tık daha kesinleşiyor. Dolayısıyla F-25'i real triyaj edip
VERIFY/SHIP'in doküman geçişine bağlamayı öneriyorum (`docs/testing.md` ve `docs/commands.md`
zaten CB-4 kapsamında review'da okunuyor); F-26 ve F-27 doğrudan VERIFY'ın kanıt tablosuna
yazılarak kapanır. İnsan yine de şimdi düzeltmek isterse: bu, letter-of-the-rule gereği dördüncü
tur sayılır ve R-06 **biçimsel olarak uygulanır** — o analizden çıkacak verdict'in, elimdeki
kanıtla, "continue (doküman-only; kök neden spec'te ya da planda değil)" olacağını şimdiden
söyleyebilirim; bu tercih edilirse review kaydına R-06'nın tartıldığı ve niye aşılmadığı yazılsın.

**STOP — segment burada bitiyor.**
Next: TRIAGE — insan (real / noise / investigate); "investigate" çıkan olursa R-05 ile QA'ya
minimal yeniden üretim için gider, doğrudan düzeltmeye değil.

### Triyaj — round 4, 2026-11-04 (insan: MuaddibL)

**3 real · 0 noise · 0 investigate.** Hiçbir bulgu reddedilmedi.

| # | Verdict | Karar gerekçesi |
|---|---|---|
| F-25 | **real** | Reviewer'ın üç parçalı önerisi uygulanır: ilk dal jeton listesi yerine `scripts/check.conf` envanterine bağlanır, ikinci dal "sizin açıklayabildiğiniz uygulama" diye sınırlanır, ikiliği kapatan fail-closed varsayılan yazılır. Ağırlık nedeni: `docs/testing.md` ANEW şablonuyla başka depolara gidiyor; check'i tarayıcı başlatan bir projede cümle yanlış yönlendirir. Kod değişikliği yok. |
| F-26 | **real**, reviewer'ın **(a)** seçeneğiyle | Reviewer (b)'yi (kaydet, düzeltme) yeni tur açılmasın diye önermişti; tur F-25 için zaten açıldığından (a) tercih edildi: POSIX sentetik tablosuna ppid'si sayı olmayan tek satır, mevcut iddialar değişmeden. Davranış riski yok ve planın 1. adımının yardımcıyı ayrı dosya yapma gerekçesi (`specs/plans/0003-plan.md:33-36`) nihayet bu satır için de kullanılır. |
| F-27 | **real** | Fix round 3 kaydı tek bir gözlemle "sınırlama kapandı" diyor; reviewer aynı makinede üç ölçümde ignore yolunu göremedi. Cümle niteliklendirilir ve reviewer'ın koşumları da kayda girer. Tek cümle, kod yok. |

#### R-06 kararı (insan)

Bu dördüncü fix turu, `workflows/feature-development.md:25` gereği R-06'yı
(`prompts/recovery/fix-loop-limit.md`) tetikliyor. Konu triyajda açıkça tartıldı:

- Reviewer, kök nedenin spec'te ya da planda olmadığını, turlar arası işin hep "yeni yazılan cümle
  yarım kaldı" sınıfında kaldığını (F-6 → F-17 → F-18 → F-22 → F-25) söyleyip dördüncü tur
  açılmamasını önerdi.
- Üretici, bir recovery rampasının sonucunu önceden söyleyip rampayı atlamanın kapıların engellemek
  için var olduğu kısa yol olduğunu söyleyerek R-06 analizinin koşulmasını önerdi.
- **İnsanın kararı: R-06 analizi koşulmadan fix round 4'e geçilir.** Gerekçe kayıt altında: bu turun
  üç bulgusunun hiçbiri kod değişikliği gerektirmiyor (iki doküman cümlesi, bir selftest tablo
  satırı, bir kayıt düzeltmesi), yani R-06'nın koruduğu şey — "kök neden koddaysa kodu daha fazla
  yamamak" — bu turda zaten söz konusu değil.

Bu karar VERIFY'ın okuyacağı kayıttır: R-06 atlanmadı, **tartılıp insan tarafından aşıldı**.

Kapsam sınırı değişmedi: **F-12c** hâlâ bu spec'in dışında, ayrı bir CR'a ait.
