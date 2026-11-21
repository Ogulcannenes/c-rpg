# Görsel UI/UX, Erişilebilirlik ve Teknik Kalite Denetimi

Tarih: 2026-11-21 · Dal: `modernization` · Sürüm 0.5.0

## Yöntem

- **Gerçek uygulama:** Puanlar çalışan uygulamadan alındı. Uygulama, geçici bir veritabanıyla Chrome'da açıldı. "Mira" adlı bir profil oluşturuldu ve 2 görev gerçekten çözüldü.
- **Ekran görüntüleri:** Toplam 26 görüntü alındı. Önce 15 menü bölümünün hepsi, karşılama ekranı, ders, quiz, kod editörü, boss, ayarlar ve profil ekranları görüntülendi.
- **Boyutlar:** 980×680 (en küçük pencere), 1440×900 ve 1920×1080 kullanıldı. Rusça arayüz de kontrol edildi.
- **Ölçümler:** Sayfanın içinde çalışan betiklerle şunlar ölçüldü:
  - yatay taşma,
  - WCAG kontrastı (2. turda üst öğelerin opaklığı da hesaba katıldı),
  - 11 px altındaki yazılar,
  - adsız düğmeler,
  - görünüm değiştiğinde odak ve başlık,
  - kare hızı.
- **Bağımsız puanlama:** Beş ajan çalıştı. UI Designer, UX Architect, Accessibility Auditor ve Code Reviewer aynı kanıtlarla, salt okunur ve birbirinden bağımsız puan verdi. Reality Checker 16 iddiayı kodda ve görüntülerde doğruladı. Sonra her düzeltme turunu yeniden puanladı.
- **Formül:** Görsel kalite, 9 kriterin eşit ağırlıklı ortalamasıdır. Toplam = 0.6 × teknik + 0.4 × görsel.

**"15 tema" kriteri hakkında:** Uygulamada renk teması sistemi yok; tek bir koyu tema var. Bu kriter, menüdeki 15 bölümün görsel bütünlüğü olarak değerlendirildi. Bu bir yorumdur, tema testi değildir.

## Puanlar

| Görsel kalite kriteri | Önce | 1. tur | 2. tur |
|---|---:|---:|---:|
| Görsel tasarım ve estetik | 80 | 82 | **83** |
| UI tutarlılığı | 68 | 73 | **76** |
| Kullanıcı deneyimi | 72 | 77 | **79** |
| Renk, kontrast ve tipografi | 68 | 75 | **77** |
| Animasyonlar | 75 | 78 | **80** |
| Responsive tasarım | 73 | 76 | **79** |
| 15 bölümün bütünlüğü | 76 | 78 | **79** |
| Erişilebilirlik | 64 | 72 | **76** |
| Profesyonellik ve detay | 70 | 75 | **77** |
| **GENEL GÖRSEL KALİTE** | **71.8** | **76.2** | **78.4** |
| Teknik kalite | 68 | 73 | **77** |
| **TOPLAM KALİTE** | **69.5** | **74.3** | **77.6** |

- **"Önce" sütunu:** Dört uzman ajan şu puanları vermişti: renk ve tipografi 71, animasyon 79, erişilebilirlik 67. Reality Checker bunları kanıt yetersizliği nedeniyle sırasıyla 68, 75 ve 64'e düşürdü; tabloda bu daha sıkı değerler kullanılıyor.
- **Üçüncü tur:** 2. tur puanlamasından sonra 3. tur düzeltmeleri de yapıldı (aşağıda). Bu tur **bağımsız olarak yeniden puanlanmadı**, bu yüzden tabloda yer almıyor.

## Kanıt: ölçümler

