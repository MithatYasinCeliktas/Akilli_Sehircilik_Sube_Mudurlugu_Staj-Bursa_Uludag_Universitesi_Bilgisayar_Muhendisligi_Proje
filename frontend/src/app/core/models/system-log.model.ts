export interface SystemLog {
  id: number;
  created_at: string;
  action: string;
  user_id?: number;
  entity_type?: string;
  entity_id?: number;
  details?: any;
  user?: any; // The user object if included
}

export interface LogFilter {
  user_id?: number;
  action?: string;
  entity_type?: string;
  entity_id?: number;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}
