import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from './core/guards/auth.guard';
import { AdminGuard } from './core/guards/admin.guard';
import { RoleGuard } from './core/guards/role.guard';
import { MainLayoutComponent } from './layout/main-layout/main-layout.component';

/**
 * Uygulamanın Ana Rota (Routing) Tanımlamaları
 * 
 * Bu dosya, hangi URL adresinin hangi modülü veya bileşeni açacağını belirler.
 * Angular'ın "Lazy Loading" (Tembel Yükleme) özelliği kullanılarak, 
 * modüller sadece kullanıcı o sayfaya girdiğinde tarayıcıya indirilir (loadChildren).
 * Bu sayede uygulamanın ilk açılış hızı (performance) büyük ölçüde artırılır.
 */
const routes: Routes = [
  {
    // Giriş (Login) sayfası rotası. 
    // AuthGuard tarafından korunmaz, çünkü giriş yapmamış herkesin buraya erişebilmesi gerekir.
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.module').then(m => m.AuthModule)
  },
  {
    // Ana uygulama rotası (Login sonrası ekranlar).
    // MainLayoutComponent, sol menü (Sidebar) ve üst çubuğu (Header) barındırır.
    path: '',
    component: MainLayoutComponent,
    canActivate: [AuthGuard], // Sadece geçerli bir JWT token'a sahip giriş yapmış kullanıcılar girebilir.
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
      {
        // Genel Bakış (Dashboard) modülü
        path: 'dashboard',
        loadChildren: () => import('./features/dashboard/dashboard.module').then(m => m.DashboardModule)
      },
      {
        // Faaliyet Raporları (Rapor ekleme, listeleme, onaylama) modülü
        path: 'reports',
        loadChildren: () => import('./features/reports/reports.module').then(m => m.ReportsModule)
      },
      {
        // Organizasyon Yapısı ve Ağaç (Tree/Chart) modülü
        path: 'units',
        loadChildren: () => import('./features/units/units.module').then(m => m.UnitsModule)
      },
      {
        // Kullanıcı Yönetimi paneli
        // Ekstra olarak "AdminGuard" ile korunur. Sadece ADMIN ve USER_MANAGER görebilir.
        path: 'users',
        canActivate: [AdminGuard],
        loadChildren: () => import('./features/users/users.module').then(m => m.UsersModule)
      },
      {
        // Kurum/Kuruluş Yönetimi
        path: 'institutions',
        canActivate: [RoleGuard],
        data: { roles: ['ADMIN', 'USER_MANAGER', 'MANAGER'] },
        loadChildren: () => import('./features/institutions/institutions.module').then(m => m.InstitutionsModule)
      },
      {
        // Sistem Logları (Sadece ADMIN)
        path: 'logs',
        canActivate: [RoleGuard],
        data: { roles: ['ADMIN'] },
        loadChildren: () => import('./features/logs/logs.module').then(m => m.LogsModule)
      }
    ]
  },
  {
    // Tanımsız (Bulunamayan) tüm URL'ler (Wildcard route) 
    // otomatik olarak /dashboard adresine yönlendirilir.
    path: '**',
    redirectTo: 'dashboard'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

export { routes };