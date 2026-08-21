# Bursa Büyükşehir Belediyesi - Faaliyet Raporu Yönetim Sistemi

Bu doküman, Bursa Büyükşehir Belediyesi bünyesinde görev yapan personelin faaliyet raporlarını dijital ortamda kayıt altına almasını, yöneticilerin bu raporları hiyerarşik yapı içerisinde onaylama veya reddetme süreçlerini yönetmesini sağlayan kurumsal web uygulamasının teknik detaylarını içermektedir.

## 1. Sistemin Amacı ve Kapsamı

Faaliyet Raporu Yönetim Sistemi, kurum içi iş süreçlerinin şeffaflığını artırmayı, personel performans takibini kolaylaştırmayı ve kağıt israfını önlemeyi hedefleyen uçtan uca (end-to-end) bir dijital dönüşüm projesidir. Sistem, kurumun organizasyon şemasına (Daire Başkanlıkları, Şube Müdürlükleri ve Birimler) entegre çalışarak Rol Tabanlı Erişim Kontrolü (RBAC) sağlamaktadır.

## 2. Teknoloji Altyapısı

Sistem, yüksek performanslı ve güvenilir açık kaynak teknolojiler kullanılarak modern bir mimariyle tasarlanmıştır:

- **Sunucu (Backend):** FastAPI (Python 3.12+)
- **Veri Tabanı:** PostgreSQL (Asyncpg sürücüsü ile eşzamanlı asenkron işlemler)
- **Veri Tabanı Yöneticisi (ORM):** SQLAlchemy 2.0 (Async) & Alembic
- **İstemci (Frontend):** Angular 17+ (TypeScript)
- **Arayüz (UI) Kütüphanesi:** PrimeNG & PrimeFlex (SCSS)
- **Güvenlik ve Kimlik Doğrulama:** JWT (JSON Web Token) ve Bcrypt Hash algoritması

## 3. Sistem Kontrol ve Konfigürasyon Dosyaları

Sistemi devralacak teknik personelin (Sistem Yöneticisi / Geliştirici) uygulamanın temel davranışlarını ve görünümünü hızlıca yönetebilmesi adına yapılandırma parametreleri belirli dosyalarda merkezileştirilmiştir:

### 3.1. Sunucu Yapılandırması: `backend/app/core/config.py`
Bu dosya, sunucunun (Backend) sinir merkezidir. Uygulamanın veritabanı bağlantı metinleri (Connection String), JWT güvenlik anahtarları, token geçerlilik süreleri, CORS (Çapraz Kaynak Kaynak Paylaşımı) politikaları ve çevre değişkenleri (`.env`) bu dosya üzerinden yönetilmektedir. Veritabanı veya sunucu taşıma işlemlerinde değiştirilecek ilk noktadır.

### 3.2. Arayüz ve Tasarım Yapılandırması: `frontend/src/styles.scss`
Uygulamanın Kurumsal Kimlik (renk kodları, logo ebatları, tipografi, düğme ve menü tasarımları vb.) ayarları bu dosyanın en üst kısmında yer alan `:root` CSS Değişkenleri (CSS Variables) alanında toplanmıştır. Herhangi bir HTML/TS koduna müdahale edilmeden, sadece bu dosyadaki renk veya boyut değişkenleri güncellenerek tüm uygulamanın görsel teması saniyeler içinde değiştirilebilmektedir. Ayrıca modern **Glassmorphism (Şeffaflık ve Bulanıklık)** efekti sisteme entegre edilerek, kullanıcıların panellerin şeffaflık seviyesini veya sistem fontunu **Ayarlar** menüsü üzerinden dinamik (anlık) olarak değiştirebilmelerine olanak tanınmıştır.

### 3.3. Dinamik Kullanıcı Turu (Driver.js)
Sisteme yeni giriş yapan kullanıcıların ekranları daha kolay öğrenebilmeleri için `driver.js` tabanlı rehberli turlar eklenmiştir. Bu turlar; kullanıcının bulunduğu sayfaya (Örn: Raporlar, Organizasyon Yapısı vb.) göre değişmekte ve sayfadaki filtre, buton, tablo gibi ögeleri tek tek vurgulayarak ne işe yaradıklarını açıklamaktadır.

