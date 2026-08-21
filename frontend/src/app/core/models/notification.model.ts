export interface Notification {
  id: number;
  user_id: number;
  message: string;
  is_read: boolean;
  type: string;
  reference_id?: number;
  created_at: string;
}
