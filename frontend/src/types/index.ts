export type UserRole = "admin" | "sales_agent" | "accountant" | "client";

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  phone_number?: string;
  is_active: boolean;
  email_notifications_enabled: boolean;
}

export type LotStatus = "available" | "reserved" | "sold" | "on_hold";

export interface LotImage {
  id: string;
  image: string;
  is_thumbnail: boolean;
}

export interface Lot {
  id: string;
  project: string;
  project_name?: string;
  block_number: string;
  lot_number: string;
  area_sqm: string;
  price_per_sqm: string;
  total_price: string;
  status: LotStatus;
  thumbnail: string | null;
  description?: string;
  floor_plan?: string | null;
  images?: LotImage[];
}

export interface Reservation {
  id: string;
  lot: string;
  lot_display: string;
  lot_detail?: Lot;
  reservation_fee: string;
  deadline: string;
  status: "pending_payment" | "active" | "converted" | "expired" | "cancelled";
  created_at: string;
  extension_count: number;
  dismissed_by_client: boolean;
  can_extend: boolean;
  max_extensions: number;
}

export interface Project {
  id: string;
  name: string;
  slug: string;
  location: string;
  description: string;
  is_published: boolean;
}

export type ContractStatus = "draft" | "active" | "completed" | "cancelled" | "defaulted";

export interface Contract {
  id: string;
  contract_number: string;
  lot: string;
  lot_display?: string;
  client: string;
  client_name?: string;
  agent?: string | null;
  payment_plan_type: "full_payment" | "installment";
  total_contract_price: string;
  down_payment: string;
  term_months: number;
  status: ContractStatus;
  financed_amount?: string;
  total_paid?: string;
  outstanding_balance?: string;
  installments?: Installment[];
}

export interface Installment {
  id: string;
  contract?: string;
  installment_number: number;
  due_date: string;
  principal_amount?: string;
  fees_amount?: string;
  penalty_amount?: string;
  amount_due: string;
  amount_paid: string;
  balance?: string;
  status: "pending" | "paid" | "partially_paid" | "overdue";
}

export interface Receipt {
  id: string;
  payment: string;
  contract: string;
  contract_number: string;
  lot_display: string | null;
  receipt_number: string;
  pdf_file: string | null;
  issued_at: string;
}

export interface Notification {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  related_object_id: string;
  created_at: string;
}