## 4. Kullanıcı Rolleri ve Yetki Matrisi

Sistem güvenliği, aşağıdaki dört temel rol üzerinden sağlanmaktadır:

1. **Standart Personel (USER):** Sadece kendi yöneticisi tarafından oluşturulmuş olan ilgili döneme ait faaliyet raporlarına "satır bazlı" faaliyet girişi yapar. Kendi eklediği faaliyet satırlarını güncelleyebilir ve silebilir. Yeni bir rapor dosyası oluşturamaz.
2. **Yönetici (MANAGER):** Kendisine bağlı çalışan personelin rapor girişi yapabilmesi için yeni dönem (Yıl/Ay) rapor dosyasını oluşturur. Ancak kendi oluşturduğu rapora doğrudan faaliyet ekleyemez; faaliyetlerini bir üst yöneticisinin oluşturduğu rapora girmek zorundadır. Astlarının girdiği faaliyet satırlarını tek tek inceler, onaylar veya "Red Nedeni" ile iade eder. Tüm satırlar onaylandığında, eksik veri girmeyen personelleri kontrol ederek raporu tamamen kapatır ve onaylanmış faaliyetleri bir üst yöneticisinin dosyasına (Aynı Yıl/Ay) aktarır.
3. **Kullanıcı Yöneticisi (USER_MANAGER):** "Kullanıcı Yönetimi" modülüne erişim sağlayarak yeni personel kaydı oluşturur ve mevcut personelin organizasyonel atamalarını günceller. Sistem yöneticilerine (ADMIN) müdahale etme yetkisi kısıtlanmıştır.
4. **Sistem Yöneticisi (ADMIN):** Uygulamadaki tüm rapor, organizasyon şeması (birimler) ve kullanıcı verileri üzerinde tam (Super User) okuma, yazma, güncelleme ve silme yetkisine sahiptir.

## 5. Uygulama Kurulumu ve Başlatma (Deployment)

Projeyi geliştirme veya üretim (Production) ortamında başlatmak için aşağıdaki prosedür takip edilmelidir:

### 5.1. Veri Tabanı Hazırlığı
- Sunucuda PostgreSQL servisi çalışır durumda olmalıdır.
- `bursa_faaliyet` (veya belirlenen) veritabanı şeması oluşturulmalıdır.
- İlgili veritabanı kimlik bilgileri (kullanıcı adı, şifre, port) `backend/app/core/config.py` dosyasına işlenmelidir.

### 5.2. Sunucu (Backend) Kurulumu
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows sistemler için
# source venv/bin/activate # Linux/Unix sistemler için

pip install -r requirements.txt
alembic upgrade head       # Veritabanı tablolarının (migration) oluşturulması
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
*(Sunucu hizmete girdiğinde API dokümantasyonuna `/docs` veya `/redoc` uç noktalarından erişilebilir.)*

### 5.3. İstemci (Frontend) Kurulumu
```bash
cd frontend
npm install                # Gerekli kütüphanelerin indirilmesi

# Geliştirme (Development) ortamı için:
npm run dev

# Üretim (Production) ortamı derlemesi için:
ng build
```
*(Üretim ortamı için oluşturulan statik dosyalar `dist/` klasöründe yer alır ve Nginx/Apache gibi bir web sunucusunda barındırılmalıdır.)*

## 6. Geliştirici Kılavuzu (Mimari Prensip)

Projeye yeni bir özellik entegre edileceği durumlarda, **Katmanlı Mimari (Layered Architecture)** prensiplerine sadık kalınması zorunludur:
- Veri modelleri `app/models/` dizininde SQLAlchemy kullanılarak tanımlanır.
- Veri doğrulama işlemleri `app/schemas/` dizininde Pydantic modelleri aracılığıyla yapılır.
- Doğrudan veritabanı (CRUD) işlemleri `app/repositories/` katmanından yönetilir.
- İş mantığı (Business Logic) `app/services/` katmanında işletilir.
- İstemci ile iletişim (Endpoint/Controller) `app/api/` katmanı üzerinden sağlanır.
