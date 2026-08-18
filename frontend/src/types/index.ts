export type UserRole = "admin" | "sales_agent" | "accountant" | "client";

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  phone_number?: string;
  email_notifications_enabled: boolean;
}

export type LotStatus = "available" | "reserved" | "sold" | "on_hold";

export interface Lot {
  id: string;
  project: string;
  block_number: string;
  lot_number: string;
  area_sqm: string;
  price_per_sqm: string;
  total_price: string;
  status: LotStatus;
  photos: string[];
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