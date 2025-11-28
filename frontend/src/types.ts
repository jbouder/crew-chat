/**
 * TypeScript types for the Member Center application
 */

export enum MilitaryBranch {
  ARMY = "Army",
  NAVY = "Navy",
  AIR_FORCE = "Air Force",
  MARINE_CORPS = "Marine Corps",
  COAST_GUARD = "Coast Guard",
  SPACE_FORCE = "Space Force",
}

export enum MembershipStatus {
  ACTIVE = "Active",
  INACTIVE = "Inactive",
  PENDING = "Pending",
  SUSPENDED = "Suspended",
}

export enum BenefitCategory {
  LIFE_INSURANCE = "Life Insurance",
  DISABILITY = "Disability",
  ACCIDENT = "Accident",
  CRITICAL_ILLNESS = "Critical Illness",
  SUPPLEMENTAL = "Supplemental",
}

export interface Member {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  military_branch: MilitaryBranch;
  service_start_date?: string;
  service_end_date?: string;
  rank?: string;
  is_active_duty: boolean;
  member_number: string;
  membership_status: MembershipStatus;
  membership_start_date?: string;
}

export interface Benefit {
  id: number;
  name: string;
  description?: string;
  category: BenefitCategory;
  coverage_amount: number;
  monthly_premium: number;
  deductible: number;
  min_age: number;
  max_age: number;
  requires_active_duty: boolean;
  plan_code: string;
  is_active: boolean;
}

export interface Enrollment {
  id: number;
  member_id: number;
  benefit_id: number;
  enrollment_date: string;
  effective_date: string;
  termination_date?: string;
  is_active: boolean;
  coverage_amount: number;
  monthly_premium: number;
  beneficiary_name?: string;
  beneficiary_relationship?: string;
  benefit?: Benefit;
}

export interface DashboardData {
  member: Member;
  enrollments: Enrollment[];
  total_monthly_premium: number;
  total_coverage: number;
}

export interface EnrollmentCreate {
  benefit_id: number;
  beneficiary_name?: string;
  beneficiary_relationship?: string;
}

export interface MemberLogin {
  email: string;
  password: string;
}
