import { Component, OnInit, NgZone } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { TreeNode } from 'primeng/api';
import { UnitService } from '../../../../core/services/unit.service';
import { AuthService } from '../../../../core/services/auth.service';
import { ReportShareService } from '../../../../core/services/report-share.service';
import { MessageService } from 'primeng/api';
import { SettingsService } from '../../../../core/services/settings.service';

@Component({
  selector: 'app-unit-list',
  templateUrl: './unit-list.component.html',
  styleUrls: ['./unit-list.component.scss'],
  providers: [MessageService]
})
export class UnitListComponent implements OnInit {
  nodes: TreeNode[] = [];
  rawTreeData: any[] = [];
  loading: boolean = true;
  showUsers: boolean = true;
  searchQuery: string = '';
  searchType: 'all' | 'unit' | 'user' = 'all';
  showSearchOptions: boolean = false;

  displayCreateDialog: boolean = false;
  unitForm!: FormGroup;
  formLoading: boolean = false;
  flatUnits: { label: string, value: number }[] = [];
  
  isAdmin: boolean = false;
  isUserManager: boolean = false;
  isEditing: boolean = false;
  editingUnitId: number | null = null;
  selectedNode: TreeNode | null = null;
  zoomLevel: number = 100;
  isSmoothZoom: boolean = false;
  private zoomScrollTimeout: any;
  
  // Sürükleme (Pan) durumları
  isDragging: boolean = false;
  dragStartX: number = 0;
  dragStartY: number = 0;
  scrollStartX: number = 0;
  scrollStartY: number = 0;

  viewMode: 'tree' | 'chart' = 'tree';
  viewOptions: any[] = [
    { label: 'Ağaç Görünümü', value: 'tree', icon: 'pi pi-sitemap' },
    { label: 'Şema Görünümü', value: 'chart', icon: 'pi pi-share-alt' }
  ];

  isShareMode: boolean = false;
  shareReportId: number | null = null;
  selectedShareTarget: any = null; // { type: 'unit'|'user', id: number, name: string }

  constructor(
    private unitService: UnitService,
    private authService: AuthService,
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private reportShareService: ReportShareService,
    private messageService: MessageService,
    private ngZone: NgZone,
    private settingsService: SettingsService
  ) {}

  ngOnInit(): void {
    // Listen to global searches from chatbot
    this.settingsService.globalSearch$.subscribe(data => {
      if (data.searchText) {
        this.searchQuery = data.searchText;
        this.searchType = 'all';
      }
      if (data.viewMode) {
        this.viewMode = data.viewMode as 'tree' | 'chart';
      }
      this.filterTree();
    });

    const user = this.authService.currentUserValue;
    this.isAdmin = user ? (user.is_superuser || user.isSuperuser || user.role === 'ADMIN') : false;
    this.isUserManager = user ? (user.role === 'USER_MANAGER') : false;
    
    this.route.queryParams.subscribe(params => {
      this.isShareMode = params['mode'] === 'share';
      if (this.isShareMode) {
        const idStr = localStorage.getItem('share_report_id');
        this.shareReportId = idStr ? parseInt(idStr, 10) : null;
        if (!this.shareReportId) {
           this.cancelShare();
        }
      }
    });

    this.initForm();
    this.loadTree();
  }

  private initForm(): void {
    this.unitForm = this.fb.group({
      name: ['', Validators.required],
      code: [''],
      description: [''],
      parent_id: [null]
    });
  }

