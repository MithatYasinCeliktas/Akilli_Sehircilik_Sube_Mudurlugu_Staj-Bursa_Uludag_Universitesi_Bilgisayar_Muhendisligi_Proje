import { ActivityReport } from './report.model';
import { User } from './user.model';

export enum ShareStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  REVOKED = 'REVOKED'
}

export interface ReportShareCreate {
  report_id: number;
  target_user_id?: number | null;
  target_unit_id?: number | null;
}

export interface ReportShareAction {
  note?: string;
}

export interface ReportShareResponse {
  id: number;
  report_id: number;
  requester_id: number;
  manager_id: number | null;
  target_user_id: number | null;
  target_unit_id: number | null;
  status: ShareStatus;
  manager_note: string | null;
  created_at: string;
  updated_at: string;
  
  report?: ActivityReport;
  requester?: User;
  manager?: User;
  target_user?: User;
  target_unit?: any;
}
