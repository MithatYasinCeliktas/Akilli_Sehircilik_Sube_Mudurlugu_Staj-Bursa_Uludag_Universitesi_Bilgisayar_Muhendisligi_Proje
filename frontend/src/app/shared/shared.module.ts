import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DividerModule } from 'primeng/divider';
import { DropdownModule } from 'primeng/dropdown';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { MenuModule } from 'primeng/menu';
import { MessagesModule } from 'primeng/messages';
import { MessageModule } from 'primeng/message';
import { PanelMenuModule } from 'primeng/panelmenu';
import { TableModule } from 'primeng/table';
import { ToolbarModule } from 'primeng/toolbar';
import { TreeModule } from 'primeng/tree';
import { DialogModule } from 'primeng/dialog';
import { CheckboxModule } from 'primeng/checkbox';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { OrganizationChartModule } from 'primeng/organizationchart';
import { SelectButtonModule } from 'primeng/selectbutton';
import { ToastModule } from 'primeng/toast';
import { CalendarModule } from 'primeng/calendar';
import { MultiSelectModule } from 'primeng/multiselect';
import { TreeSelectModule } from 'primeng/treeselect';
import { SliderModule } from 'primeng/slider';
import { TabViewModule } from 'primeng/tabview';
import { TooltipModule } from 'primeng/tooltip';
import { RadioButtonModule } from 'primeng/radiobutton';
import { TagModule } from 'primeng/tag';
import { PaginatorModule } from 'primeng/paginator';

const PRIME_NG_MODULES = [
  ButtonModule,
  DividerModule,
  DropdownModule,
  InputNumberModule,
  InputTextModule,
  MenuModule,
  MessagesModule,
  MessageModule,
  PanelMenuModule,
  TableModule,
  ToolbarModule,
  TreeModule,
  DialogModule,
  CheckboxModule,
  InputTextareaModule,
  OrganizationChartModule,
  SelectButtonModule,
  ToastModule,
  CalendarModule,
  MultiSelectModule,
  TreeSelectModule,
  SliderModule,
  TabViewModule,
  TooltipModule,
  RadioButtonModule,
  TagModule,
  PaginatorModule
];

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    ...PRIME_NG_MODULES,
  ],
  exports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    ...PRIME_NG_MODULES,
  ],
})
export class SharedModule {}