| Ölçüm | Önce | Sonra |
|---|---|---|
| 11 px altı metin düğümü (15 bölüm, 1440 px) | ~350 (harita tek başına 118) | 8 (laboratuvar SVG etiketleri) |
| WCAG AA kontrast hatası (ölçülebilen 766 düğüm, opaklık dahil) | 54 | 0 gerçek hata (6'sı süs öğesi ya da devre dışı kontrol) |
| Kilitli başarım metni kontrastı | ≈2.85:1 | ≥5.5:1 (renk tokenı) |
| 980 px'te sayfa taşması | 0 | 0 (15/15 bölüm) |
| 980 px'te kesilen ya da kırılan menü/profil etiketi | birkaç (m02) | 0 |
| Görünüm değişiminde odak ve `document.title` | yok, başlık hep aynı | h1'e odak ve "Bölüm · C++ Adventure" (15 bölüm, ayarlar, profiller) |
| 1440×900'de Çalıştır/Gönder | ekranın dışında | yapışkan çubuk, görünür |
| Kare hızı (pencere önde) | — | ~100 fps; "Animasyonları azalt" açıkken çalışan animasyon 0 |

Ekran görüntüleri (`docs/screenshots/ux/`):

| | Önce | Sonra |
|---|---|---|
| Ders girişi (boş kart) | `01-before-lesson-intro.png` | `01-after-lesson-intro.png` |
| Boss görevi (kilit mesajı, ekran dışı düğmeler, "Boss Challenge") | `02-before-boss-task.png` | `02-after-boss-task.jpeg` |
| Başarımlar (soluk kilitli metin) | `03-before-achievements.png` | `03-after-achievements.jpeg` |
| 980 px (sıkışık kenar çubuğu, kırılan düğme) | `04-before-shop-980.png` | `04-after-home-980.jpeg` |
| Kariyer (boş "—" durumları) | `05-before-career.png` | `05-after-career.jpeg` |
| Ayarlar > Görünüm (yeni) | — | `06-after-settings-appearance.jpeg` |

## Düzeltilen sorunlar

**Kullanıcı deneyimi ve profesyonellik**
- 1\. bölümde bile "Önceki bölümün Boss görevini tamamla" yazıyordu. Bu metin, görev sırasını açıklayan bir notla değiştirildi.
- Uygulama genelinde dinlenen Escape tuşu, kod yazarken bile profil ekranına atıyordu. Bu dinleyici kaldırıldı.
- Ders girişindeki kedi kartı tam yüksekliğe uzayıp boş görünüyordu. Artık üstte ve yapışkan.
- Kod ve boss görevlerinde Çalıştır/Gönder düğmeleri yapışkan bir çubukta; daha önce `.editor-box` öğesindeki `overflow:hidden` yapışkanlığı bozuyordu.
- Görev sekmeleri 4×2 düzende. Ayarlar ve profil ekranlarında başlık, odak ve menüdeki etkin öğe artık doğru.
- Türkçe arayüzdeki İngilizce metinler çevrildi: "Boss Challenge" → "Bölüm Boss'u", "Coding Arena" → "Kod Arenası". Boş arena rekorlarında "0%" yerine "—" görünüyor. Altbilgi cümlesi düzeltildi.
- Kariyer ekranındaki "—" yerine açıklayıcı boş durum metni geldi.

**Tipografi, renk ve tutarlılık**
- 11 px altındaki tüm `font-size` ve `font:` değerleri büyütüldü: 7–9.5 px → 11 px, 10–10.5 px → 12 px. Bunu artık bir test denetliyor.
- Tasarım sistemi dışındaki griler (`#777b8a`, `#7d8192`, `#85899a`, `#6f7594`…) `--ds-text-subtle` tokenına bağlandı.
- Opaklıkla soluklaştırılan metinler (kilitli başarımlar, ön koşul çipleri, kariyer basamakları) renk tokenıyla okunur hale geldi.
- Eyebrow (bölüm üst başlığı) artık tek stilde.
- Ders editörünün yazı boyutu 12 px'ten 14 px'e çıktı.

**Responsive**
- 1100 px altında kenar çubuğu `clamp(224px,18vw,260px)` genişlikte. Marka adı, menü ve profil yazıları tek satırda kalıyor.
- Dükkândaki taşma ve "Kombini kaydet" düğmesinin iki satıra kırılması düzeldi.
- Yetenek ağacının kenarına kaydırılabildiğini gösteren bir solma eklendi.

**Erişilebilirlik**
- Görünüm değişince odak h1'e gidiyor (WCAG 2.4.3), sayfa başlığı güncelleniyor ve sayfa başa kayıyor.
- Ayarlar > Görünüm: yazı boyutu %100/115/130/150. Ctrl+Artı/Eksi/0 da çalışıyor; paketli WebView2 penceresinde tarayıcı yakınlaştırması kapalı olduğu için bu gerekliydi (1.4.4). Ayrıca "Animasyonları azalt" seçeneği eklendi; CSS animasyonlarını, tüm JS animasyon modüllerini ve yumuşak kaydırmayı kapatıyor.
- Beş Monaco editörünün hepsinin `ariaLabel` değeri var. Cevap ve girdi alanlarında `aria-label`, mevcut görevde `aria-current="step"`, adı olan bir boss sekmesi var.
- Toast mesajları en az 4 saniye kalıyor ve metin uzadıkça daha uzun duruyor (2.2.1).
- 650 px altında menü etiketleri `display:none` yerine görsel olarak gizleniyor; ekran okuyucu onları hâlâ okuyabiliyor.
- Dil düğmesinin erişilebilir adı, düğmede görünen metni içeriyor (2.5.3).
- Terminal girişinde odak halkası var. Küçük dokunma hedefleri büyütüldü (2.5.8).

**Teknik**
- Başarısız bir **gizli** test artık girdisini ve beklenen çıktısını açıklamıyor; bu hem `/api/submit` hem çevrimdışı tanılama için geçerli. Yalnızca sayfada zaten gösterilen örnek test açıklanıyor.
- `/api/import` profili değiştirmeden önce veritabanının doğrulanmış bir yedeğini alıyor. Bozuk listeleri 400 hatası ve hata koduyla reddediyor; 18 listenin hepsi doğrulanıyor.
- Beklenmeyen 500 hataları `logs/server-errors.log` dosyasına yazılıyor (1 MB'ta döndürülüyor). İstemciye yalnızca genel bir mesaj ve bir olay kodu dönüyor; önceden istisna metni olduğu gibi gidiyordu.
- Yedekler tek dosya (`journal_mode=DELETE`) ve yollar `as_uri` ile açılıyor; `%`, `#` ve `&` karakterli yollar bu yüzden güvenli.
- Altı test sınıfı `DATA_ROOT`'u da geçici klasöre yönlendirip geri yüklüyor; daha önce proje klasörüne yedek yazıyorlardı.

Testler: `tests/test_ux_audit_fixes.py` (8), güncellenen `test_phase10_a11y_i18n.py`, `test_i18n_catalog.py`, `test_architecture.py`. Tam paket her turdan sonra çalıştırıldı: 1. tur sonrası 301 OK, 2. tur sonrası 301 OK.

## Hâlâ mevcut sorunlar

- **UI tutarlılığı (76):** `app.js` içinde hâlâ satır içi stiller ve tasarım sistemi dışı renkler var (örneğin `#8e94b0`, `#9095a7`). Sekme ve düğme bileşenleri bölümden bölüme farklı.
- **Renk ve tipografi (77):** Gradyan ve görsel üzerindeki metinlerin kontrastı ölçülemiyor (**TEST EDİLEMEDİ**).
- **Responsive (79):** 1920 px'te içerik dar ve yanlarda büyük boşluk kalıyor. Haritanın altında da geniş bir boşluk var.
- **Bölüm bütünlüğü (79):** İstatistik ve kariyer ekranları seyrek. Kariyerdeki "Portföyüm" başlığı panelin dışında. Menü, sayfa yolu ve başlık adları bazı bölümlerde farklı.
- **Erişilebilirlik (76):** Gerçek bir ekran okuyucuyla (NVDA/JAWS) test yapılmadı. CSS `zoom` ile Monaco'da imleç ve tıklama hizası denenmedi. Sekme kalıpları (ok tuşları, `tabpanel`) eksik.
- **Profesyonellik (77):** Ana sayfadaki büyük kartlarda boş dikey alan var. "Mira ·" çipi ders başlığında ikinci bir profil düğmesi gibi duruyor.
- **Teknik:**
  - Yedek budama bilerek yapılmadı; sahibinin kuralı "yedekleri silme".
  - Proje klasöründeki `backups/` altında testlerin eskiden bıraktığı 78 dosya duruyor. Git'e girmiyorlar ve silinmediler.
  - Görev sırası yalnızca arayüzde uygulanıyor; sunucu sadece bölüm ön koşulunu kontrol ediyor.
  - `server.py` tek dosyada ~2 400 satır, `app.js` ise tek satırlık devasa fonksiyonlardan oluşuyor.
- Atölye projelerinin testleri tasarım gereği sayfada açık. Bu yüzden `/api/project/submit` yanıtındaki beklenen çıktı ek bir sızıntı değil; Reality Checker da bu görüşe katıldı.

## Test edilemeyen alanlar

- Ekran okuyucu davranışı (NVDA/JAWS/Anlatıcı).
- Animasyonların akıcılığı (yalnızca kod ve kare hızı ölçümü var).
- Gradyan ve görsel üzerindeki metin kontrastı.
- Windows Yüksek Kontrast (`forced-colors`) modu.
- %400 yakınlaştırma.
- Paketli exe içinde Ctrl+Artı/Eksi; tarayıcıda test edildi.
- 15 renk teması (uygulamada yok).

## Geçiş kararı

**Aşama başarılı sayılmadı.** Dokuz görsel kriterden yedisi hâlâ 80'in altında (76–79). Kritik kullanılabilirlik ve responsive sorunları kapandı:

- yanlış kilit mesajı,
- profile atan Escape,
- ekran dışında kalan düğmeler,
- okunmayan küçük ve soluk yazılar,
- 980 px'te kırılan yerleşim.

Bir sonraki aşamaya geçmeden önce yapılması gerekenler:

- Gerçek bir ekran okuyucu testi (NVDA).
- 1920 px yerleşimi.
- Sekme ve düğme bileşenlerinin tek bir bileşene indirilmesi.
- Bu düzeltmelerin bağımsız olarak yeniden puanlanması.
