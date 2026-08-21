import { Component, HostListener, OnInit, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { SettingsService } from './core/services/settings.service';
import { IdleService } from './core/services/idle.service';
import { PrimeNGConfig } from 'primeng/api';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'Bursa Büyükşehir Belediyesi Faaliyet Raporu Sistemi';

  // Global Arka Plan Ayarları
  backgroundImages: string[] = [
    'assets/global-bg-1.jpg',
    'assets/global-bg-2.jpg',
    'assets/global-bg-3.jpg'
  ];
  currentBgIndex: number = 0;
  bgInterval: any;

  constructor(
    @Inject(PLATFORM_ID) private platformId: Object,
    private settingsService: SettingsService,
    private idleService: IdleService,
    private primengConfig: PrimeNGConfig
  ) {}

  ngOnInit(): void {
    // PrimeNG z-index konfigürasyonu (açılır bileşenlerin arkada kalmasını engeller)
    this.primengConfig.zIndex = {
      modal: 1100,      // dialog, sidebar
      overlay: 1000,    // dropdown, overlaypanel
      menu: 1000,       // overlay menus
      tooltip: 1100     // tooltip
    };

    if (isPlatformBrowser(this.platformId)) {
      // Başlangıçta rastgele bir resim seç
      this.currentBgIndex = Math.floor(Math.random() * this.backgroundImages.length);
      
      // Her 60 saniyede bir resmi rastgele (farklı olacak şekilde) değiştir
      this.bgInterval = setInterval(() => {
        let nextIndex = this.currentBgIndex;
        while (nextIndex === this.currentBgIndex) {
          nextIndex = Math.floor(Math.random() * this.backgroundImages.length);
        }
        this.currentBgIndex = nextIndex;
      }, 60000); // 60 saniye
      
      this.idleService.startWatching();
    }
  }

  ngOnDestroy(): void {
    if (this.bgInterval) {
      clearInterval(this.bgInterval);
    }
  }

  // Sağ tık (context menu) engelleme
  @HostListener('document:contextmenu', ['$event'])
  onRightClick(event: MouseEvent) {
    event.preventDefault();
  }

  // Geliştirici araçlarını açan kısayolları engelleme
  @HostListener('document:keydown', ['$event'])
  onKeyDown(event: KeyboardEvent) {
    if (event.key === 'F12') {
      event.preventDefault();
    }
    
    if (event.ctrlKey && event.shiftKey && (event.key === 'I' || event.key === 'i' || event.key === 'J' || event.key === 'j')) {
      event.preventDefault();
    }
    
    if (event.ctrlKey && (event.key === 'U' || event.key === 'u')) {
      event.preventDefault();
    }
    
    if (event.ctrlKey && event.shiftKey && (event.key === 'C' || event.key === 'c')) {
      event.preventDefault();
    }
  }
}