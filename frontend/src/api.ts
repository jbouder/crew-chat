/**
 * API service for the Member Center application
 */

import type {
  Member,
  Benefit,
  Enrollment,
  DashboardData,
  EnrollmentCreate,
  MemberLogin,
  BenefitCategory,
} from "./types";

// Use relative path for production (nginx proxy) or localhost for development
const API_BASE_URL = import.meta.env.PROD
  ? "/api"
  : "http://localhost:8000/api";

class ApiService {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "An error occurred" }));
      throw new Error(error.detail || "An error occurred");
    }

    return response.json();
  }

  // Member endpoints
  async login(credentials: MemberLogin): Promise<Member> {
    return this.request<Member>("/members/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  }

  async getMember(memberId: number): Promise<Member> {
    return this.request<Member>(`/members/${memberId}`);
  }

  async getMemberDashboard(memberId: number): Promise<DashboardData> {
    return this.request<DashboardData>(`/members/${memberId}/dashboard`);
  }

  // Benefits endpoints
  async getBenefits(category?: BenefitCategory): Promise<Benefit[]> {
    const params = category ? `?category=${encodeURIComponent(category)}` : "";
    return this.request<Benefit[]>(`/benefits${params}`);
  }

  async getBenefit(benefitId: number): Promise<Benefit> {
    return this.request<Benefit>(`/benefits/${benefitId}`);
  }

  // Enrollment endpoints
  async getMemberEnrollments(memberId: number): Promise<Enrollment[]> {
    return this.request<Enrollment[]>(`/members/${memberId}/enrollments`);
  }

  async createEnrollment(
    memberId: number,
    enrollment: EnrollmentCreate
  ): Promise<Enrollment> {
    return this.request<Enrollment>(`/members/${memberId}/enrollments`, {
      method: "POST",
      body: JSON.stringify(enrollment),
    });
  }

  async cancelEnrollment(
    memberId: number,
    enrollmentId: number
  ): Promise<{ message: string }> {
    return this.request<{ message: string }>(
      `/members/${memberId}/enrollments/${enrollmentId}`,
      {
        method: "DELETE",
      }
    );
  }
}

export const api = new ApiService();
