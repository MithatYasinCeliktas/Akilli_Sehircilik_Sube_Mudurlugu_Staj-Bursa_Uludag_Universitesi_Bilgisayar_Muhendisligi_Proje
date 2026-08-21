import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { SidebarModule } from 'primeng/sidebar';
import { InputTextModule } from 'primeng/inputtext';
import { TooltipModule } from 'primeng/tooltip';
import { ChatService, ChatMessageResponse } from '../../../core/services/chat.service';
import { SettingsService } from '../../../core/services/settings.service';
import { Router } from '@angular/router';

interface ChatMessage {
  text: string;
  isUser: boolean;
  time: Date;
}

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonModule, SidebarModule, InputTextModule, TooltipModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss']
})
export class ChatbotComponent implements OnInit, AfterViewChecked {
  displaySidebar = false;
  userMessage = '';
  messages: ChatMessage[] = [];
  isLoading = false;
  private shouldScrollToBottom = false;
  isSoundEnabled = true;

  @ViewChild('chatScrollContainer') private chatScrollContainer!: ElementRef;

  constructor(private chatService: ChatService, private router: Router, private settingsService: SettingsService) {}

  ngOnInit() {
    this.messages.push({
      text: 'Merhaba! Ben Bursa Faaliyet Raporu Sistem Asistanı. Size nasıl yardımcı olabilirim?',
      isUser: false,
      time: new Date()
    });
  }

