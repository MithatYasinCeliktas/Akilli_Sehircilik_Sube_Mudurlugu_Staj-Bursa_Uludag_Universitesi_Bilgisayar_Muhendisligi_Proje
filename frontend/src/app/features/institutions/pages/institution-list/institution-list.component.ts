import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { InstitutionService } from '../../../../core/services/institution.service';
import { Institution } from '../../../../core/models/institution.model';
import { ConfirmationService, MessageService } from 'primeng/api';
import { AuthService } from '../../../../core/services/auth.service';
import { User } from '../../../../core/models/user.model';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-institution-list',
  templateUrl: './institution-list.component.html',
  styleUrls: ['./institution-list.component.scss'],
  providers: [MessageService, ConfirmationService]
})
export class InstitutionListComponent implements OnInit, OnDestroy {
  institutions: Institution[] = [];
  loading: boolean = true;

  displayDialog: boolean = false;
  form!: FormGroup;
  isEditing: boolean = false;
  editingId: number | null = null;
  formLoading: boolean = false;
  
  currentUser: User | null = null;
  authSub!: Subscription;

  constructor(
    private institutionService: InstitutionService,
    private fb: FormBuilder,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.authSub = this.authService.currentUser$.subscribe(u => this.currentUser = u);
    this.initForm();
    this.loadInstitutions();
  }
  
  ngOnDestroy(): void {
    if (this.authSub) this.authSub.unsubscribe();
  }

  private initForm(): void {
    this.form = this.fb.group({
      name: ['', Validators.required],
      is_active: [true]
    });
  }

  loadInstitutions(): void {
    this.loading = true;
    this.institutionService.getInstitutions(false).subscribe({
      next: (data) => {
        this.institutions = data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  canEdit(inst: Institution): boolean {
    if (!this.currentUser) return false;
    if (this.currentUser.role === 'ADMIN' || this.currentUser.is_superuser) return true;
    return inst.created_by_id === this.currentUser.id;
  }

  showAddDialog(): void {
    this.isEditing = false;
    this.editingId = null;
    this.form.reset({
      name: '',
      is_active: true
    });
    this.displayDialog = true;
  }

  showEditDialog(inst: Institution): void {
    this.isEditing = true;
    this.editingId = inst.id;
    this.form.patchValue({
      name: inst.name,
      is_active: inst.is_active
    });
    this.displayDialog = true;
  }

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.formLoading = true;
    const request = this.isEditing && this.editingId
      ? this.institutionService.updateInstitution(this.editingId, this.form.value)
      : this.institutionService.createInstitution(this.form.value);

    request.subscribe({
      next: () => {
        this.messageService.add({ severity: 'success', summary: 'Başarılı', detail: 'Kurum kaydedildi.' });
        this.displayDialog = false;
        this.formLoading = false;
        this.loadInstitutions();
      },
      error: () => {
        this.formLoading = false;
      }
    });
  }

  confirmDelete(inst: Institution): void {
    this.confirmationService.confirm({
      message: `${inst.name} isimli kurumu silmek istediğinize emin misiniz?`,
      header: 'Silme Onayı',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Evet',
      rejectLabel: 'Hayır',
      accept: () => {
        this.institutionService.deleteInstitution(inst.id).subscribe({
          next: () => {
            this.messageService.add({ severity: 'success', summary: 'Başarılı', detail: 'Kurum silindi.' });
            this.loadInstitutions();
          }
        });
      }
    });
  }
}
