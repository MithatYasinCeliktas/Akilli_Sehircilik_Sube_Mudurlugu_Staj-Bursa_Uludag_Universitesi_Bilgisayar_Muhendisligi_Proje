export enum UserRole {
  ADMIN = 'ADMIN',
  MANAGER = 'MANAGER',
  USER = 'USER',
  USER_MANAGER = 'USER_MANAGER'
}

export interface UnitBrief {
  id: number;
  name: string;
  code?: string;
}

export interface UserBrief {
  id: number;
  fullName?: string;
  full_name?: string;
  email: string;
}

export interface User {
  id: number;
  email: string;
  fullName?: string;
  full_name?: string;
  title?: string;
  role: UserRole;
  isActive?: boolean;
  is_active?: boolean;
  isSuperuser?: boolean;
  is_superuser?: boolean;
  unitId?: number;
  unit_id?: number;
  managerId?: number;
  manager_id?: number;
  ui_settings?: any;
  unit?: UnitBrief;
  manager?: UserBrief;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
  password?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// Backend'den dönen token yapısı (snake_case)
export interface AuthToken {
  access_token: string;
  token_type: string;
  user: User;
}