  ngAfterViewChecked() {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  private scrollToBottom(): void {
    try {
      this.chatScrollContainer.nativeElement.scrollTop = this.chatScrollContainer.nativeElement.scrollHeight;
    } catch(err) { }
  }

  toggleChat() {
    this.displaySidebar = !this.displaySidebar;
  }

  toggleSound() {
    this.isSoundEnabled = !this.isSoundEnabled;
    if (!this.isSoundEnabled && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  private speak(text: string) {
    if (!this.isSoundEnabled || !('speechSynthesis' in window)) return;
    
    // Stop any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'tr-TR';
    
    // Ses kalitesini artırmak için daha doğal (premium/Google) bir ses bulmaya çalışalım
    const voices = window.speechSynthesis.getVoices();
    const trVoices = voices.filter(v => v.lang.includes('tr'));
    if (trVoices.length > 0) {
      // Google'ın çevrimiçi sesleri veya işletim sisteminin doğal (Natural) sesleri genellikle çok daha akıcıdır
      const bestVoice = trVoices.find(v => 
        v.name.includes('Google') || 
        v.name.includes('Natural') || 
        v.name.includes('Premium') ||
        v.name.includes('Online')
      ) || trVoices[0];
      utterance.voice = bestVoice;
    }

    // Akıcılığı artırmak için hızı bir tık düşürüp, vurguyu (pitch) standartta bırakıyoruz
    utterance.rate = 0.95; 
    utterance.pitch = 1.0;
    
    window.speechSynthesis.speak(utterance);
  }

  sendMessage() {
    if (!this.userMessage.trim()) return;

    const messageText = this.userMessage;
    this.messages.push({
      text: messageText,
      isUser: true,
      time: new Date()
    });
    this.shouldScrollToBottom = true;
    this.userMessage = '';
    this.isLoading = true;

    this.chatService.sendMessage(messageText).subscribe({
      next: (res: ChatMessageResponse) => {
        this.isLoading = false;
        this.messages.push({
          text: res.message,
          isUser: false,
          time: new Date()
        });
        this.shouldScrollToBottom = true;

        if (res.route) {
          const currentUrlTree = this.router.parseUrl(this.router.url);
          const currentPath = currentUrlTree.root.children['primary'] 
            ? '/' + currentUrlTree.root.children['primary'].segments.map(s => s.path).join('/')
            : '/';
            
          const targetUrlTree = this.router.parseUrl(res.route);
          const targetPath = targetUrlTree.root.children['primary']
            ? '/' + targetUrlTree.root.children['primary'].segments.map(s => s.path).join('/')
            : '/';
            
          if (currentPath === targetPath) {
            // Check if target route specifies query params, if so we should navigate
            if (Object.keys(targetUrlTree.queryParams).length > 0 && 
                JSON.stringify(currentUrlTree.queryParams) !== JSON.stringify(targetUrlTree.queryParams)) {
                this.router.navigateByUrl(res.route).then(() => {
                  if (res.action_trigger) {
                    setTimeout(() => this.handleActionTrigger(res.action_trigger!), 200);
                  }
                });
            } else {
                // Zaten aynı sayfadayız ve hedef farklı bir query istemiyor, query param'ları bozmamak için navigate etme
                if (res.action_trigger) {
                  this.handleActionTrigger(res.action_trigger);
                }
            }
          } else {
            this.router.navigateByUrl(res.route).then(() => {
              if (res.action_trigger) {
                setTimeout(() => this.handleActionTrigger(res.action_trigger!), 200);
              }
            });
          }
        } else {
          if (res.action_trigger) {
            this.handleActionTrigger(res.action_trigger);
          }
        }

        const finalMessage = this.messages[this.messages.length - 1].text;
        this.speak(finalMessage);
      },
      error: () => {
        this.isLoading = false;
        this.messages.push({
          text: 'Üzgünüm, şu anda bağlantı sorunu yaşıyorum. Lütfen daha sonra tekrar deneyin.',
          isUser: false,
          time: new Date()
        });
        this.shouldScrollToBottom = true;
      }
    });
  }

  private handleActionTrigger(trigger: string) {
    // Basic implementation for highlighting UI elements based on trigger
    setTimeout(() => {
      let selector = '';
      if (trigger === 'HIGHLIGHT_CREATE_REPORT') {
        selector = "button[label='Yeni Rapor Oluştur']";
      } else if (trigger === 'HIGHLIGHT_EXPORT_REPORT') {
        selector = "button[icon='pi pi-file-excel']";
      } else if (trigger === 'HIGHLIGHT_CREATE_USER') {
        selector = "button[label='Yeni Kullanıcı Ekle']";
      } else if (trigger === 'HIGHLIGHT_CREATE_INSTITUTION') {
        selector = "button[label='Yeni Kurum Ekle']";
      } else if (trigger === 'HIGHLIGHT_PROPOSAL_VIEW') {
        selector = "button[label='Gelen Teklifler']";
      } else if (trigger === 'HIGHLIGHT_PROFILE_MENU') {
        selector = ".btn-settings"; // or profile button depending on class
      } else if (trigger.startsWith('ACTION_')) {
        // Handle settings actions
        const currentSettings = this.settingsService.getSettings();
        
        if (trigger === 'ACTION_THEME_DARK') {
          this.settingsService.updateSettings({ theme: 'dark' });
        } else if (trigger === 'ACTION_THEME_LIGHT') {
          this.settingsService.updateSettings({ theme: 'light' });
        } else if (trigger === 'ACTION_FONT_UP') {
          if (currentSettings.fontSize >= 24) {
            this.messages[this.messages.length - 1].text = "Yazı boyutu zaten en yüksek seviyede (24px), daha fazla büyütülemez.";
          } else {
            this.settingsService.updateSettings({ fontSize: Math.min(currentSettings.fontSize + 2, 24) });
          }
        } else if (trigger === 'ACTION_FONT_DOWN') {
          if (currentSettings.fontSize <= 12) {
            this.messages[this.messages.length - 1].text = "Yazı boyutu zaten en düşük seviyede (12px), daha fazla küçültülemez.";
          } else {
            this.settingsService.updateSettings({ fontSize: Math.max(currentSettings.fontSize - 2, 12) });
          }
        } else if (trigger.startsWith('ACTION_FONT_SET:')) {
          const targetSize = parseInt(trigger.split(':')[1], 10);
          if (targetSize > 24) {
            this.settingsService.updateSettings({ fontSize: 24 });
            this.messages[this.messages.length - 1].text = "İstediğiniz boyut çok büyük. Yazı boyutu en yüksek sınır olan 24px olarak ayarlandı.";
          } else if (targetSize < 12) {
            this.settingsService.updateSettings({ fontSize: 12 });
            this.messages[this.messages.length - 1].text = "İstediğiniz boyut çok küçük. Yazı boyutu en düşük sınır olan 12px olarak ayarlandı.";
          } else {
            this.settingsService.updateSettings({ fontSize: targetSize });
            this.messages[this.messages.length - 1].text = `Yazı boyutu ${targetSize}px olarak ayarlandı.`;
          }
        } else if (trigger.startsWith('ACTION_OPACITY_SET:')) {
          const targetOpacity = parseInt(trigger.split(':')[1], 10);
          if (targetOpacity > 100) {
            this.settingsService.updateSettings({ panelOpacity: 1.0 });
            this.messages[this.messages.length - 1].text = "Görünürlük en fazla %100 olabilir. Panel görünürlüğü %100 olarak ayarlandı.";
          } else if (targetOpacity < 10) {
            this.settingsService.updateSettings({ panelOpacity: 0.1 });
            this.messages[this.messages.length - 1].text = "Görünürlük en az %10 olabilir. Panel görünürlüğü %10 olarak ayarlandı.";
          } else {
            this.settingsService.updateSettings({ panelOpacity: targetOpacity / 100.0 });
            this.messages[this.messages.length - 1].text = `Panel görünürlüğü %${targetOpacity} olarak ayarlandı.`;
          }
        } else if (trigger === 'ACTION_START_TOUR') {
          this.settingsService.startTour$.next();
          return;
        } else if (trigger.startsWith('ACTION_FILTER_REPORTS')) {
          const filterStr = trigger.split(':')[1];
          if (filterStr) {
            const params = filterStr.split(',');
            const filterData: {year?: string, status?: string, month?: string, recent?: string, searchText?: string, startDate?: string, endDate?: string} = {};
            params.forEach(p => {
              const [k, v] = p.split('=');
              if (k === 'year') filterData.year = v;
              if (k === 'status') filterData.status = v;
              if (k === 'month') filterData.month = v;
              if (k === 'recent') filterData.recent = v;
              if (k === 'searchText') filterData.searchText = v;
              if (k === 'startDate') filterData.startDate = v;
              if (k === 'endDate') filterData.endDate = v;
            });
            this.settingsService.filterReports$.next(filterData);
          } else {
            this.settingsService.filterReports$.next({});
          }
          return;
        } else if (trigger.startsWith('ACTION_GLOBAL_SEARCH')) {
          const params = trigger.split(':')[1];
          if (params) {
            const searchData: {searchText: string, viewMode?: string} = {searchText: ''};
            params.split(',').forEach(p => {
              const [k, v] = p.split('=');
              if (k === 'searchText') searchData.searchText = v;
              if (k === 'viewMode') searchData.viewMode = v;
            });
            
            if (searchData.searchText || searchData.viewMode) {
              // Delay emitting until router navigation completes if we're navigating
              setTimeout(() => {
                this.settingsService.globalSearch$.next(searchData);
              }, 100);
            }
          }
          return;
        }

        
        if (!trigger.startsWith('ACTION_FILTER_REPORTS')) {
          this.settingsService.openSettingsPanel$.next(); // Open settings sidebar after update
        }
        return; // Don't try to highlight DOM elements for these actions
      }

      if (selector) {
        const element = document.querySelector(selector) as HTMLElement;
        if (element) {
          // Highlight effect
          element.style.transition = "all 0.5s";
          element.style.boxShadow = "0 0 15px 5px rgba(255, 193, 7, 0.8)";
          element.style.transform = "scale(1.05)";
          
          setTimeout(() => {
            element.style.boxShadow = "";
            element.style.transform = "";
          }, 3000);
        }
      }
    }, 1000); // delay to wait for navigation to finish
  }
}
