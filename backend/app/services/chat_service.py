import os
import pickle
from app.schemas.chat import ChatMessageResponse
from app.services.log_service import LogService
from app.schemas.system_log import SystemLogCreate
from sqlalchemy.orm import Session
from app.models.user import User, UserRole

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self._load_model()
        self._load_model()

    def _load_model(self):
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'ai', 'intent_model.pkl')
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)

    async def process_message(self, user: User, message: str) -> ChatMessageResponse:
        # Log the user's query using normal logs but with entity_type="CHAT_LOG"
        await LogService.create_log(
            db=self.db,
            action="CHAT_QUERY",
            user_id=user.id,
            entity_type="CHAT_LOG",
            entity_id=None,
            details={"message": message}
        )

        if not self.model:
            return ChatMessageResponse(
                intent="ERROR",
                message="Chatbot model_path bulunamadı veya yüklenemedi. Lütfen sistem yöneticisiyle iletişime geçin."
            )
            
        intent = self.model.predict([message.lower()])[0]
        
        # Log the predicted intent
        await LogService.create_log(
            db=self.db,
            action="CHAT_RESPONSE",
            user_id=user.id,
            entity_type="CHAT_LOG",
            entity_id=None,
            details={"intent": intent}
        )

        return self._generate_response(intent, user, message.lower())

    def _generate_response(self, intent: str, user: User, message_text: str) -> ChatMessageResponse:
        import re
        
        # Protect help/tour queries from being overridden to filters
        help_keywords = ["nasıl", "rehber", "kılavuz", "klavuz", "yardım", "ne işe", "öğren", "tanıt", "kullanırım", "çalışıyorsun"]
        if any(w in message_text for w in help_keywords) and len(message_text.split()) <= 5:
            intent = "SYSTEM_EXPLAIN"
            
        # Override intent to REPORT_FILTER if it seems like a filter but was misclassified
        is_report_filter = False
        if intent not in ["REPORT_FILTER", "REPORT_CREATE", "REPORT_EXPORT", "REPORT_PROPOSAL_VIEW", "SYSTEM_EXPLAIN"]:
            filter_keywords = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık", "onayland", "reddedil", "bekleyen", "taslak", "geçenlerde", "yakın zamanda", "son günlerde", "içinde", "dün", "bugün", "yazdığı", "eklediği", "içeren", "ait", "önce", "hafta", "ay", "son"]
            
            if ("rapor" in message_text or "faaliyet" in message_text or "proje" in message_text or "yazdığı" in message_text) and intent not in ["REPORTS_VIEW"]:
                is_report_filter = True
            elif intent not in ["SETTINGS_THEME_LIGHT", "SETTINGS_THEME_DARK", "SETTINGS_FONT_UP", "SETTINGS_FONT_DOWN", "SETTINGS_OPACITY"]:
                if any(w in message_text for w in filter_keywords) or re.search(r'\b(20[0-9]{2})\b', message_text):
                    is_report_filter = True
                else:
                    remove_words_test = ["bana", "lütfen", "göster", "ara", "bul", "listele", "getir", "aç", "git", "sayfası", "sayfasını", "sayfasına", "rapor", "raporu", "raporları", "raporlarımı", "raporlarım", "faaliyet", "faaliyetleri", "faaliyetlerimi", "tüm", "bütün", "birlikte", "yaptığımız", "yaptığım", "ortak", "olan"]
                    pattern = re.compile(r'\b(' + '|'.join(remove_words_test) + r')\b', re.IGNORECASE)
                    residual = pattern.sub('', message_text).strip()
                    residual = re.sub(r"'[a-zçiğüşö]+", "", residual, flags=re.IGNORECASE).strip()
                    if len(residual) >= 2 and intent not in ["USER_MANAGE", "UNIT_MANAGE", "INSTITUTION_MANAGE", "PROFILE_MANAGE", "LOG_VIEW", "SYSTEM_INFO"]:
                        is_report_filter = True
                        
        if is_report_filter:
            intent = "REPORT_FILTER"
                
        # Override intent to USER_MANAGE if it seems like a person/unit search
        if intent not in ["USER_MANAGE", "UNIT_MANAGE"]:
            chart_keywords = ["şema", "şemasında", "görünümünde", "görüntüsünde", "görüntüsü", "organizasyon"]
            search_keywords = ["bul", "ara", "kişisini", "kişisi", "personeli", "personel", "kullanıcısı"]
            if any(w in message_text for w in chart_keywords):
                intent = "USER_MANAGE"
            elif any(w in message_text for w in search_keywords) and "rapor" not in message_text and "faaliyet" not in message_text:
                intent = "USER_MANAGE"

        if intent == "REPORT_FILTER":
            import datetime
            today = datetime.datetime.now()
            
            search_msg = message_text
            
            # Extract year
            year = None
            year_match = re.search(r'\b(20[0-9]{2})\b', search_msg)
            if year_match:
                year = year_match.group(1)
                search_msg = search_msg.replace(year_match.group(0), " ")
                
            # Extract status
            status = None
            status_tr = "tüm"
            if "taslak" in search_msg:
                status = "DRAFT"
                status_tr = "taslak durumundaki"
                search_msg = search_msg.replace("taslak", " ")
            elif any(w in search_msg for w in ["onaylandı", "onaylanan", "onaylı", "onaylanmış"]):
                status = "APPROVED"
                status_tr = "onaylanmış"
                for w in ["onaylandı", "onaylanan", "onaylı", "onaylanmış"]: search_msg = search_msg.replace(w, " ")
            elif "reddedil" in search_msg or "reddedilen" in search_msg:
                status = "REJECTED"
                status_tr = "reddedilmiş"
                for w in ["reddedil", "reddedilmiş", "reddedildi", "reddedilen"]: search_msg = search_msg.replace(w, " ")
            elif "bekleyen" in search_msg or "onay bekliyor" in search_msg:
                status = "PENDING"
                status_tr = "onay bekleyen"
                for w in ["bekleyen", "onay bekleyen", "onay bekliyor"]: search_msg = search_msg.replace(w, " ")
            
            # Extract month
            month = None
            month_name_tr = ""
            month_map = {
                "ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "haziran": 6,
                "temmuz": 7, "ağustos": 8, "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12
            }
            
            if "geçen ayın" in search_msg:
                month = today.month - 1 if today.month > 1 else 12
                year = str(today.year if today.month > 1 else today.year - 1)
                for m_name, m_val in month_map.items():
                    if m_val == month: month_name_tr = m_name
                search_msg = search_msg.replace("geçen ayın", " ")
            else:
                for m_name, m_val in month_map.items():
                    if m_name in search_msg:
                        month = m_val
                        month_name_tr = m_name
                        search_msg = search_msg.replace(m_name, " ")
                        break
                if not month:
                    numeric_month_match = re.search(r'\b(1[0-2]|0?[1-9])\.\s*ay\w*', search_msg, flags=re.IGNORECASE)
                    if numeric_month_match:
                        month = int(numeric_month_match.group(1))
                        for m_name, m_val in month_map.items():
                            if m_val == month: month_name_tr = m_name
                        search_msg = search_msg.replace(numeric_month_match.group(0), " ")

            # Extract precise date ranges
            start_date = None
            end_date = None
            date_filter_tr = ""
            recent = None
            
            if "dün" in search_msg:
                past = today - datetime.timedelta(days=1)
                start_date = past.strftime("%Y-%m-%d")
                end_date = past.strftime("%Y-%m-%d")
                date_filter_tr = "Dün"
                search_msg = search_msg.replace("dün", " ")
            elif "bugün" in search_msg:
                start_date = today.strftime("%Y-%m-%d")
                end_date = today.strftime("%Y-%m-%d")
                date_filter_tr = "Bugün"
                search_msg = search_msg.replace("bugün", " ")
            elif "bu hafta" in search_msg:
                past = today - datetime.timedelta(days=7)
                start_date = past.strftime("%Y-%m-%d")
                end_date = today.strftime("%Y-%m-%d")
                date_filter_tr = "Son 7 gün"
                search_msg = search_msg.replace("bu hafta", " ")
            elif "bu ay" in search_msg:
                past = today - datetime.timedelta(days=30)
                start_date = past.strftime("%Y-%m-%d")
                end_date = today.strftime("%Y-%m-%d")
                date_filter_tr = "Son 30 gün"
                search_msg = search_msg.replace("bu ay", " ")
            elif "bu yıl" in search_msg:
                year = str(today.year)
                search_msg = search_msg.replace("bu yıl", " ")
            elif "geçen hafta" in search_msg:
                # O gün, ondan önceki ve sonraki 3 gün (7 gün önce merkezli)
                past_center = today - datetime.timedelta(days=7)
                start_date = (past_center - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
                end_date = (past_center + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
                date_filter_tr = "Geçen Hafta (7 günlük aralık)"
                search_msg = search_msg.replace("geçen hafta", " ")
            elif "geçen ay" in search_msg:
                # O gün merkezli 31 günlük işaretleme
                past_center = today - datetime.timedelta(days=30)
                start_date = (past_center - datetime.timedelta(days=15)).strftime("%Y-%m-%d")
                end_date = (past_center + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
                date_filter_tr = "Geçen Ay (31 günlük aralık)"
                search_msg = search_msg.replace("geçen ay", " ")
            else:
                days_ago = re.search(r'(\d+)\s*gün\s*önce', search_msg)
                if days_ago:
                    past = today - datetime.timedelta(days=int(days_ago.group(1)))
                    start_date = past.strftime("%Y-%m-%d")
                    end_date = past.strftime("%Y-%m-%d")
                    date_filter_tr = f"{days_ago.group(1)} gün önce"
                    search_msg = search_msg.replace(days_ago.group(0), " ")
                
                last_days = re.search(r'son\s*(\d+)\s*gün(de)?', search_msg)
                if last_days:
                    past = today - datetime.timedelta(days=int(last_days.group(1)))
                    start_date = past.strftime("%Y-%m-%d")
                    end_date = today.strftime("%Y-%m-%d")
                    date_filter_tr = f"Son {last_days.group(1)} gün"
                    search_msg = search_msg.replace(last_days.group(0), " ")
                    
                weeks_ago = re.search(r'(\d+)\s*hafta\s*önce', search_msg)
                if weeks_ago:
                    past = today - datetime.timedelta(days=int(weeks_ago.group(1))*7)
                    start_date = past.strftime("%Y-%m-%d")
                    end_date = past.strftime("%Y-%m-%d")
                    date_filter_tr = f"{weeks_ago.group(1)} hafta önce"
                    search_msg = search_msg.replace(weeks_ago.group(0), " ")
                    
                last_weeks = re.search(r'son\s*(\d+)\s*hafta(da)?', search_msg)
                if last_weeks:
                    past = today - datetime.timedelta(days=int(last_weeks.group(1))*7)
                    start_date = past.strftime("%Y-%m-%d")
                    end_date = today.strftime("%Y-%m-%d")
                    date_filter_tr = f"Son {last_weeks.group(1)} hafta"
                    search_msg = search_msg.replace(last_weeks.group(0), " ")
                    
                months_ago = re.search(r'(\d+)\s*ay\s*önce', search_msg)
                if months_ago:
                    past = today - datetime.timedelta(days=int(months_ago.group(1))*30)
                    start_date = past.strftime("%Y-%m-%d")
                    end_date = past.strftime("%Y-%m-%d")
                    date_filter_tr = f"{months_ago.group(1)} ay önce"
                    search_msg = search_msg.replace(months_ago.group(0), " ")
                    
                last_months = re.search(r'son\s*(\d+)\s*ay(da)?', search_msg)
                if last_months:
                    past = today - datetime.timedelta(days=int(last_months.group(1))*30)
                    start_date = past.strftime("%Y-%m-%d")
                    end_date = today.strftime("%Y-%m-%d")
                    date_filter_tr = f"Son {last_months.group(1)} ay"
                    search_msg = search_msg.replace(last_months.group(0), " ")
                    
                if not start_date and any(w in search_msg for w in ["geçenlerde", "yakın zamanda", "son günlerde"]):
                    recent = "30"
                    
            # Extract search text
            search_text = None
            search_match = re.search(r'içinde\s+[\'"]?(.+?)[\'"]?\s+(kelimesi\s+)?(geçen|bulunan|olan)', search_msg)
            if search_match:
                search_text = search_match.group(1).strip()
            else:
                remove_words_report = ["bana", "lütfen", "göster", "ara", "bul", "listele", "getir", "gertir", "ver", "aç", "git", "sayfası", "sayfasını", "sayfasına", "rapor", "raporu", "raporlar", "raporları", "raporlarımı", "raporlarım", "raporlarını", "raporlarına", "raporlarımızı", "proje", "projeleri", "projelerini", "projelerine", "faaliyet", "faaliyetleri", "faaliyetlerimi", "tüm", "bütün", "onaylanmış", "onaylandı", "onaylı", "reddedilmiş", "reddedildi", "bekleyen", "onay bekleyen", "onay bekliyor", "taslak", "geçenlerde", "yakın zamanda", "son günlerde", "içinde", "kelimesi", "geçen", "yazı", "eklediği", "ekleyen", "yazdığı", "yazan", "girilen", "içeren", "hazırlanan", "hazırlanmış", "kişisinin", "kullanıcısının", "personel", "kişi", "kullanıcı", "ait", "olan", "yapılan", "yaptığımız", "yaptığım", "birlikte", "ortak", "ay", "ayı", "ayına", "ayının", "yıl", "yılı", "yılına", "yılının", "ylının", "yılında", "ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık", "dün", "bugün", "bu", "önce", "hafta", "gün", "son", "günde", "haftada", "ayda", "ile", "ilgili", "dair", "hakkında", "işbirliği", "işbirlikleri", "işbirliğinde", "işbirliğiyle", "ortaklığı", "ortaklık", "nin", "nın", "nun", "nün", "in", "ın", "un", "ün", "da", "de", "ta", "te", "yönetici", "yöneticimin", "yöneticisinin", "yöneticisi"]
                pattern = re.compile(r'\b(' + '|'.join(remove_words_report) + r')\b', re.IGNORECASE)
                residual = pattern.sub('', search_msg).strip()
                residual = re.sub(r"'[a-zçiğüşö]+", "", residual, flags=re.IGNORECASE).strip()
                # Remove suffixes attached to numbers directly (e.g. 212nin -> 212)
                residual = re.sub(r'\b(\d+)(nin|nın|nun|nün|in|ın|un|ün|ya|ye|a|e|da|de|ta|te|dan|den|tan|ten)\b', r'\1', residual, flags=re.IGNORECASE).strip()
                residual = re.sub(r'\s+', ' ', residual).strip()
                if len(residual) >= 2:
                    search_text = residual
                
            trigger_str = "ACTION_FILTER_REPORTS"
            params = []
            if year:
                params.append(f"year={year}")
            if month:
                params.append(f"month={month}")
            if recent:
                params.append(f"recent={recent}")
            if start_date and end_date:
                params.append(f"startDate={start_date}")
                params.append(f"endDate={end_date}")
            if status:
                params.append(f"status={status}")
            if search_text:
                params.append(f"searchText={search_text}")
                
            if params:
                trigger_str += ":" + ",".join(params)
                
            msg = f"Tabii ki, hemen Faaliyet Raporları sayfasında istediğiniz aramayı gerçekleştiriyorum"
            details = []
            if search_text: details.append(f"'{search_text}'")
            if date_filter_tr: details.append(f"Oluşturulma Tarihi: {date_filter_tr}")
            if year: details.append(f"Yıl: {year}")
            if month: details.append(f"Ay: {month_name_tr}")
            if status: details.append(f"Durum: {status_tr}")
            if details:
                msg += f" ({', '.join(details)})."
            else:
                msg += "."
            msg += " Bu kriterlere uyan faaliyet raporlarını görebilmeniz için listeyi güncelliyorum ve sizi oraya yönlendiriyorum."
            
            is_person_search = any(w in message_text for w in ["kişisinin", "kişi", "kullanıcısının", "kullanıcı", "personel", "personeli", "yazdığı", "yazan", "eklediği", "ekleyen", "ait", "kim", "'in", "'ın", "'un", "'ün", "'nin", "'nın", "'nun", "'nün", "in ", "ın ", "un ", "ün ", "nin ", "nın ", "nun ", "nün "])
            is_institution_search = any(w in message_text for w in ["kurum", "kurumu", "kuruluş", "kuruluşu", "şirket", "şirketi", "işbirliği", "işbirlikleri", "ortaklığı", "ortaklık"])
            is_manager_search = any(w in message_text for w in ["yönetici", "yöneticimin", "yöneticisinin", "yöneticisi"])
            
            target_route = "/reports"
            if is_manager_search:
                target_route = "/reports?tab=manager"
            elif (is_person_search or is_institution_search) and search_text:
                target_route = "/reports?tab=unit"
            
            return ChatMessageResponse(
                intent=intent,
                message=msg,
                route=target_route,
                action_trigger=trigger_str if params else "ACTION_FILTER_REPORTS"
            )
        elif intent == "REPORT_CREATE":
            return ChatMessageResponse(
                intent=intent,
                message="Harika, yeni bir faaliyet kaydı girmek istiyorsunuz. İşleminizi kolaylaştırmak için sizi doğrudan Faaliyet Raporları sayfasına yönlendiriyorum. Lütfen sayfanın sağ üst köşesinde işaretlediğim 'Yeni Rapor Oluştur' butonuna tıklayarak form ekranını açın ve bilgileri doldurun.",
                route="/reports",
                action_trigger="HIGHLIGHT_CREATE_REPORT"
            )
        elif intent == "REPORTS_VIEW":
            return ChatMessageResponse(
                intent=intent,
                message="Geçmişte sisteme girdiğiniz tüm faaliyetlerinizi incelemek istediğinizi anlıyorum. Kendi raporlarınıza ve detaylarına ulaşabilmeniz için sizi Faaliyet Raporları sayfasına yönlendiriyorum. Eklediğiniz tüm faaliyetleri 'Kendi Raporlarım' sekmesi altında liste halinde görebilirsiniz.",
                route="/reports"
            )
        elif intent == "REPORT_EXPORT":
            return ChatMessageResponse(
                intent=intent,
                message="Raporlarınızı dışa aktarıp Excel formatında indirmek oldukça kolay. Sizi Faaliyet Raporları sayfasına yönlendiriyorum. Lütfen sayfanın üst tarafında işaretlediğim yeşil renkli 'Excel İndir' butonuna tıklayın. Eğer tablodan yandaki kutucuklarla sadece belirli satırları seçerseniz, sistem yalnızca o seçtiğiniz satırları Excel olarak indirecektir.",
                route="/reports",
                action_trigger="HIGHLIGHT_EXPORT_REPORT"
            )
        elif intent == "REPORT_PROPOSAL_VIEW":
            return ChatMessageResponse(
                intent=intent,
                message="Yönetici olarak size onaylanması için gönderilen teklifleri ve alt birimlerinizin raporlarını incelemek istiyorsunuz. Bu işlem için sizi Faaliyet Raporları sayfasına yönlendiriyorum. Lütfen işaretlediğim sarı çanlı 'Gelen Teklifler' butonuna tıklayarak onay bekleyen faaliyetleri görün.",
                route="/reports",
                action_trigger="HIGHLIGHT_PROPOSAL_VIEW"
            )
        elif intent == "USER_MANAGE":
            import re
            remove_words = ["bana", "lütfen", "göster", "ara", "bul", "kişisini", "kullanıcısını", "birimini", "personel", "personelini", "müdürlüğünü", "kurumunu", "listele", "getir", "aç", "git", "sayfası", "sayfasını", "sayfasına", "şema", "şemasında", "görünümünde", "görüntüsünde", "görüntüsü"]
            pattern = re.compile(r'\b(' + '|'.join(remove_words) + r')\b', re.IGNORECASE)
            search_text = pattern.sub('', message_text).strip()
            search_text = re.sub(r"'[a-zıiüuöoğşç]+", "", search_text, flags=re.IGNORECASE).strip()
            
            view_mode = "chart" if any(w in message_text for w in ["şema", "şemasında", "görünümünde", "görüntüsünde", "görüntüsü"]) else ""
            
            trigger_params = []
            if len(search_text) >= 2: trigger_params.append(f"searchText={search_text}")
            if view_mode: trigger_params.append(f"viewMode={view_mode}")
            
            trigger_str = f"ACTION_GLOBAL_SEARCH:{','.join(trigger_params)}" if trigger_params else "HIGHLIGHT_CREATE_USER"
            
            if user.role not in [UserRole.ADMIN, UserRole.USER_MANAGER] and len(search_text) < 2:
                return ChatMessageResponse(
                    intent=intent,
                    message="Kullanıcı ekleme, şifre sıfırlama veya yetki düzenleme gibi kullanıcı yönetimi işlemlerini yapmak için maalesef yetkiniz bulunmuyor. Sistem güvenliği gereği yalnızca Sistem Yöneticileri ve Personel Yöneticileri bu işlemi gerçekleştirebilir."
                )
            
            if len(search_text) >= 2:
                msg = f"'{search_text}' kişisi için aramayı başlatıyorum ve sizi Organizasyon Yapısı sayfasına yönlendiriyorum."
                route = "/units"
            else:
                msg = "Personel işlemleri yapmak istediğinizi anlıyorum. Kullanıcıları yönetmeniz ve yeni personel tanımlamanız için sizi Kullanıcılar sayfasına yönlendiriyorum. Sayfanın sağ üst köşesinde vurguladığım 'Yeni Kullanıcı Ekle' butonunu kullanarak işlemi başlatabilirsiniz."
                route = "/users"
            
            return ChatMessageResponse(
                intent=intent,
                message=msg,
                route=route,
                action_trigger=trigger_str
            )
        elif intent == "UNIT_MANAGE":
            import re
            remove_words = ["bana", "lütfen", "göster", "ara", "bul", "kişisini", "kullanıcısını", "birimini", "personel", "personelini", "müdürlüğünü", "kurumunu", "listele", "getir", "aç", "git", "sayfası", "sayfasını", "sayfasına", "organizasyon", "şemasını", "ağacında", "ağacı", "şema", "şemasında", "görünümünde", "görüntüsünde", "görüntüsü"]
            pattern = re.compile(r'\b(' + '|'.join(remove_words) + r')\b', re.IGNORECASE)
            search_text = pattern.sub('', message_text).strip()
            search_text = re.sub(r"'[a-zıiüuöoğşç]+", "", search_text, flags=re.IGNORECASE).strip()
            
            view_mode = "chart" if any(w in message_text for w in ["şema", "şemasında", "görünümünde", "görüntüsünde", "görüntüsü"]) else ""
            
            trigger_params = []
            if len(search_text) >= 2: trigger_params.append(f"searchText={search_text}")
            if view_mode: trigger_params.append(f"viewMode={view_mode}")
            
            trigger_str = f"ACTION_GLOBAL_SEARCH:{','.join(trigger_params)}" if trigger_params else ""
            
            if user.role != UserRole.ADMIN and len(search_text) < 2 and not view_mode:
                return ChatMessageResponse(
                    intent=intent,
                    message="Birim veya organizasyon şeması düzenleme yetkiniz bulunmuyor. Yalnızca sistem yöneticileri bu işlemi yapabilir."
                )
            
            msg = f"Organizasyon yapısı sayfasında '{search_text}' için aramayı başlatıyorum ve sizi oraya yönlendiriyorum." if len(search_text) >= 2 else "Birim ve organizasyon şeması işlemleri için Organizasyon Yapısı sayfasına yönlendiriliyorsunuz."
            if view_mode and len(search_text) < 2:
                msg = "Organizasyon yapısı şema görünümüne yönlendiriliyorsunuz."
            
            return ChatMessageResponse(
                intent=intent,
                message=msg,
                route="/units",
                action_trigger=trigger_str if trigger_str else None
            )
        elif intent == "INSTITUTION_MANAGE":
            if user.role != UserRole.ADMIN:
                return ChatMessageResponse(
                    intent=intent,
                    message="Kurum veya iştirak ekleme yetkiniz bulunmuyor. Yalnızca sistem yöneticileri bu işlemi yapabilir."
                )
            return ChatMessageResponse(
                intent=intent,
                message="İştirak ve dış kurumları yönetmek için Kurum ve Kuruluşlar sayfasına yönlendiriliyorsunuz.",
                route="/institutions",
                action_trigger="HIGHLIGHT_CREATE_INSTITUTION"
            )
        elif intent == "LOG_VIEW":
            if user.role != UserRole.ADMIN:
                return ChatMessageResponse(
                    intent=intent,
                    message="Sistem loglarını görüntüleme yetkiniz bulunmuyor. Yalnızca sistem yöneticileri bu sayfaya erişebilir."
                )
            return ChatMessageResponse(
                intent=intent,
                message="Sistem loglarını incelemek için Sistem Logları sayfasına yönlendiriliyorsunuz.",
                route="/logs"
            )
        elif intent == "SETTINGS_THEME_DARK":
            return ChatMessageResponse(
                intent=intent,
                message="Karanlık modu sizin için aktif ediyorum.",
                action_trigger="ACTION_THEME_DARK"
            )
        elif intent == "SETTINGS_THEME_LIGHT":
            return ChatMessageResponse(
                intent=intent,
                message="Aydınlık modu (açık tema) sizin için aktif ediyorum.",
                action_trigger="ACTION_THEME_LIGHT"
            )
        elif intent == "SETTINGS_FONT_UP" or intent == "SETTINGS_FONT_DOWN":
            import re
            match = re.search(r'\b(\d{1,3})\b', message_text)
            if match:
                size = int(match.group(1))
                return ChatMessageResponse(
                    intent=intent,
                    message=f"Yazı boyutunu {size}px olarak ayarlıyorum...",
                    action_trigger=f"ACTION_FONT_SET:{size}"
                )
                
            if intent == "SETTINGS_FONT_UP":
                return ChatMessageResponse(
                    intent=intent,
                    message="Yazı boyutunu sizin için büyütüyorum.",
                    action_trigger="ACTION_FONT_UP"
                )
            else:
                return ChatMessageResponse(
                    intent=intent,
                    message="Yazı boyutunu sizin için küçültüyorum.",
                    action_trigger="ACTION_FONT_DOWN"
                )
        elif intent == "SETTINGS_OPACITY":
            import re
            match = re.search(r'\b(\d{1,3})\b', message_text)
            if match:
                val = int(match.group(1))
                return ChatMessageResponse(
                    intent=intent,
                    message=f"Panel görünürlüğünü %{val} olarak ayarlıyorum...",
                    action_trigger=f"ACTION_OPACITY_SET:{val}"
                )
            else:
                return ChatMessageResponse(
                    intent=intent,
                    message="Panel görünürlük değerini değiştirmek için lütfen bir oran (ör. 50, 80) belirtin.",
                    action_trigger="HIGHLIGHT_PROFILE_MENU"
                )
        elif intent == "PROFILE_MANAGE":
            return ChatMessageResponse(
                intent=intent,
                message="Hesap bilgilerinizi ve şifrenizi sağ üst köşedeki profil menüsünden (kullanıcı ikonuna tıklayarak) güncelleyebilirsiniz.",
                action_trigger="HIGHLIGHT_PROFILE_MENU"
            )
        elif intent == "SYSTEM_INFO":
            return ChatMessageResponse(
                intent=intent,
                message="Merhaba! Ben Bursa Faaliyet Raporu asistanıyım. Kurum içi raporları doldurma, birim yönetimi veya excel çıktıları alma gibi işlemlerinizde size yardımcı olabilirim. Nasıl bir işlem yapmak istersiniz?"
            )
        elif intent == "SYSTEM_EXPLAIN":
            if any(w in message_text for w in ["nasıl", "rehber", "kılavuz", "klavuz", "yardım", "ne işe", "öğren", "tanıt", "kullanırım"]):
                return ChatMessageResponse(
                    intent=intent,
                    message="Sistemimizi daha iyi kullanabilmeniz için size küçük bir interaktif tur hazırladık. Arayüzümüzü ve temel fonksiyonları tanıtmak üzere Sistem Turu'nu başlatıyorum. Ekrandaki yönlendirmeleri takip edebilirsiniz.",
                    action_trigger="ACTION_START_TOUR"
                )
            if "kullanıcı" in message_text or "personel" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Kullanıcı Yönetimi, sisteme girecek olan personelleri tanımladığınız, şifrelerini ve yetkilerini ayarladığınız bölümdür."
                )
            elif "birim" in message_text or "organizasyon" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Birim (Organizasyon) Yönetimi, belediye içindeki müdürlüklerin ve daire başkanlıklarının hiyerarşik ağaç yapısında tanımlandığı bölümdür. Raporlar bu birimlere göre kırılımlanır."
                )
            elif "kurum" in message_text or "iştirak" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Kurum Yönetimi, belediye dışındaki iştiraklerin veya dış kurumların sisteme tanımlandığı bölümdür."
                )
            elif "rapor" in message_text or "faaliyet" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Faaliyet Raporları, kurumunuzun veya biriminizin gerçekleştirdiği işleri sisteme girdiğiniz, daha sonra üst birimlerin bunları onaylayarak konsolide (birleşik) Excel çıktıları alabildiği ana modüldür."
                )
            elif "içe aktar" in message_text or "yükle" in message_text or "import" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Excel'den İçe Aktarma: Daha önceden şablonumuza uygun olarak hazırladığınız faaliyet raporu kayıtlarını tek tek girmek yerine, Excel dosyasını sisteme yükleyerek toplu halde hızlıca sisteme eklemenizi sağlar."
                )
            elif "taslak" in message_text or "şablon" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Excel Taslağı İndir: Toplu rapor yüklemesi (içe aktarma) yapabilmeniz için sistemin kabul edeceği sütun başlıklarını ve yapıyı içeren boş bir örnek Excel şablonu indirmenizi sağlar."
                )
            elif "şema" in message_text or "ağaç" in message_text or "görünüm" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Organizasyon Görünümleri: Birimlerinizi 'Ağaç Görünümü' ile alt alta açılır listeler şeklinde veya 'Şema Görünümü' ile görsel bir soy ağacı (hiyerarşi) tablosu şeklinde inceleyebilirsiniz."
                )
            elif "alt birim" in message_text or "yeni birim" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Yeni Alt Birim Ekle: Seçtiğiniz müdürlük veya daire başkanlığının altına bağlı çalışan yeni bir alt departman eklemenizi sağlar."
                )
            elif "excel" in message_text or "pdf" in message_text or "indir" in message_text or "çıktı" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Çıktı Alma işlemleri: Seçtiğiniz birden fazla raporu üst kısımdaki butonla toplu olarak Excel'e aktarabilir, veya tablodaki her bir raporun yanındaki işlemler sütununda bulunan butona tıklayarak o raporun detaylarını tekil olarak PDF belgesi şeklinde indirebilirsiniz."
                )
            elif "log" in message_text or "kayıt" in message_text or "geçmiş" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Sistem Logları, platformda hangi kullanıcının hangi işlemi (rapor ekleme, şifre değiştirme vb.) saat kaçta yaptığını yöneticilerin takip edebildiği güvenlik amaçlı denetim kaydı bölümüdür."
                )
            elif "teklif" in message_text or "onay" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Gelen Teklifler, alt birimlerinizin sizin onayınıza sunduğu faaliyet raporlarıdır. Bu teklifleri inceleyebilir, onaylayabilir veya reddederek düzeltilmesi için geri gönderebilirsiniz."
                )
            elif "ayar" in message_text or "tema" in message_text or "yazı boyutu" in message_text or "karanlık mod" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Görünüm Ayarları, uygulamanın sizin gözünüzü yormaması için karanlık temaya (dark mode) geçiş yapabildiğiniz veya yazı fontu ve boyutunu kişiselleştirebildiğiniz alandır. Yaptığınız ayarlar kaydedilir ve her girişinizde hatırlanır."
                )
            elif "şifre" in message_text or "profil" in message_text:
                return ChatMessageResponse(
                    intent=intent,
                    message="Profil Yönetimi, sisteme giriş yaparken kullandığınız şifreyi güvenliğiniz için değiştirebileceğiniz bölümdür."
                )
            else:
                return ChatMessageResponse(
                    intent=intent,
                    message="Bu sistem, Bursa Büyükşehir Belediyesi ve iştiraklerinin yürüttüğü faaliyetlerin tek bir merkezden girilip, hiyerarşik onaya sunulduğu ve Excel olarak raporlanabildiği bir platformdur."
                )
        else:
            return ChatMessageResponse(
                intent="UNKNOWN",
                message="Bu isteğinizi tam olarak anlayamadım veya şu an desteklemiyorum. Ancak 'Faaliyet ekle', 'Excel indir', 'Kullanıcı ekle' veya 'Raporlarımı göster' diyerek benden yardım alabilirsiniz."
            )
