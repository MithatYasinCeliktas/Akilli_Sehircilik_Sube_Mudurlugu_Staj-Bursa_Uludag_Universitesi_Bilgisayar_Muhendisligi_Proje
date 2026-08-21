import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MenuItem, MessageService } from 'primeng/api';
import { MenuModule } from 'primeng/menu';
import { ButtonModule } from 'primeng/button';
import { SidebarModule } from 'primeng/sidebar';
import { SliderModule } from 'primeng/slider';
import { DropdownModule } from 'primeng/dropdown';
import { TooltipModule } from 'primeng/tooltip';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { OverlayPanelModule } from 'primeng/overlaypanel';
import { BadgeModule } from 'primeng/badge';
import { InputSwitchModule } from 'primeng/inputswitch';
import { AuthService } from '../../../core/services/auth.service';
import { UserService } from '../../../core/services/user.service';
import { NotificationService } from '../../../core/services/notification.service';
import { IdleService } from '../../../core/services/idle.service';
import { ReportService } from '../../../core/services/report.service';
import { User } from '../../../core/models/user.model';
import { Notification } from '../../../core/models/notification.model';
import { SettingsService, AppSettings } from '../../../core/services/settings.service';
import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MenuModule,
    ButtonModule,
    SidebarModule,
    SliderModule,
    DropdownModule,
    TooltipModule,
    DialogModule,
    InputTextModule,
    OverlayPanelModule,
    BadgeModule,
    InputSwitchModule
  ],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss'],
  providers: [MessageService]
})
export class NavbarComponent implements OnInit {
  currentUser: User | null = null;
  userMenuItems: MenuItem[] = [];
  
  displaySettings: boolean = false;
  currentSettings!: AppSettings;
  fontOptions = [
    { label: 'Outfit (Varsayılan)', value: "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" },
    { label: 'Inter', value: "'Inter', sans-serif" },
    { label: 'Roboto', value: "'Roboto', sans-serif" },
    { label: 'Open Sans', value: "'Open Sans', sans-serif" },
  ];
  
  // Opaklık değeri 0-1 arası (slider için 0-100 kullanıp 100'e böleceğiz)
  sliderOpacity: number = 40;
  
  isDarkMode: boolean = false;
  
  displayPasswordDialog: boolean = false;
  passwordForm!: FormGroup;
  passwordLoading: boolean = false;

  unreadCount: number = 0;
  notifications: Notification[] = [];

