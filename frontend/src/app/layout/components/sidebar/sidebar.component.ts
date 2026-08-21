import { Component, OnInit } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { AuthService } from '../../../core/services/auth.service';

import { CommonModule } from '@angular/common';

import { RouterModule, Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule
  ],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent implements OnInit {
  menuItems: MenuItem[] = [];

  constructor(private authService: AuthService, private router: Router) {}

  ngOnInit(): void {
    this.buildMenu();
    this.checkExpandedState(this.router.url);
    
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      this.checkExpandedState(event.urlAfterRedirects);
    });
  }

  private checkExpandedState(url: string): void {
    this.menuItems.forEach(item => {
      if (item.items && item.routerLink) {
        const link = Array.isArray(item.routerLink) ? item.routerLink.join('/') : item.routerLink;
        if (url.startsWith(link)) {
          (item as any).expanded = true;
        }
      }
    });
  }

  isItemActive(item: MenuItem): boolean {
    if (!item.routerLink) return false;
    const link = Array.isArray(item.routerLink) ? item.routerLink.join('/') : item.routerLink;
    // Strip query params for base path check
    const currentPath = this.router.url.split('?')[0];
    return currentPath.startsWith(link);
  }

  private buildMenu(): void {
    const user = this.authService.currentUserValue;
    const isAdmin = user?.is_superuser || user?.isSuperuser || user?.role === 'ADMIN' || user?.role === 'USER_MANAGER';
    const isNormalUser = user?.role === 'USER';

    let reportItems: any[] = [];
    
    if (isNormalUser) {
        reportItems = [
          {
            label: 'Raporlarım',
            icon: 'pi pi-users',
            routerLink: ['/reports'],
            queryParams: { tab: 'manager' }
          },
          {
            label: 'Benimle Paylaşılanlar',
            icon: 'pi pi-share-alt',
            routerLink: ['/reports'],
            queryParams: { tab: 'shared' }
          }
        ];
    } else {
        reportItems = [
          {
            label: 'Kendi Raporlarım',
            icon: 'pi pi-user',
            routerLink: ['/reports'],
            queryParams: { tab: 'my' }
          },
          {
            label: 'Birim Raporları',
            icon: 'pi pi-sitemap',
            routerLink: ['/reports'],
            queryParams: { tab: 'unit' }
          },
          {
            label: 'Yöneticimin Raporları',
            icon: 'pi pi-users',
            routerLink: ['/reports'],
            queryParams: { tab: 'manager' }
          },
          {
            label: 'Benimle Paylaşılanlar',
            icon: 'pi pi-share-alt',
            routerLink: ['/reports'],
            queryParams: { tab: 'shared' }
          }
        ];
    }

    let reportsMenuItem: any = {
      label: 'Faaliyet Raporları',
      icon: 'pi pi-file-edit',
      routerLink: ['/reports']
    };

    if (isAdmin) {
      reportsMenuItem.queryParams = { tab: 'all' };
    } else {
      reportsMenuItem.items = reportItems;
    }

    this.menuItems = [
      {
        label: 'Genel Bakış',
        icon: 'pi pi-home',
        routerLink: ['/dashboard']
      },
      reportsMenuItem,
      {
        label: 'Organizasyon Yapısı',
        icon: 'pi pi-sitemap',
        routerLink: ['/units']
      }
    ];

    if (isAdmin) {
      this.menuItems.push(
        {
          label: 'Kullanıcı Yönetimi',
          icon: 'pi pi-users',
          routerLink: ['/users']
        }
      );
    }
    
    if (user?.role === 'ADMIN' || user?.is_superuser || user?.isSuperuser) {
      this.menuItems.push(
        {
          label: 'Sistem Logları',
          icon: 'pi pi-history',
          routerLink: ['/logs']
        }
      );
    }
    
    if (isAdmin || user?.role === 'MANAGER') {
      this.menuItems.push(
        {
          label: 'Kurum Yönetimi',
          icon: 'pi pi-building',
          routerLink: ['/institutions']
        }
      );
    }
  }
}