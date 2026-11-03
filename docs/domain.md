# Domain

Kodda İngilizce karşılık kullanılır; konuşma, spec ve UI'da Türkçe terim. Aynı kelime = aynı anlam.

Ürün adı **Notes&MJ**; `MJ` = *My Job*. Kod ve dosya adlarında `notes-mj` / `notes_mj` yazılır
(`&` paket ve dosya adlarında geçerli değildir).

## Ubiquitous language

| Term | Meaning | Notes / not to be confused with |
|---|---|---|
| Görev (`Task`) | Yapılacak tek iş kalemi | Zaman Bloğu ile aynı şey değil: görev *ne*, blok *ne zaman* |
| Gün Planı (`DayPlan`) | Belirli bir takvim gününün görevleri ve zaman blokları | Takvim günü yerel saate göre belirlenir |
| Zaman Bloğu (`TimeBlock`) | Gün içinde başlangıç–bitiş saati olan planlanmış aralık | Mola da bir bloktur; bir Göreve bağlanabilir ama şart değil |
| Odak Oturumu (`FocusSession`) | Bir Görev üzerinde geçirilen, zamanlanmış kesintisiz çalışma | Zaman Bloğu plandır, Odak Oturumu gerçekleşendir |
| Pomodoro Döngüsü (`PomodoroCycle`) | Çalışma + mola tekrarlarından oluşan dizi (ör. 4 seans) | Odak Oturumu'nun bir biçimi; tek biçimi değil |
| Not (`Note`) | Serbest metin kaydı | Tek başına var olabilir (BR-2) |
| Proje (`Project`) | Görevleri gruplayan uzun ömürlü iş başlığı | Etiket değildir: bir Görev en fazla bir Projeye aittir |
| Etiket (`Tag`) | Görev ve Notları kesen serbest sınıflandırma | Çoktan çoğa; Proje ile karıştırılmaz |
| Eisenhower Çeyreği (`EisenhowerQuadrant`) | Acil/Önemli ekseninde dört çeyrek: Yap, Planla, Devret, Ele | Öncelik alanıdır, durum değil |
| Günün 3 Büyük Odağı (`TopThree`) | Gün için seçilen en fazla üç öncelikli Görev | Gün Planı'nın tamamı değil (BR-7) |
| Devir (`RollOver`) | Tamamlanmamış Görev'in ertesi günün planına aktarılması | Kopyalama değil: aynı Görev taşınır, sayacı artar (BR-1) |
| Devir Sayısı (`rollover_count`) | Bir Görev'in kaç kez devrettiği | Sürüncemede kalan işin görünür sinyali |
| Aktif (`Active`) | Öğenin normal, listelerde görünen durumu | |
| Arşivlendi (`Archived`) | Tamamlanmış ama saklanan öğe | Silme değildir (BR-4) |
| Çöpte (`Trashed`) | Silinmiş ama geri alınabilir öğe | Kalıcı silme ayrı ve açık bir eylemdir (BR-3) |
| Bilişsel Yük (`CognitiveLoad`) | Günün planlanan yoğunluğunun özeti | Türetilmiş gösterge; saklanan veri değil |

## Business rules
- **BR-1:** Gün sonunda tamamlanmamış Görev, ertesi günün planına **devreder**; Görev'in Devir
  Sayısı bir artar ve arayüzde görünür. Devir sessiz değildir — devreden görev işaretlidir.
- **BR-2:** Bir Not tek başına var olabilir; isteğe bağlı olarak en fazla bir Göreve ve/veya bir
  Gün Planı'na bağlanır. Not alma hiçbir bağlantı zorunluluğuyla yavaşlatılmaz.
- **BR-3:** Silinen öğe önce **Çöpte** durumuna geçer ve geri alınabilir. Kalıcı silme, kullanıcının
  ayrı ve açık bir eylemidir; onay ister.
- **BR-4:** Arşivleme silme değildir: Arşivlenen öğe varsayılan listelerde görünmez, aramada ve
  arşiv ekranında bulunur, geri alınabilir.
- **BR-5:** Bir Odak Oturumu en fazla bir Göreve bağlıdır ve aynı anda yalnızca bir Odak Oturumu
  etkin olabilir. Yeni oturum başlatmak, etkin oturumu bitirir (kullanıcıya sorulur).
- **BR-6:** Aynı Gün Planı içindeki Zaman Blokları çakışamaz.
- **BR-7:** Günün 3 Büyük Odağı en fazla üç Görev içerir; dördüncüsü eklenemez.
- **BR-8:** Etiket adı büyük/küçük harf duyarsız benzersizdir (`#UX` ile `#ux` aynı Etiket'tir).

## Key domain invariants
- **Veri makineden çıkmaz.** Hiçbir kayıt ağa gönderilmez, hiçbir dış servise yazılmaz
  (`docs/security.md`).
- Kayıtlar yok edilmez: durum **Aktif → Arşivlendi → Çöpte** üzerinden ilerler; tek istisna
  kullanıcının açık kalıcı silme eylemidir (BR-3).
- Takvim günü ve blok saatleri **yerel saat** esaslıdır; oluşturma/değiştirme damgaları UTC
  (`docs/conventions.md`, Data rules).
- Bir Görev en fazla bir Projeye aittir; Etiket sayısı sınırsızdır.
- Odak Oturumu geçmişi değiştirilemez: biten bir oturumun süresi sonradan düzenlenmez.

## Deliberately out of scope
Senkronizasyon ve çoklu cihaz, paylaşım ve ekip görünümleri, dış takvim/e-posta entegrasyonları —
gerekçe ve kapsam dışı listesinin tamamı: `docs/architecture.md`.
