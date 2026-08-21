import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import make_pipeline

# Turkish training data for intents
DATA = [
    # REPORT_FILTER (Yeni Niyet: Filtreleme İstekleri)
    ("Bana 2023 onaylı raporları getirir misin", "REPORT_FILTER"),
    ("Geçen gün girdim baktım ama bulamadım, bana 2023 onaylı raporları getirir misin?", "REPORT_FILTER"),
    ("Sadece onaylanmış faaliyetlerimi görmek istiyorum", "REPORT_FILTER"),
    ("Taslak durumunda olan raporlarımı listele", "REPORT_FILTER"),
    ("Geçen sene yani 2023'te girdiğim reddedilmiş raporlara nasıl bakarım, filtreler misin", "REPORT_FILTER"),
    ("Onay bekleyen faaliyetleri filtrele", "REPORT_FILTER"),
    ("Bana 2024 yılına ait onaylanan faaliyet raporlarını göster", "REPORT_FILTER"),
    ("Dün taslak olarak bıraktığım raporları getir", "REPORT_FILTER"),
    ("2023 raporlarım", "REPORT_FILTER"),
    ("Sadece reddedildi durumundaki faaliyetleri görmek istiyorum", "REPORT_FILTER"),
    ("Bana geçmiş yılların 2022'ye ait onaylanmış olan faaliyet raporlarımı listeler misin rica etsem", "REPORT_FILTER"),
    ("Yalnızca taslaklar", "REPORT_FILTER"),
    ("ağustos ayına ait raporlar", "REPORT_FILTER"),
    ("geçenlerde girdiğim ağustos ayına ait raporları gösterirmisin", "REPORT_FILTER"),
    ("ocak ayı raporları", "REPORT_FILTER"),
    ("geçen aya ait faaliyetlerim", "REPORT_FILTER"),
    ("sadece ekim ayında oluşturduklarımı listele", "REPORT_FILTER"),
    ("temmuz ayına ait faaliyet raporlarımı getir", "REPORT_FILTER"),
    ("içinde test kelimesi geçen onaylanmış ekim ayı raporlarımı göster", "REPORT_FILTER"),
    ("içinde bursa geçen onay bekleyen raporlar", "REPORT_FILTER"),
    ("içinde ihale kelimesi geçen taslak raporlarım", "REPORT_FILTER"),
    ("geçenlerde oluşturduğum ve içinde park geçen faaliyetler", "REPORT_FILTER"),
    
    # REPORT_CREATE
    ("Yeni rapor ekle", "REPORT_CREATE"),
    ("Faaliyet girmek istiyorum", "REPORT_CREATE"),
    ("Nasıl rapor oluştururum", "REPORT_CREATE"),
    ("Faaliyet raporu ekle", "REPORT_CREATE"),
    ("Yeni kayıt oluştur", "REPORT_CREATE"),
    ("Rapor formunu aç", "REPORT_CREATE"),
    ("Kendi raporuma satır ekle", "REPORT_CREATE"),
    ("Satır eklemek istiyorum", "REPORT_CREATE"),
    ("Bugün yeni bir faaliyet gerçekleştirdim bunu sisteme nasıl girebilirim?", "REPORT_CREATE"),
    ("Geçen hafta yaptığım bir işi yeni bir rapor olarak eklemek istiyorum sayfayı açar mısın", "REPORT_CREATE"),
    
    # REPORTS_VIEW
    ("Raporlarımı göster", "REPORTS_VIEW"),
    ("Faaliyetlerimi nerede bulurum", "REPORTS_VIEW"),
    ("Girdiğim verileri gör", "REPORTS_VIEW"),
    ("Rapor listesini aç", "REPORTS_VIEW"),
    ("Tüm faaliyetlerim", "REPORTS_VIEW"),
    ("Eski raporlar", "REPORTS_VIEW"),
    ("Yazdığım raporlar nerede", "REPORTS_VIEW"),
    ("Şimdiye kadar sisteme girdiğim tüm faaliyet raporlarının olduğu listeyi görmek istiyorum", "REPORTS_VIEW"),
    
    # REPORT_EXPORT
    ("Raporu excel olarak indir", "REPORT_EXPORT"),
    ("Excel'e nasıl aktarırım", "REPORT_EXPORT"),
    ("Excel çıktısı al", "REPORT_EXPORT"),
    ("Raporu dışa aktar", "REPORT_EXPORT"),
    ("Tabloyu indir", "REPORT_EXPORT"),
    ("Ekranda gördüğüm bu rapor listesini bilgisayarıma excel dosyası olarak nasıl indirebilirim", "REPORT_EXPORT"),
    
    # REPORT_PROPOSAL_VIEW
    ("Gelen teklifler", "REPORT_PROPOSAL_VIEW"),
    ("Bana gönderilen faaliyetler", "REPORT_PROPOSAL_VIEW"),
    ("Yöneticimden gelen rapor", "REPORT_PROPOSAL_VIEW"),
    ("Onay bekleyen teklifler", "REPORT_PROPOSAL_VIEW"),
    ("Teklifleri nerede görürüm", "REPORT_PROPOSAL_VIEW"),
    ("Birimimdeki çalışanların bana onay için gönderdiği faaliyet tekliflerini nereden görüp onaylayabilirim", "REPORT_PROPOSAL_VIEW"),
    
    # USER_MANAGE
    ("Kullanıcı ekle", "USER_MANAGE"),
    ("Personel tanımla", "USER_MANAGE"),
    ("Şifre sıfırla", "USER_MANAGE"),
    ("Kullanıcı yönetimi", "USER_MANAGE"),
    ("Yeni kullanıcı", "USER_MANAGE"),
    ("Kullanıcıları nerede bulurum", "USER_MANAGE"),
    ("Aktif pasif yap", "USER_MANAGE"),
    ("Belediyemizde yeni işe başlayan bir personel var, ona sisteme giriş yapabilmesi için yeni bir kullanıcı hesabı açmak istiyorum", "USER_MANAGE"),
    
    # UNIT_MANAGE
    ("Birim ekle", "UNIT_MANAGE"),
    ("Organizasyon şeması", "UNIT_MANAGE"),
    ("Yeni müdürlük tanımla", "UNIT_MANAGE"),
    ("Birim ağacı", "UNIT_MANAGE"),
    ("Birim listesi", "UNIT_MANAGE"),
    ("Hiyerarşi şeması", "UNIT_MANAGE"),
    ("Belediyemizin organizasyon şemasını görmek ve yeni bir daire başkanlığı tanımlamak istiyorum", "UNIT_MANAGE"),
    
    # INSTITUTION_MANAGE
    ("Kurum ekle", "INSTITUTION_MANAGE"),
    ("Dış kurumlar", "INSTITUTION_MANAGE"),
    ("İştirakler", "INSTITUTION_MANAGE"),
    ("Yeni kurum", "INSTITUTION_MANAGE"),
    ("Kurum yönetimi", "INSTITUTION_MANAGE"),
    ("Belediyeye bağlı yeni bir iştirak şirketi kuruldu, bunu dış kurum olarak sisteme nasıl eklerim", "INSTITUTION_MANAGE"),
    
    # LOG_VIEW
    ("Sistem logları", "LOG_VIEW"),
    ("Kayıtları gör", "LOG_VIEW"),
    ("Kim ne yapmış", "LOG_VIEW"),
    ("İşlem geçmişi", "LOG_VIEW"),
    ("Sistem kayıtları", "LOG_VIEW"),
    ("Bugün sistemde kimlerin hangi işlemleri yaptığını ve geçmiş log kayıtlarını güvenlik amacıyla incelemek istiyorum", "LOG_VIEW"),
    
    # SYSTEM_EXPLAIN
    ("Faaliyet raporu nedir", "SYSTEM_EXPLAIN"),
    ("Kullanıcı yönetimi ne işe yarar", "SYSTEM_EXPLAIN"),
    ("Bu sistemin amacı ne", "SYSTEM_EXPLAIN"),
    ("Birim nedir", "SYSTEM_EXPLAIN"),
    ("Kurum tanımlamak ne demek", "SYSTEM_EXPLAIN"),
    ("Neyi raporluyoruz", "SYSTEM_EXPLAIN"),
    ("Birim yönetimi nedir", "SYSTEM_EXPLAIN"),
    ("İştirak nedir", "SYSTEM_EXPLAIN"),
    ("Sistem nasıl çalışır", "SYSTEM_EXPLAIN"),
    ("Ne işe yarar", "SYSTEM_EXPLAIN"),
    ("Nedir bu", "SYSTEM_EXPLAIN"),
    ("PDF indir ne oluyor", "SYSTEM_EXPLAIN"),
    ("PDF indir ne işe yarıyor", "SYSTEM_EXPLAIN"),
    ("Excel indirmek nedir", "SYSTEM_EXPLAIN"),
    ("Loglar ne işe yarar", "SYSTEM_EXPLAIN"),
    ("Gelen teklifler nedir", "SYSTEM_EXPLAIN"),
    ("Şema görünümü ne işe yarıyor", "SYSTEM_EXPLAIN"),
    ("Ağaç görünümü nedir", "SYSTEM_EXPLAIN"),
    ("Yeni alt birim nasıl eklenir", "SYSTEM_EXPLAIN"),
    ("Sisteme yeni girdim ama faaliyet raporunun tam olarak ne anlama geldiğini ve nasıl işlediğini bana açıklar mısın?", "SYSTEM_EXPLAIN"),
    ("Lütfen bana birim yönetiminin amacını ve organizasyon şemasının nasıl çalıştığını detaylı bir şekilde anlat", "SYSTEM_EXPLAIN"),
    ("Gelen teklifler diye bir buton var, bunun tam olarak ne işe yaradığını merak ediyorum açıklar mısın", "SYSTEM_EXPLAIN"),
    
    # SYSTEM_INFO
    ("Bursa faaliyet raporu", "SYSTEM_INFO"),
    ("Bu sistem", "SYSTEM_INFO"),
    ("Merhaba", "SYSTEM_INFO"),
    ("Selam", "SYSTEM_INFO"),
    ("Sen kimsin", "SYSTEM_INFO"),
    ("Neler yapabilirsin", "SYSTEM_INFO"),
    ("Bana yardım et", "SYSTEM_INFO"),
    
    # SETTINGS_THEME_DARK
    ("Karanlık mod", "SETTINGS_THEME_DARK"),
    ("Gece modu", "SETTINGS_THEME_DARK"),
    ("Koyu tema", "SETTINGS_THEME_DARK"),
    ("Karanlık moda geç", "SETTINGS_THEME_DARK"),
    ("Siyah tema", "SETTINGS_THEME_DARK"),
    
    # SETTINGS_THEME_LIGHT
    ("Aydınlık mod", "SETTINGS_THEME_LIGHT"),
    ("Gündüz modu", "SETTINGS_THEME_LIGHT"),
    ("Açık tema", "SETTINGS_THEME_LIGHT"),
    ("Aydınlık moda geç", "SETTINGS_THEME_LIGHT"),
    ("Beyaz tema", "SETTINGS_THEME_LIGHT"),
    
    # SETTINGS_FONT_UP
    ("Yazı boyutunu büyüt", "SETTINGS_FONT_UP"),
    ("Yazılar küçük", "SETTINGS_FONT_UP"),
    ("Metinleri büyüt", "SETTINGS_FONT_UP"),
    ("Daha büyük yazı", "SETTINGS_FONT_UP"),
    ("Yazı boyutunu arttır", "SETTINGS_FONT_UP"),
    ("Fontu büyüt", "SETTINGS_FONT_UP"),
    ("Metin boyutunu arttır", "SETTINGS_FONT_UP"),
    ("Yazıları arttır", "SETTINGS_FONT_UP"),
    
    # SETTINGS_FONT_DOWN
    ("Yazı boyutunu küçült", "SETTINGS_FONT_DOWN"),
    ("Yazılar büyük", "SETTINGS_FONT_DOWN"),
    ("Metinleri küçült", "SETTINGS_FONT_DOWN"),
    ("Daha küçük yazı", "SETTINGS_FONT_DOWN"),
    
    # SETTINGS_OPACITY
    ("Panel görünürlüğü", "SETTINGS_OPACITY"),
    ("Görünürlüğü değiştir", "SETTINGS_OPACITY"),
    ("Görünürlük ayarı", "SETTINGS_OPACITY"),
    ("Paneli şeffaf yap", "SETTINGS_OPACITY"),
    ("Görünürlüğü arttır", "SETTINGS_OPACITY"),
    ("Panel görünürlüğünü azalt", "SETTINGS_OPACITY"),
    ("Görünürlüğü 50 yap", "SETTINGS_OPACITY"),
    
    # PROFILE_MANAGE
    ("Şifremi nasıl değiştiririm", "PROFILE_MANAGE"),
    ("Hesap bilgilerim", "PROFILE_MANAGE"),
    ("Profilimi düzenle", "PROFILE_MANAGE"),
    ("Şifre güncelle", "PROFILE_MANAGE"),
]

def train_model():
    texts = [item[0].lower() for item in DATA]
    labels = [item[1] for item in DATA]
    
    # Create pipeline with TF-IDF and SVM
    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2)),
        LinearSVC(C=1.0, class_weight='balanced', dual="auto")
    )
    
    model.fit(texts, labels)
    
    # Save model
    model_dir = os.path.join(os.path.dirname(__file__), 'app', 'models', 'ai')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'intent_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    print(f"Model successfully trained and saved to {model_path}")
    
    # Test predictions
    test_queries = [
        "Yeni bir rapor gireceğim",
        "Kullanıcıları nereden ekliyorum",
        "Excel indirmek istiyorum",
        "İştirak kurumunu nasıl tanımlarım"
    ]
    
    print("\nTest Predictions:")
    for query in test_queries:
        pred = model.predict([query.lower()])[0]
        print(f"'{query}' -> {pred}")

if __name__ == '__main__':
    train_model()
