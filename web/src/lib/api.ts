export interface Metric {
  label: string;
  value: string;
  change: string;
  is_demo: boolean;
}

export interface OverviewResponse {
  brand_id: string;
  brand_name: string;
  period: string;
  metrics: Metric[];
  is_demo: boolean;
}

export interface Campaign {
  id: string;
  brand_id: string;
  name: string;
  channel: string;
  status: string;
  progress: number;
  target_date: string;
  is_demo: boolean;
}

export interface CampaignListResponse {
  items: Campaign[];
  total: number;
  is_demo: boolean;
}

export interface ContentItem {
  id: string;
  brand_id: string;
  channel: string;
  title: string;
  body: string;
  status: string;
  scheduled_for: string;
  is_ai_generated_example: boolean;
}

export interface ContentListResponse {
  items: ContentItem[];
  total: number;
  is_demo: boolean;
}

export type ApiResource<T> =
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; message: string };

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isBoolean(value: unknown): value is boolean {
  return typeof value === "boolean";
}

function isMetric(value: unknown): value is Metric {
  return (
    isRecord(value) &&
    isString(value.label) &&
    isString(value.value) &&
    isString(value.change) &&
    isBoolean(value.is_demo)
  );
}

export function isOverviewResponse(value: unknown): value is OverviewResponse {
  return (
    isRecord(value) &&
    isString(value.brand_id) &&
    isString(value.brand_name) &&
    isString(value.period) &&
    Array.isArray(value.metrics) &&
    value.metrics.every(isMetric) &&
    isBoolean(value.is_demo)
  );
}

function isCampaign(value: unknown): value is Campaign {
  return (
    isRecord(value) &&
    isString(value.id) &&
    isString(value.brand_id) &&
    isString(value.name) &&
    isString(value.channel) &&
    isString(value.status) &&
    typeof value.progress === "number" &&
    Number.isInteger(value.progress) &&
    value.progress >= 0 &&
    value.progress <= 100 &&
    isString(value.target_date) &&
    isBoolean(value.is_demo)
  );
}

export function isCampaignListResponse(value: unknown): value is CampaignListResponse {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(isCampaign) &&
    typeof value.total === "number" &&
    Number.isInteger(value.total) &&
    value.total >= 0 &&
    isBoolean(value.is_demo)
  );
}

function isContentItem(value: unknown): value is ContentItem {
  return (
    isRecord(value) &&
    isString(value.id) &&
    isString(value.brand_id) &&
    isString(value.channel) &&
    isString(value.title) &&
    isString(value.body) &&
    isString(value.status) &&
    isString(value.scheduled_for) &&
    isBoolean(value.is_ai_generated_example)
  );
}

export function isContentListResponse(value: unknown): value is ContentListResponse {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(isContentItem) &&
    typeof value.total === "number" &&
    Number.isInteger(value.total) &&
    value.total >= 0 &&
    isBoolean(value.is_demo)
  );
}

export async function fetchApiData<T>(
  path: string,
  validate: (value: unknown) => value is T,
  signal: AbortSignal,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: { Accept: "application/json" },
    signal,
  });

  if (!response.ok) {
    throw new Error(`The API returned ${response.status} ${response.statusText}.`);
  }

  const payload: unknown = await response.json();
  if (!validate(payload)) {
    throw new Error("The API returned data in an unexpected format.");
  }

  return payload;
}