  constructor(
    private authService: AuthService,
    private userService: UserService,
    private router: Router,
    private settingsService: SettingsService,
    private fb: FormBuilder,
    private messageService: MessageService,
    private notificationService: NotificationService,
    private reportService: ReportService,
    private idleService: IdleService
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      this.initUserMenu();
      if (user && user.ui_settings) {
        this.settingsService.setSettingsFromBackend(user.ui_settings);
        this.currentSettings = this.settingsService.getSettings();
        this.sliderOpacity = Math.round(this.currentSettings.panelOpacity * 100);
        this.isDarkMode = this.currentSettings.theme === 'dark';
      }
      if (user) {
        this.loadUnreadCount();
      }
    });
    
    this.currentSettings = this.settingsService.getSettings();
    this.sliderOpacity = Math.round(this.currentSettings.panelOpacity * 100);
    this.isDarkMode = this.currentSettings.theme === 'dark';
    this.initPasswordForm();

    this.settingsService.openSettingsPanel$.subscribe(() => {
      this.currentSettings = this.settingsService.getSettings();
      this.sliderOpacity = Math.round(this.currentSettings.panelOpacity * 100);
      this.isDarkMode = this.currentSettings.theme === 'dark';
      this.displaySettings = true;
    });

    this.settingsService.startTour$.subscribe(() => {
      this.startTour();
    });
  }

  private initPasswordForm(): void {
    this.passwordForm = this.fb.group({
      newPassword: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required]]
    }, { validators: this.passwordMatchValidator });
  }

  private passwordMatchValidator(g: FormGroup) {
    return g.get('newPassword')?.value === g.get('confirmPassword')?.value
      ? null : { mismatch: true };
  }

  private initUserMenu(): void {
    this.userMenuItems = [
      {
        label: this.currentUser?.full_name || 'Kullanıcı',
        items: [
          {
            label: 'Şifre Değiştir',
            icon: 'pi pi-key',
            command: () => this.showPasswordDialog()
          },
          {
            label: 'Oturumu Kapat',
            icon: 'pi pi-power-off',
            command: () => this.logout()
          }
        ]
      }
    ];
  }
  
  showPasswordDialog(): void {
    this.passwordForm.reset();
    this.displayPasswordDialog = true;
  }

  changePassword(): void {
    if (this.passwordForm.invalid || !this.currentUser) {
      this.passwordForm.markAllAsTouched();
      return;
    }

    this.passwordLoading = true;
    const newPassword = this.passwordForm.get('newPassword')?.value;

    this.userService.updateUser(this.currentUser.id, { password: newPassword }).subscribe({
      next: () => {
        this.passwordLoading = false;
        this.displayPasswordDialog = false;
        this.messageService.add({severity: 'success', summary: 'Başarılı', detail: 'Şifreniz başarıyla güncellendi.'});
      },
      error: () => {
        this.passwordLoading = false;
        this.messageService.add({severity: 'error', summary: 'Hata', detail: 'Şifre güncellenirken bir hata oluştu.'});
      }
    });
  }

  showSettings(): void {
    this.displaySettings = true;
  }
  
  onSettingChange(): void {
    this.currentSettings.theme = this.isDarkMode ? 'dark' : 'light';
    this.settingsService.updateSettings({
      panelOpacity: this.sliderOpacity / 100,
      fontFamily: this.currentSettings.fontFamily,
      fontSize: this.currentSettings.fontSize,
      idleTimeoutMinutes: this.currentSettings.idleTimeoutMinutes,
      theme: this.currentSettings.theme
    });
    this.idleService.resetTimer();
  }

  saveSettings(): void {
    if (!this.currentUser) return;
    this.userService.updateUser(this.currentUser.id, { ui_settings: this.currentSettings }).subscribe({
      next: () => {
        // Profil bilgisini (ve içindeki ui_settings'i) sessionStorage'a ve auth state'ine yansıt
        this.authService.loadUserProfile().subscribe(() => {
          this.messageService.add({severity: 'success', summary: 'Başarılı', detail: 'Ayarlarınız başarıyla kaydedildi.'});
          this.displaySettings = false;
        });
      },
      error: () => {
        this.messageService.add({severity: 'error', summary: 'Hata', detail: 'Ayarlar kaydedilirken bir hata oluştu.'});
      }
    });
  }

  resetSettings(): void {
    const defaultSet = this.settingsService.getDefaultSettings();
    this.currentSettings = { ...defaultSet };
    this.sliderOpacity = Math.round(this.currentSettings.panelOpacity * 100);
    this.isDarkMode = this.currentSettings.theme === 'dark';
    this.settingsService.updateSettings(this.currentSettings);
    
    if (this.currentUser) {
      this.userService.updateUser(this.currentUser.id, { ui_settings: this.currentSettings }).subscribe({
        next: () => {
          this.messageService.add({severity: 'info', summary: 'Sıfırlandı', detail: 'Ayarlar varsayılana döndürüldü.'});
        }
      });
    }
  }

  startTour(): void {
    const currentUrl = this.router.url;
    const basePath = currentUrl.split('?')[0]; // Query parametrelerini yoksay
    let steps: any[] = [];

    if (basePath === '/reports') {
      const isVisible = (selector: string): boolean => {
        const el = document.querySelector(selector) as HTMLElement;
        return !!el && (el.offsetWidth > 0 || el.offsetHeight > 0);
      };

      steps = [
        { popover: { title: 'Faaliyet Raporları Yönetimi', description: 'Hoş geldiniz! Bu ekranda, kurumunuzun faaliyet raporlarını süzebilir ve durumlarını anlık olarak takip edebilirsiniz. Size sistemin ana hatlarını kısaca tanıtayım.', side: "bottom", align: 'start' }},
        { element: '.p-tabview-nav', popover: { title: 'Rapor Kategorileri', description: 'Raporlarınızı sekmeler halinde görebilirsiniz. İlk sekmede sizin yazdığınız raporlar yer alırken, diğer sekmelerde onayınızdaki veya sizinle paylaşılan raporlar bulunur.', side: "bottom", align: 'start' }}
      ];

      if (isVisible('button.p-button-success.p-button-outlined')) {
          steps.push({ element: 'button.p-button-success.p-button-outlined', popover: { title: 'Excel Çıktısı', description: 'Ekranda listelenen veya kutucuklardan seçtiğiniz raporları toplu olarak bir Excel dosyasına aktarıp bilgisayarınıza indirebilirsiniz.', side: "bottom", align: 'start' }});
      }

      if (isVisible('button.p-button-primary')) {
          steps.push({ element: 'button.p-button-primary', popover: { title: 'Yeni Rapor', description: 'Bu butona basarak yepyeni bir faaliyet raporu formu açabilirsiniz.', side: "left", align: 'start' }});
      }

      // Check for datatable that is actually visible
      if (isVisible('.p-datatable-wrapper')) {
          steps.push({ element: '.p-datatable-wrapper', popover: { title: 'Detaylı Veri Tablosu', description: 'Raporların özetini, oluşturulma zamanını ve durumunu buradan inceleyebilirsiniz. Sağ taraftaki işlem butonlarıyla (kalem vb.) detaylara girebilirsiniz.', side: "top", align: 'start' }});
      }

      if (isVisible('input[placeholder="Yıl"]')) {
          steps.push({ element: 'input[placeholder="Yıl"]', popover: { title: 'Yıla Göre Daralt', description: 'Raporlar arasından sadece belirli bir yıla ait olanları getirmek isterseniz burayı kullanın.', side: "bottom", align: 'start' }});
      }
      if (isVisible('input[placeholder="Ay"]')) {
          steps.push({ element: 'input[placeholder="Ay"]', popover: { title: 'Aylık Dağılım', description: 'Yıl seçtikten sonra, sadece belirli bir ayda girilmiş olan verileri süzmek için ay seçimi yapabilirsiniz.', side: "bottom", align: 'start' }});
      }
      if (isVisible('input[placeholder="Arama metni..."]')) {
          steps.push({ element: 'input[placeholder="Arama metni..."]', popover: { title: 'Metin Arama (Searchbar)', description: 'İçerikte kelime veya cümle aramak için bu alanı kullanabilirsiniz.', side: "bottom", align: 'start' }});
      }
      if (isVisible('p-dropdown')) {
          steps.push({ element: 'p-dropdown', popover: { title: 'Süreç Takibi', description: 'Durumu onay bekleyen veya reddedilen raporları filtreleyerek iş yükünüzü yönetin.', side: "bottom", align: 'start' }});
      }

      steps.push({ popover: { title: 'Tur Bitti', description: 'Filtreleri kombinleyerek aradığınızı çok daha hızlı bulabilirsiniz. İyi çalışmalar!', side: "bottom", align: 'start' }});
    } else if (basePath.startsWith('/reports/')) {
      steps = [
        { popover: { title: 'Rapor Detay Ekranı', description: 'Buradan faaliyet raporunuzun detaylarını inceleyebilir, form alanlarını doldurarak raporunuzu güncelleyebilirsiniz.', side: "bottom", align: 'start' }}
      ];
    } else if (basePath.startsWith('/units')) {
      steps = [
        { popover: { title: 'Organizasyon Şeması', description: 'Burası kurumumuzun tüm hiyerarşik organizasyon yapısını görüntülediğiniz, devasa bir aile ağacı ekranıdır.', side: "bottom", align: 'start' }},
        { element: 'input[placeholder="Birim veya Personel Ara..."]', popover: { title: 'Birim Arama Modülü', description: 'Aradığınız birimi (Örn: Bilgi İşlem) hızlıca bulmak için buraya yazmanız yeterli.', side: "bottom", align: 'start' }},
        { element: 'p-selectbutton', popover: { title: 'Görünüm Seçenekleri', description: 'Buradan görünümü Liste veya Etkileşimli Şema olarak değiştirebilirsiniz. Şema görünümündeyken mouse tekerleğiyle yakınlaşıp uzaklaşabilir, boşluğa tıklayarak şemayı sürükleyebilirsiniz.', side: "bottom", align: 'start' }},
        { popover: { title: 'Hızlı Yakınlaşma', description: 'İpucu: Şema görünümündeyken herhangi bir birim kutusuna çift tıklarsanız, kamera otomatik olarak o birime odaklanacaktır.', side: "bottom", align: 'start' }},
        { popover: { title: 'Tur Bitti', description: 'Birimleri incelemeye hemen başlayabilirsiniz.', side: "bottom", align: 'start' }}
      ];
    } else if (currentUrl.includes('/institutions')) {
      steps = [
        { popover: { title: 'Kurum ve Kuruluş Rehberi', description: 'Bu sayfada, ortak koordinasyon yürüttüğümüz diğer kurumların ve kuruluşların listesini yönetiyoruz.', side: "bottom", align: 'start' }},
        { element: '.p-datatable-wrapper', popover: { title: 'Kurumlar Tablosu', description: 'Sistemde kayıtlı olan tüm dış veya iç iştirak kurumlarını, aktiflik durumlarıyla beraber buradan görebilirsiniz.', side: "top", align: 'start' }},
        { element: 'button.p-button-primary', popover: { title: 'Kurum Ekleme', description: 'Eğer çalışmakta olduğunuz yeni bir dış kurum varsa, herkes gibi siz de "Yeni Kurum Ekle" butonuyla listeye dahil edebilirsiniz.', side: "bottom", align: 'start' }},
        { popover: { title: 'Yetkilendirme Kuralı', description: 'Önemli: Eklediğiniz kurumları sadece siz silebilir veya güncelleyebilirsiniz. Başkalarının eklediklerini sadece görebilirsiniz.', side: "bottom", align: 'start' }},
        { popover: { title: 'Tur Bitti', description: 'Şimdi kurum eklemeyi deneyebilirsiniz.', side: "bottom", align: 'start' }}
      ];
    } else {
      steps = [
        { popover: { title: 'Bursa Büyükşehir Belediyesi', description: 'Faaliyet Raporu Sistemine hoş geldiniz! Sizi kısaca gezdireyim.', side: "bottom", align: 'start' }},
        { element: '.sidebar-bg', popover: { title: 'Ana Menü (Navigasyon)', description: 'Tüm modüllere (Raporlar, Organizasyon Şeması, Kurumlar) bu yan menü üzerinden güvenle geçiş yapabilirsiniz.', side: "right", align: 'start' }},
        { element: '.btn-settings', popover: { title: 'Kişiselleştirme', description: 'Gözünüzü yormaması için "Karanlık Mod" açabilir, yazı tipi boyutunu büyütebilir veya panel şeffaflıklarını zevkinize göre ayarlayabilirsiniz.', side: "bottom", align: 'end' }},
        { element: 'p-menu', popover: { title: 'Profil ve Bildirimler', description: 'Sağ üst köşeden gelen kutunuzu (bildirimler) kontrol edebilir ve kullanıcı şifrenizi güvenli bir şekilde değiştirebilirsiniz.', side: "bottom", align: 'end' }},
        { popover: { title: 'Tur Bitti', description: 'Sistemi dilediğiniz gibi keşfetmeye hazırsınız. Kolay gelsin!', side: "bottom", align: 'start' }}
      ];
    }

    const driverObj = driver({
      showProgress: true,
      animate: true,
      nextBtnText: 'İleri ➔',
      prevBtnText: '⬅ Geri',
      doneBtnText: 'Bitir',
      steps: steps
    });
    
    driverObj.drive();
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/auth/login']);
  }

  loadUnreadCount(): void {
    this.notificationService.getUnreadCount().subscribe(count => {
      this.unreadCount = count;
    });
  }

  loadNotifications(): void {
    this.notificationService.getNotifications().subscribe(data => {
      this.notifications = data;
    });
  }

  onBellClick(event: any, op: any): void {
    this.loadNotifications();
    op.toggle(event);
  }

  markAsRead(notification: Notification, op: any): void {
    const action = () => {
      if ((notification.type === 'REJECTED_ITEM' || notification.type === 'PROPOSAL_EDITED') && notification.reference_id) {
        this.reportService.getReportIdByItem(notification.reference_id).subscribe({
          next: (reportId) => {
            this.router.navigate(['/reports', reportId], { queryParams: { itemId: notification.reference_id } });
            op.hide();
          },
          error: () => {
            this.messageService.add({severity: 'error', summary: 'Hata', detail: 'İlgili rapor bulunamadı.'});
          }
        });
      } else if (notification.type === 'PROPOSAL_PENDING') {
        this.router.navigate(['/reports'], { queryParams: { showProposals: 'true' } });
        op.hide();
      } else if (notification.type === 'MISSING_REPORT_WARNING') {
        this.router.navigate(['/reports']);
        op.hide();
      } else {
        // Fallback for any other type
        this.router.navigate(['/reports']);
        op.hide();
      }
    };

    if (!notification.is_read) {
      this.notificationService.markAsRead(notification.id).subscribe(() => {
        notification.is_read = true;
        this.unreadCount = Math.max(0, this.unreadCount - 1);
        action();
      });
    } else {
      action();
    }
  }

  markAllAsRead(): void {
    this.notificationService.markAllAsRead().subscribe(() => {
      this.notifications.forEach(n => n.is_read = true);
      this.unreadCount = 0;
    });
  }
}