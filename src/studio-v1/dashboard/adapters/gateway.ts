import type { StudioAssetPage } from "../domain/assets";
import type { StudioBalance, StudioBillingHistory } from "../domain/billing";
import type { DashboardWorkSnapshot } from "../domain/dashboard";
import type { StudioBrandCollection, StudioCastCollection, StudioMemoryCollection, StudioMemoryScope, StudioSeriesCollection } from "../domain/creative-memory";

export interface StudioDashboardGateway {
  getWork(signal?: AbortSignal): Promise<DashboardWorkSnapshot>;
  getBrands(signal?: AbortSignal): Promise<StudioBrandCollection>;
  getCast(signal?: AbortSignal): Promise<StudioCastCollection>;
  getSeries(signal?: AbortSignal): Promise<StudioSeriesCollection>;
  getMemory(scope: StudioMemoryScope, scopeRefId: string, signal?: AbortSignal): Promise<StudioMemoryCollection>;
  getAssets(cursor?: string | null, signal?: AbortSignal): Promise<StudioAssetPage>;
  getBalance(signal?: AbortSignal): Promise<StudioBalance>;
  getBillingHistory(cursor?: string | null, signal?: AbortSignal): Promise<StudioBillingHistory>;
}
