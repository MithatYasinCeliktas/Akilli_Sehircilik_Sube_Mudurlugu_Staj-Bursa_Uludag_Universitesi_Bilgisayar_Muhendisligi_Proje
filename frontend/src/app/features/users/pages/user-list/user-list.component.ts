import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { UserService } from '../../../../core/services/user.service';
import { UnitService } from '../../../../core/services/unit.service';
import { User, UserRole } from '../../../../core/models/user.model';
import { AuthService } from '../../../../core/services/auth.service';
import { SettingsService } from '../../../../core/services/settings.service';

@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.html',
  styleUrls: ['./user-list.component.scss']
})
export class UserListComponent implements OnInit {
  users: User[] = [];
  totalRecords: number = 0;
  loading: boolean = true;
  page: number = 1;
  pageSize: number = 10;
  first: number = 0;

  // Filtreler
  searchText: string = '';
  filterUnitId: number | null = null;
  filterRole: string | null = null;

  // Dialog ve Form durumları
  displayCreateDialog: boolean = false;
  isEditMode: boolean = false;
  selectedUserId: number | null = null;
  userForm!: FormGroup;
  formLoading: boolean = false;

  // Dropdown listeleri
  units: { label: string, value: number }[] = [];
  managers: { label: string, value: number }[] = [];

  roleOptions = [
    { label: 'Kullanıcı', value: UserRole.USER },
    { label: 'Birim Yöneticisi', value: UserRole.MANAGER },
    { label: 'Kullanıcı Yöneticisi', value: UserRole.USER_MANAGER },
    { label: 'Sistem Yöneticisi (Admin)', value: UserRole.ADMIN }
  ];

  currentUser: User | null = null;

  constructor(
    private userService: UserService,
    private unitService: UnitService,
    private fb: FormBuilder,
    private authService: AuthService,
    private route: ActivatedRoute,
    private router: Router,
    private settingsService: SettingsService
  ) {}

  ngOnInit(): void {
    this.currentUser = this.authService.currentUserValue;
    if (this.currentUser?.role === UserRole.USER_MANAGER) {
      this.roleOptions = this.roleOptions.filter(r => r.value !== UserRole.ADMIN);
    }
    
    // Listen to global searches from chatbot
    this.settingsService.globalSearch$.subscribe(data => {
      if (data.searchText) {
        this.searchText = data.searchText;
      }
      this.loadUsers();
    });

    this.loadUsers();
    this.initForm();
    this.loadUnits();
    // Managers are loaded dynamically based on unit_id, but let's load all initially just in case (or maybe just clear it)
    this.managers = [];

    // Check query params for action=create&unit_id
    this.route.queryParams.subscribe(params => {
      if (params['action'] === 'create') {
        const preselectUnitId = params['unit_id'] ? parseInt(params['unit_id'], 10) : null;
        this.showCreateDialog();
        if (preselectUnitId) {
          this.userForm.patchValue({ unit_id: preselectUnitId });
        }
        
        // Remove query params after handling so it doesn't reopen on refresh
        this.router.navigate([], {
          relativeTo: this.route,
          queryParams: {},
          replaceUrl: true
        });
      }
    });
  }