  loadTree(): void {
    this.loading = true;
    this.unitService.getUnitTree().subscribe({
      next: (treeData) => {
        this.rawTreeData = treeData;
        this.nodes = [...this.mapToTreeNode(this.rawTreeData)];
        this.nodes.forEach(n => this.calculateSubtreeDepth(n));
        this.extractFlatUnits(this.rawTreeData);
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  private extractFlatUnits(nodes: any[]): void {
    this.flatUnits = [];
    const traverse = (items: any[], prefix = '') => {
      for (const item of items) {
        this.flatUnits.push({ label: `${prefix}${item.name}`, value: item.id });
        if (item.children && item.children.length > 0) {
          traverse(item.children, prefix + '- ');
        }
      }
    };
    traverse(nodes);
  }

  toggleUsers(): void {
    this.showUsers = !this.showUsers;
    this.filterTree();
  }

  toggleUserList(node: any, event: Event): void {
    if (event) {
      event.stopPropagation();
    }
    if (node && node.data) {
      node.data.isUsersExpanded = !node.data.isUsersExpanded;
    }
  }

  filterTree(): void {
    if (!this.searchQuery || this.searchQuery.trim() === '') {
      this.nodes = [...this.mapToTreeNode(this.rawTreeData)];
      return;
    }

    const query = this.searchQuery.toLocaleLowerCase('tr-TR');
    
    const filterNodes = (nodes: any[]): any[] => {
      const filtered = [];
      for (const node of nodes) {
        let match = false;
        
        if (this.searchType === 'all' || this.searchType === 'unit') {
          if (node.name.toLocaleLowerCase('tr-TR').includes(query) || (node.code && node.code.toLocaleLowerCase('tr-TR').includes(query))) {
            match = true;
          }
        }
        
        let matchedUsers: any[] = [];
        if (this.showUsers && (this.searchType === 'all' || this.searchType === 'user')) {
           const users = node.unit_users || node.unitUsers || [];
           matchedUsers = users.filter((u: any) => 
              (u.full_name && u.full_name.toLocaleLowerCase('tr-TR').includes(query)) ||
              (u.title && u.title.toLocaleLowerCase('tr-TR').includes(query)) ||
              (u.email && u.email.toLocaleLowerCase('tr-TR').includes(query))
           );
           if (matchedUsers.length > 0) match = true;
        }

        let matchedChildren: any[] = [];
        if (node.children && node.children.length > 0) {
          matchedChildren = filterNodes(node.children);
          if (matchedChildren.length > 0) match = true;
        }

        if (match) {
           const clonedNode = { ...node, children: matchedChildren };
           
           if (this.showUsers) {
               if (matchedUsers.length > 0) {
                   clonedNode.unit_users = matchedUsers;
                   clonedNode.unitUsers = matchedUsers;
               } else if (!node.name.toLocaleLowerCase('tr-TR').includes(query) && !(node.code && node.code.toLocaleLowerCase('tr-TR').includes(query))) {
                   clonedNode.unit_users = [];
                   clonedNode.unitUsers = [];
               }
           }
           clonedNode._originalChildrenLength = node.children ? node.children.length : 0;
           filtered.push(clonedNode);
        }
      }
      return filtered;
    };

    const filteredData = filterNodes(this.rawTreeData);
    this.nodes = [...this.mapToTreeNode(filteredData)];
    this.nodes.forEach(n => this.calculateSubtreeDepth(n));

    // Aranan sonuca otomatik odaklanma (Scroll)
    if (this.searchQuery && this.searchQuery.trim().length >= 2) {
      setTimeout(() => {
        const matchEl = document.querySelector('.search-match');
        if (matchEl) {
          matchEl.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
        }
      }, 300); // DOM render süresi
    }
  }

  setSearchType(type: 'unit' | 'user'): void {
    if (this.searchType === type) {
      this.searchType = 'all'; // Toggling off
    } else {
      this.searchType = type;
    }
    this.filterTree();
  }

  onViewModeChange(event: any): void {
    if (event) {
      this.viewMode = event;
    }
  }

  private smoothZoomAndScroll(
    container: HTMLElement, chartWrapper: HTMLElement,
    targetX: number, targetY: number, targetZoom: number, duration: number
  ) {
    const startX = container.scrollLeft;
    const startY = container.scrollTop;
    const startZoom = this.zoomLevel;
    
    const distanceX = targetX - startX;
    const distanceY = targetY - startY;
    const distanceZoom = targetZoom - startZoom;
    const startTime = performance.now();

    const easeInOutQuad = (t: number, b: number, c: number, d: number) => {
      t /= d / 2;
      if (t < 1) return (c / 2) * t * t + b;
      t--;
      return (-c / 2) * (t * (t - 2) - 1) + b;
    };

    const animate = (currentTime: number) => {
      const timeElapsed = currentTime - startTime;
      
      const currentZoom = easeInOutQuad(timeElapsed, startZoom, distanceZoom, duration);
      chartWrapper.style.transform = `scale(${currentZoom / 100})`;
      
      container.scrollLeft = easeInOutQuad(timeElapsed, startX, distanceX, duration);
      container.scrollTop = easeInOutQuad(timeElapsed, startY, distanceY, duration);

      if (timeElapsed < duration) {
        requestAnimationFrame(animate);
      } else {
        chartWrapper.style.transform = `scale(${targetZoom / 100})`;
        container.scrollLeft = targetX;
        container.scrollTop = targetY;
      }
    };

    this.ngZone.runOutsideAngular(() => {
      requestAnimationFrame(animate);
    });
  }

  onZoomChange(newZoom: number, smooth: boolean = false) {
    if (this.zoomScrollTimeout) {
      clearTimeout(this.zoomScrollTimeout);
    }
    
    // Küçük bir gecikme ile DOM elementlerini alıyoruz
    this.zoomScrollTimeout = setTimeout(() => {
      const container = document.querySelector('.custom-scrollbar') as HTMLElement;
      const chartWrapper = document.querySelector('.custom-scrollbar > div') as HTMLElement;
      if (!container || !chartWrapper) return;
      
      // Hedef (Final) hesaplamalar
      const targetZ = newZoom / 100;
      let targetX = 0;
      let targetY = 0;

      let targetEl: HTMLElement | null = null;
      if (this.selectedNode) {
        targetEl = document.getElementById('node-' + this.selectedNode.key);
      }
      
      if (targetEl) {
        let elTop = 0;
        let elLeft = 0;
        let current: HTMLElement | null = targetEl;
        while (current && current !== chartWrapper) {
          elTop += current.offsetTop;
          elLeft += current.offsetLeft;
          current = current.offsetParent as HTMLElement;
        }
        
        const cx = elLeft + (targetEl.offsetWidth / 2);
        const cy = elTop + (targetEl.offsetHeight / 2);
        
        const ox = chartWrapper.offsetWidth / 2;
        const oy = 0;
        
        const cxScaled = ox + (cx - ox) * targetZ;
        const cyScaled = oy + (cy - oy) * targetZ;
        
        targetX = cxScaled - (container.clientWidth / 2);
        targetY = cyScaled - (container.clientHeight / 2);
      } else {
        const currentZ = this.zoomLevel / 100;
        const vpCenterX = container.scrollLeft + (container.clientWidth / 2);
        const vpCenterY = container.scrollTop + (container.clientHeight / 2);
        
        const ox = chartWrapper.offsetWidth / 2;
        const oy = 0;
        
        // Bulunduğumuz noktanın gerçek (unscaled) koordinatını bul
        const cx = ox + (vpCenterX - ox) / currentZ;
        const cy = oy + (vpCenterY - oy) / currentZ;
        
        // Yeni zoom değerinde bu noktanın nereye kayacağını hesapla
        const cxScaled = ox + (cx - ox) * targetZ;
        const cyScaled = oy + (cy - oy) * targetZ;
        
        targetX = cxScaled - (container.clientWidth / 2);
        targetY = cyScaled - (container.clientHeight / 2);
      }
      
      if (smooth) {
        // Slider değerini Angular için hedefe ayarla
        this.zoomLevel = newZoom;
        
        // Animasyonu Angular dışında, CSS/JS senkronizasyonu bozmadan çalıştır
        this.smoothZoomAndScroll(container, chartWrapper, targetX, targetY, newZoom, 800);
      } else {
        // Slider sürüklenirken
        this.zoomLevel = newZoom;
        chartWrapper.style.transform = `scale(${targetZ})`;
        container.scrollLeft = targetX;
        container.scrollTop = targetY;
      }
    }, 10);
  }

  onWheelZoom(event: WheelEvent): void {
    if (this.viewMode !== 'chart') return;
    
    event.preventDefault();
    
    // Yön belirle: Yukarı kaydırma (negatif delta) zoom in, aşağı kaydırma zoom out
    const delta = Math.sign(event.deltaY);
    
    // Her tekerlek hareketinde %10 değiştir
    let newZoom = this.zoomLevel - (delta * 10);
    newZoom = Math.max(20, Math.min(200, newZoom));
    
    if (newZoom !== this.zoomLevel) {
      this.onZoomChange(newZoom, false); // smooth=false yaparak anında slider hissi veriyoruz
    }
  }
  
  onMouseDown(event: MouseEvent): void {
    if (this.viewMode !== 'chart') return;
    
    // Etkileşimli elementlere (butonlar, kartlar) tıklandığında kaydırmayı (pan) başlatma
    const target = event.target as HTMLElement;
    if (target.closest('button') || target.closest('.p-button') || target.closest('.cursor-pointer')) {
      return;
    }
    
    this.isDragging = true;
    this.dragStartX = event.pageX;
    this.dragStartY = event.pageY;
    
    const container = event.currentTarget as HTMLElement;
    this.scrollStartX = container.scrollLeft;
    this.scrollStartY = container.scrollTop;
  }
  
  onMouseMove(event: MouseEvent): void {
    if (!this.isDragging || this.viewMode !== 'chart') return;
    
    event.preventDefault(); // Metin seçimini engelle
    const container = event.currentTarget as HTMLElement;
    
    const x = event.pageX - this.dragStartX;
    const y = event.pageY - this.dragStartY;
    
    // Ters yönde kaydır (harita gibi)
    container.scrollLeft = this.scrollStartX - x;
    container.scrollTop = this.scrollStartY - y;
  }
  
  onMouseUp(): void {
    this.isDragging = false;
  }

  onNodeDblClick(node: TreeNode): void {
    this.selectedNode = node;
    this.onNodeClick(node.data);
    
    // Çift tıklandığında hem merkeze alır hem de okunaklı bir boyuta (%120 veya daha fazla) yaklaştırır
    let newZoom = Math.max(120, this.zoomLevel + 20);
    newZoom = Math.min(200, newZoom);
    this.onZoomChange(newZoom, true);
  }

  showCreateDialog(): void {
    this.isEditing = false;
    this.editingUnitId = null;
    this.unitForm.reset({
      name: '',
      code: '',
      description: '',
      parent_id: null
    });
    this.displayCreateDialog = true;
  }

  editUnit(unit: any, event?: Event): void {
    if (event) event.stopPropagation();
    this.isEditing = true;
    this.editingUnitId = unit.id;
    this.unitForm.patchValue({
      name: unit.name,
      code: unit.code || '',
      description: unit.description || '',
      parent_id: unit.parent_id || null
    });
    this.displayCreateDialog = true;
  }

  addUserToUnit(unit: any, event?: Event): void {
    if (event) event.stopPropagation();
    this.router.navigate(['/users'], { queryParams: { action: 'create', unit_id: unit.id } });
  }

  onUnitFormSubmit(): void {
    if (this.unitForm.invalid) {
      this.unitForm.markAllAsTouched();
      this.unitForm.markAllAsTouched();
      return;
    }

    this.formLoading = true;
    
    const request = this.isEditing && this.editingUnitId
      ? this.unitService.updateUnit(this.editingUnitId, this.unitForm.value)
      : this.unitService.createUnit(this.unitForm.value);
      
    request.subscribe({
      next: () => {
        this.formLoading = false;
        this.displayCreateDialog = false;
        this.loadTree();
      },
      error: () => {
        this.formLoading = false;
      }
    });
  }

  private mapToTreeNode(units: any[], parentNode: TreeNode | null = null): TreeNode[] {
    return units.map(unit => {
      let isUnitMatch = false;
      if (this.searchQuery && this.searchQuery.trim() !== '') {
         const q = this.searchQuery.toLocaleLowerCase('tr-TR');
         isUnitMatch = unit.name.toLocaleLowerCase('tr-TR').includes(q) || (unit.code && unit.code.toLocaleLowerCase('tr-TR').includes(q));
      }

      const node: TreeNode = {
        key: `unit-${unit.id}`,
        label: `${unit.name} (${unit.code || '-'})`,
        data: {
          ...unit,
          isSearchMatch: isUnitMatch
        },
        icon: (unit.unit_type === 'DEPARTMENT' || unit.unitType === 'DEPARTMENT') ? 'pi pi-building text-primary' : 'pi pi-folder text-warning',
        expanded: true,
        parent: parentNode || undefined,
        children: []
      };

      const childrenNodes: TreeNode[] = [];
      
      // 1. Alt Birimleri (Çocuk Düğüm) ekle
      if (unit.children && unit.children.length > 0) {
        childrenNodes.push(...this.mapToTreeNode(unit.children, node));
      }
      
      // 2. Birimdeki Kullanıcıları (Personel) ekle (Eğer showUsers aktifse)
      if (this.showUsers) {
        const users = unit.unit_users || unit.unitUsers || [];
        if (users.length > 0) {
          const sortedUsers = [...users].sort((a, b) => {
             if (a.role === 'MANAGER' && b.role !== 'MANAGER') return -1;
             if (a.role !== 'MANAGER' && b.role === 'MANAGER') return 1;
             return 0;
          });

          const userNodes: TreeNode[] = sortedUsers.map((user: any) => {
            const isMe = this.authService.currentUserValue?.id === user.id;
            let isUserMatch = false;
            if (this.searchQuery && this.searchQuery.trim() !== '') {
              const q = this.searchQuery.toLocaleLowerCase('tr-TR');
              isUserMatch = (user.full_name && user.full_name.toLocaleLowerCase('tr-TR').includes(q)) ||
                            (user.title && user.title.toLocaleLowerCase('tr-TR').includes(q)) ||
                            (user.email && user.email.toLocaleLowerCase('tr-TR').includes(q));
            }
            return {
              key: `user-${user.id}`,
              label: user.full_name,
              data: {
                 ...user,
                 isCurrentUser: isMe,
                 isSearchMatch: isUserMatch
              },
              icon: user.role === 'MANAGER' ? 'pi pi-star-fill text-yellow-500' : 'pi pi-user text-green-500',
              expanded: false,
              parent: node,
              children: []
            };
          });

          const hasOriginalChildren = unit._originalChildrenLength !== undefined 
              ? unit._originalChildrenLength > 0 
              : (unit.children && unit.children.length > 0);

          if (hasOriginalChildren) {
            node.data.sideUsers = userNodes;
            
            let hasSearchMatch = false;
            if (this.searchQuery && this.searchQuery.trim() !== '') {
              const q = this.searchQuery.toLocaleLowerCase('tr-TR');
              hasSearchMatch = userNodes.some(u => 
                 (u.data.full_name && u.data.full_name.toLocaleLowerCase('tr-TR').includes(q)) ||
                 (u.data.title && u.data.title.toLocaleLowerCase('tr-TR').includes(q)) ||
                 (u.data.email && u.data.email.toLocaleLowerCase('tr-TR').includes(q))
              );
            }
            node.data.isUsersExpanded = hasSearchMatch || userNodes.length <= 10;
          } else {
            childrenNodes.push(...userNodes);
          }
        }
      }
      
      node.children = childrenNodes;
      return node;
    });
  }

  private calculateSubtreeDepth(node: TreeNode): number {
    if (!node.children || node.children.length === 0) {
      if (node.data) node.data.subtreeDepth = 0;
      return 0;
    }
    let max = 0;
    for (const child of node.children) {
      const d = this.calculateSubtreeDepth(child);
      if (d > max) max = d;
    }
    if (node.data) node.data.subtreeDepth = max + 1;
    return max + 1;
  }

  selectTargetForShare(node: any): void {
    if (!this.isShareMode) return;
    
    if (node.email) {
      // It's a user
      this.selectedShareTarget = { type: 'user', id: node.id, name: node.full_name };
    } else if (node.code !== undefined) {
      // It's a unit
      this.selectedShareTarget = { type: 'unit', id: node.id, name: node.name };
    }
  }

  onNodeClick(node: any): void {
    const isUser = node.email !== undefined;
    const typeName = isUser ? 'Kullanıcı' : 'Birim';
    const name = isUser ? (node.full_name || node.email) : node.name;
    
    this.messageService.add({
      key: 'center',
      severity: 'info',
      summary: 'Seçim Yapıldı',
      detail: `Seçilen ${typeName}: ${name}`,
      life: 3000
    });

    if (this.isShareMode) {
       this.selectTargetForShare(node);
    }
  }

  submitShare(): void {
    if (!this.shareReportId || !this.selectedShareTarget) return;

    const payload = {
      report_id: this.shareReportId,
      target_user_id: this.selectedShareTarget.type === 'user' ? this.selectedShareTarget.id : null,
      target_unit_id: this.selectedShareTarget.type === 'unit' ? this.selectedShareTarget.id : null,
    };

    this.reportShareService.requestShare(payload).subscribe({
      next: () => {
        this.messageService.add({severity: 'success', summary: 'Başarılı', detail: 'Paylaşım onaya gönderildi.'});
        this.cancelShare();
      },
      error: (err) => {
        this.messageService.add({severity: 'error', summary: 'Hata', detail: err.error?.detail || 'Paylaşım sırasında bir hata oluştu.'});
      }
    });
  }

  cancelShare(): void {
    this.isShareMode = false;
    this.shareReportId = null;
    this.selectedShareTarget = null;
    localStorage.removeItem('share_report_id');
    this.router.navigate(['/units']); // Remove mode query param
  }
}