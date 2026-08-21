export enum ReportStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED'
}

// Backend ile eşleşen 3 sabit faaliyet kategorisi
export enum ItemCategory {
  YAPILAN_ISLER = 'YAPILAN_ISLER',
  YAPILACAK_ISLER = 'YAPILACAK_ISLER',
  KORDINASYON_GEREKTIREN_ISLER = 'KORDINASYON_GEREKTIREN_ISLER'
}

export interface ReportItem {
  id?: number;
  reportId?: number;
  report_id?: number;
  creator_id?: number;
  creator?: any;
  transfer_manager?: any;
  status?: ReportStatus;
  rejection_note?: string;
  source_item_id?: number;
  category: ItemCategory;
  content: string;
  related_institutions?: string;
  solution_proposals?: string;
  display_order?: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface ReportItemReview {
  status: ReportStatus;
  rejection_note?: string;
}

export interface ActivityReport {
  id: number;
  userId?: number;
  user_id?: number;
  year: number;
  month: number;
  title?: string;
  status: ReportStatus;
  createdAt?: string;
  updatedAt?: string;
  user?: any;
  yapilan_isler: ReportItem[];
  yapilacak_isler: ReportItem[];
  koordinasyon_isleri: ReportItem[];
}

export interface ActivityReportCreate {
  year: number;
  month: number;
  title?: string;
  status: ReportStatus;
}

export interface ReportItemCreate {
  category: ItemCategory;
  content: string;
  related_institutions?: string;
  solution_proposals?: string;
  display_order?: number;
}

export interface ReportFilter {
  year?: number;
  month?: number;
  status?: ReportStatus;
  userIds?: number[];
  unitId?: number;
  category?: ItemCategory;
  searchText?: string;
  startDate?: string;
  endDate?: string;
  reportIds?: number[];
  page?: number;
  pageSize?: number;
}