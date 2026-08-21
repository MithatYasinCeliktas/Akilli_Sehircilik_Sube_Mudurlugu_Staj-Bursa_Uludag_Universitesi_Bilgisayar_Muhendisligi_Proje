import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Subject } from 'rxjs';

export interface AppSettings {
  panelOpacity: number;
  fontFamily: string;
  fontSize: number;
  idleTimeoutMinutes: number;
  theme: 'light' | 'dark';
}

@Injectable({
  providedIn: 'root'
})
export class SettingsService {
  private readonly SETTINGS_KEY = 'appSettings';
  private currentSettings: AppSettings;
  
  // Olay: Ayarlar panelini dışarıdan (örn. chatbot) açmak için
  public openSettingsPanel$ = new Subject<void>();
  
  // Olay: Chatbot üzerinden sistemi tanıtmak (tur) için
  public startTour$ = new Subject<void>();
  
  // Olay: Chatbot üzerinden raporları filtrelemek için
  public filterReports$ = new Subject<{year?: string, status?: string, month?: string, recent?: string, searchText?: string, startDate?: string, endDate?: string}>();

  // Olay: Chatbot üzerinden genel arama (Birimler, Kullanıcılar vb.) yapmak için
  public globalSearch$ = new Subject<{searchText: string, viewMode?: string}>();

  private readonly defaultSettings: AppSettings = {
    panelOpacity: 0.4,
    fontFamily: "'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    fontSize: 14,
    idleTimeoutMinutes: 30,
    theme: 'light'
  };

  constructor(@Inject(PLATFORM_ID) private platformId: Object) {
    this.currentSettings = { ...this.defaultSettings };
    if (isPlatformBrowser(this.platformId)) {
      this.loadSettings();
      this.applySettings();
    }
  }

  getSettings(): AppSettings {
    return this.currentSettings;
  }
  
  getDefaultSettings(): AppSettings {
    return { ...this.defaultSettings };
  }

  updateSettings(newSettings: Partial<AppSettings>) {
    this.currentSettings = { ...this.currentSettings, ...newSettings };
    if (isPlatformBrowser(this.platformId)) {
      this.saveSettings();
      this.applySettings();
    }
  }
  
  setSettingsFromBackend(settings: AppSettings | null) {
    if (!settings) return;
    this.currentSettings = { ...this.defaultSettings, ...settings };
    if (isPlatformBrowser(this.platformId)) {
      this.saveSettings();
      this.applySettings();
    }
  }

  private loadSettings() {
    const saved = localStorage.getItem(this.SETTINGS_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        this.currentSettings = { ...this.defaultSettings, ...parsed };
      } catch (e) {
        console.error('Ayarlar yüklenemedi, varsayılanlar kullanılacak', e);
      }
    }
  }

  private saveSettings() {
    localStorage.setItem(this.SETTINGS_KEY, JSON.stringify(this.currentSettings));
  }

  private applySettings() {
    const root = document.documentElement;
    root.style.setProperty('--panel-opacity', this.currentSettings.panelOpacity.toString());
    root.style.setProperty('--font-family', this.currentSettings.fontFamily);
    
    // Tema sınıflarını yönet (Karanlık Mod)
    if (this.currentSettings.theme === 'dark') {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
    
    // Uygulama geneli font boyutu değişimi (rem değerleri bu html font boyutuna oranlanır)
    root.style.fontSize = `${this.currentSettings.fontSize}px`;
    
    // PrimeNG komponentlerinin de bu font-family'yi zorla almasını sağlayalım (bazı temalar eziyor)
    const styleId = 'dynamic-font-override';
    let styleTag = document.getElementById(styleId);
    if (!styleTag) {
      styleTag = document.createElement('style');
      styleTag.id = styleId;
      document.head.appendChild(styleTag);
    }
    styleTag.innerHTML = `body, .p-component, .p-inputtext, .p-button { font-family: ${this.currentSettings.fontFamily} !important; }`;
  }
}
