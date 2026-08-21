export interface Institution {
  id: number;
  name: string;
  is_active: boolean;
  created_by_id: number | null;
  created_at: string;
  updated_at: string;
}
