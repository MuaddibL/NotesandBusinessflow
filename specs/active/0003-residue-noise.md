# Spec 0003 — residue noise (mini)

- Status: In progress
- Mode: lite
- Plan: `specs/plans/0003-plan.md`
- Source: CR-2026-11-03-residue-noise — spec 0002'nin PR'ında (#1) `residue` job'ının aynı commit
  üzerinde bir koşumda düşüp bir koşumda geçmesi (`specs/plans/0002-review.md`, VERIFY turu / V-6)
- Design: none — no user interface
- Supersedes: yok. `specs/done/0001-app-skeleton.md` AC-12 ve `specs/done/0002-desktop-shell.md`
  PB-3 zaten "**check'e ait** hayatta kalan süreç raporlamaz" diyor; bu değişiklik o ölçütleri
  değiştirmiyor, ölçümü onlara uyduruyor. Değişen normatif metin `docs/testing.md` Resource
  hygiene rule 2'dir (CB-4).

## Intent
Kalıntı testi bugün süreç **sayısını** baz alıyor: ölçüm aralığında ortaya çıkan her süreç —
işletim sisteminin kendi başlattıkları dâhil — hayatta kalan sayılıyor ve betiği kırmızı yapıyor.
Sonuç, aynı commit'in bir koşumda geçip birinde düşmesi: CI'da Linux çekirdek iş parçacıkları,
geliştirme makinesinde Windows arama ve servis süreçleri. Şimdi gerekiyor çünkü bu hâliyle her
PR'da "bir daha koştur" alışkanlığı doğuyor; o alışkanlık, testin yakalamak için var olduğu gerçek
kalıntıyı da görünmez kılar.

## Changed behavior
- [ ] CB-1 — Betik, hayatta kalan süreçleri iki kümeye ayırır: **check'in başlatmış olabileceği**
  süreçler ve **başlatmış olamayacağı** sistem süreçleri. Çıkış kodunu yalnızca birinci küme
  belirler; ikinci küme boş olmasa da betik yeşil biter.

  *Ayrımın ölçütü bu spec'te tanımlanmaz, planda **ölçülerek** belirlenir.* Bir süreç, onu
  başlatan süreç öldükten sonra ebeveynini kaybeder (POSIX'te init'e devredilir, Windows'ta PID
  yeniden kullanılabilir), bu yüzden "check'in çocuğu muydu" sorusu sonradan güvenilir biçimde
  sorulamaz. Ölçüt varsayımla değil, iki platformda da gözlemle doğrulanarak seçilir; Windows'ta
  sabit bir süreç-adı listesi kırılgan olacağı için kabul edilmez (bilinmeyen bir servis yarın
  yine kırmızı verir).
- [ ] CB-2 — Yok sayılan süreçler çıktıdan kaybolmaz: ayrı bir başlık altında, PID ve komut
  satırıyla listelenir ve **her satır kendi** yok sayılma sebebini taşır (tek bir toplu dipnot
  değil — on beş satırın hepsi aynı sebeple elenmediyse toplu dipnot yanıltır).
- [ ] CB-3 — Check'e ait bir süreç hayatta kaldığında betik hâlâ kırmızı biter (çıkış kodu 1),
  o süreci PID ve komut satırıyla adlandırır ve bugünkü `RESIDUE FOUND` satırını verir.

  Kanıt yöntemi: `scripts/selftest`'in kasıtlı olarak bir süreç sızdıran senaryosu — depoda
  zaten var ve CI'daki `doctor` job'ında koşuyor. Elle gözlem, var olan otomatik bir testin
  yerine geçmez. (Plan 0003/R-6, onaylandı 2026-11-04.)
- [ ] CB-4 — `docs/testing.md` Resource hygiene **rule 1 ve rule 2** kuralın yeni tanımını yazar:
  ölçüt "süreç sayısı başlangıç değerine döner" / "no survivors of any kind" değil, "**check'e
  ait** hiçbir süreç hayatta kalmaz"dır. İki kural birbiriyle ve betikle aynı şeyi söyler.

## Preserved behavior
- [ ] PB-1 — Bellek davranışı değişmez: `ANEW_RESIDUE_MB` (varsayılan 512) aşıldığında betik
  kırmızı biter ve farkı MB cinsinden bildirir; belleğin ölçülemediği platformda yalnızca
  süreçlere bakıldığını söyleyen not korunur.
- [ ] PB-2 — Check kırmızıysa kalıntı testi yapılmaz: betik
  `RESIDUE TEST ABORTED (<profil>): check failed in run <n> — the residue test needs a green check`
  yazıp 1 döner.
- [ ] PB-3 — İki-koşum ve iki-bakış yapısı korunur: her koşumdan sonra `ANEW_RESIDUE_SETTLE`
  (varsayılan 5 sn) kadar beklenir ve yeni görünen bir süreç ancak bir bekleme sonra hâlâ
  hayattaysa hayatta kalan sayılır — kısa ömürlü süreçler elenmeye devam eder.
- [ ] PB-4 — Komut arayüzü aynı kalır: `./scripts/residue` (full) ve `./scripts/residue --fast`;
  başka her kullanım `usage` yazıp 2 döner; `ANEW_RESIDUE_SETTLE`/`ANEW_RESIDUE_MB`'nin sayı
  olmayan değeri de 2 döndürür. Çıkış kodu sözleşmesi 0/1/2 değişmez.
- [ ] PB-5 — Betik hem Windows (MINGW/MSYS/CYGWIN) hem POSIX'te çalışmaya devam eder; süreç
  listesi alınamayan bir platformda bugünkü `residue: cannot list processes on this platform`
  davranışı (çıkış 2) korunur.
- [ ] PB-6 — Betiği çağıran yerler değişmeden çalışır: `./scripts/doctor`, `workflows/bootstrap.md`
  ve CI'daki `residue` job'ı.

## Out of scope
- `scripts/check`'in kendisi ve adımları.
- **Bellek tarafındaki aynı gürültü.** Tolerans da işletim sisteminin kendi tüketiminden
  etkilenebilir, ama bu bugüne kadar bir kez bile gözlenmedi (flaky olan yalnızca süreç ayağı).
  Varsayımla iş genişletilmiyor: bellek ölçümü PB-1'de olduğu gibi kalır; gözlenirse kendi
  change request'iyle gelir.
- Check'e zaman aşımı mekanizması eklemek (VERIFY'da "hiç gözlenmedi" diye kaydedildi, ayrı iş).
- `ANEW_RESIDUE_SETTLE` / `ANEW_RESIDUE_MB` varsayılanlarının değişmesi.
- CI'ın `residue` job'ını zorunlu durum kontrolü yapması/yapmaması kararı (depo ayarı, insan).
- Rule 2 dışındaki doküman değişiklikleri.
- Windows dışı platformlarda paketleme/test kapsamının genişlemesi.

## Definition of Done
- [ ] `scripts/check` green
- [ ] Independent review done; real findings fixed, noise rejected with written rationale
- [ ] Criterion ↔ evidence table complete for CB-* **and** PB-*
- [ ] Spec moved to `specs/done/` (immutable there)