  private initForm(): void {
    this.userForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      full_name: ['', Validators.required],
      password: ['', [Validators.required, Validators.minLength(6)]],
      role: [UserRole.USER, Validators.required],
      title: [''],
      unit_id: [null],
      manager_id: [null],
      is_active: [true],
      is_superuser: [false]
    });

    // Rol değiştiğinde ADMIN değilse Süper Yetkili kutusunu kapat/pasif yap
    this.userForm.get('role')?.valueChanges.subscribe(role => {
      const isSuperuserCtrl = this.userForm.get('is_superuser');
      if (role !== UserRole.ADMIN) {
        isSuperuserCtrl?.setValue(false);
      }
    });

    // unit_id değiştiğinde geçerli yöneticileri yükle
    this.userForm.get('unit_id')?.valueChanges.subscribe(unitId => {
      if (unitId) {
        this.loadManagers(unitId);
      } else {
        this.managers = [];
        this.userForm.patchValue({ manager_id: null }, { emitEvent: false });
      }
    });
  }

  loadUsers(): void {
    this.loading = true;
    this.userService.getUsers(
      this.page, 
      this.pageSize,
      this.searchText,
      this.filterUnitId !== null ? this.filterUnitId : undefined,
      this.filterRole !== null ? this.filterRole : undefined
    ).subscribe({
      next: (data) => {
        this.users = data.items;
        this.totalRecords = data.total;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  applyFilters(): void {
    this.page = 1; // Filtre uygulandığında ilk sayfaya dön
    this.first = 0;
    this.loadUsers();
  }

  clearFilters(): void {
    this.searchText = '';
    this.filterUnitId = null;
    this.filterRole = null;
    this.page = 1;
    this.first = 0;
    this.loadUsers();
  }

  loadUnits(): void {
    this.unitService.getUnitTree().subscribe({
      next: (tree) => {
        this.units = [];
        
        const processNode = (node: any) => {
          // Bir grubun kendisi seçilemediği için onu listeye dahil ediyoruz
          const group: any = {
            label: node.name,
            value: node.id,
            items: [
              { label: node.name + ' (Merkez / Tümü)', value: node.id }
            ]
          };
          
          if (node.children && node.children.length > 0) {
            for (const child of node.children) {
              if (child.children && child.children.length > 0) {
                // Eğer çocuğun da çocukları varsa, onu ayrı bir grup yapalım
                processNode(child);
              } else {
                // Sadece yaprak (leaf) düğümse gruba dahil et
                group.items.push({ label: child.name, value: child.id });
              }
            }
          }
          this.units.push(group);
        };
        
        if (tree && tree.length > 0) {
          for (const node of tree) {
            processNode(node);
          }
        }
      }
    });
  }

  loadManagers(unitId: number): void {
    this.userService.getValidManagers(unitId).subscribe({
      next: (data) => {
        this.managers = data.map(u => ({ label: `${u.full_name || u.email} (${u.role})`, value: u.id }));
        
        // Eğer seçili bir manager_id varsa ve yeni listede yoksa, temizle
        const currentManagerId = this.userForm.get('manager_id')?.value;
        if (currentManagerId && !this.managers.find(m => m.value === currentManagerId)) {
           this.userForm.patchValue({ manager_id: null }, { emitEvent: false });
        }
      }
    });
  }

  showCreateDialog(): void {
    this.isEditMode = false;
    this.selectedUserId = null;
    this.userForm.reset({
      email: '',
      full_name: '',
      password: '',
      role: UserRole.USER,
      title: '',
      unit_id: null,
      manager_id: null,
      is_active: true,
      is_superuser: false
    });
    
    // Oluştururken şifre zorunludur
    this.userForm.get('password')?.setValidators([Validators.required, Validators.minLength(6)]);
    this.userForm.get('password')?.updateValueAndValidity();
    
    this.displayCreateDialog = true;
  }

  showEditDialog(user: User): void {
    this.isEditMode = true;
    this.selectedUserId = user.id;
    
    this.userForm.reset({
      email: user.email,
      full_name: user.full_name || user.fullName || '',
      password: '', // Boş kalabilir, değiştirilmeyecekse
      role: user.role,
      title: user.title || '',
      unit_id: user.unit_id || user.unitId || null,
      manager_id: user.manager_id || user.managerId || null,
      is_active: user.is_active !== undefined ? user.is_active : (user.isActive !== undefined ? user.isActive : true),
      is_superuser: user.is_superuser !== undefined ? user.is_superuser : (user.isSuperuser !== undefined ? user.isSuperuser : false)
    });

    // Güncellerken şifre zorunlu değildir (sadece girilirse minLength check)
    this.userForm.get('password')?.setValidators([Validators.minLength(6)]);
    this.userForm.get('password')?.updateValueAndValidity();

    this.displayCreateDialog = true;
  }

  onUserFormSubmit(): void {
    if (this.userForm.invalid) {
      this.userForm.markAllAsTouched();
      return;
    }

    this.formLoading = true;
    const formValue = { ...this.userForm.value };
    
    // Rol ADMIN değilse is_superuser kesinlikle false yapılmalı
    if (formValue.role !== UserRole.ADMIN) {
      formValue.is_superuser = false;
    }

    if (this.isEditMode && this.selectedUserId) {
      // Şifre girilmediyse istek gövdesinden çıkar
      if (!formValue.password) {
        delete formValue.password;
      }
      this.userService.updateUser(this.selectedUserId, formValue).subscribe({
        next: () => {
          this.formLoading = false;
          this.displayCreateDialog = false;
          this.loadUsers();
          // this.loadManagers(); // form reset will trigger valueChanges
        },
        error: () => {
          this.formLoading = false;
        }
      });
    } else {
      this.userService.createUser(formValue).subscribe({
        next: () => {
          this.formLoading = false;
          this.displayCreateDialog = false;
          this.loadUsers();
          // this.loadManagers(); // form reset will trigger valueChanges
        },
        error: () => {
          this.formLoading = false;
        }
      });
    }
  }

  onPageChange(event: any): void {
    this.first = event.first;
    this.page = (event.first / event.rows) + 1;
    this.pageSize = event.rows;
    this.loadUsers();
  }

  deleteUser(user: User): void {
    if (confirm(`'${user.full_name}' isimli kullanıcıyı silmek istediğinize emin misiniz?`)) {
      this.userService.deleteUser(user.id).subscribe({
        next: () => {
          this.loadUsers();
        }
      });
    }
  }
}