# Review 0003 — residue noise

- Spec: `specs/active/0003-residue-noise.md`
- Plan: `specs/plans/0003-plan.md`
- Round 1: 2026-11-04, `reviewer` subagent, ayrı salt-okunur oturum (AGENTS.md kural 3)
- Diff: `git diff main..HEAD` on `feature/0003-residue-noise`, 7 commit, 9 dosya
- Status: round 2 triyajı tamam (8 real) — fix round 2 başladı

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
