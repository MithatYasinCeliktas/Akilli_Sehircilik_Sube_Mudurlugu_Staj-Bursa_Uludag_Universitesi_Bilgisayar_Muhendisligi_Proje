import { Injectable, NgZone } from '@angular/core';
import { AuthService } from './auth.service';
import { SettingsService } from './settings.service';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';

@Injectable({
  providedIn: 'root'
})
export class IdleService {
  private timeoutId: any;
  private readonly events: string[] = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];

  constructor(
    private authService: AuthService,
    private settingsService: SettingsService,
    private router: Router,
    private ngZone: NgZone,
    private messageService: MessageService
  ) {}

  startWatching() {
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.resetTimer();
        this.events.forEach(eventName => {
          window.addEventListener(eventName, this.resetTimer.bind(this), true);
        });
      } else {
        this.stopWatching();
      }
    });
  }

  stopWatching() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
    this.events.forEach(eventName => {
      window.removeEventListener(eventName, this.resetTimer.bind(this), true);
    });
  }

  resetTimer() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
    
    // Yalnızca giriş yapılmışsa timer kur
    if (!this.authService.isLoggedIn()) return;

    this.ngZone.runOutsideAngular(() => {
      const minutes = this.settingsService.getSettings().idleTimeoutMinutes || 30;
      this.timeoutId = setTimeout(() => {
        this.ngZone.run(() => {
          this.logoutDueToInactivity();
        });
      }, minutes * 60 * 1000);
    });
  }

  private logoutDueToInactivity() {
    this.stopWatching();
    this.authService.logout();
    this.messageService.add({
      severity: 'warn',
      summary: 'Oturum Kapatıldı',
      detail: 'Uzun süre işlem yapmadığınız için oturumunuz otomatik olarak sonlandırıldı.'
    });
  }
}
