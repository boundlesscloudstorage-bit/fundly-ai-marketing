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

export type Platform = "x" | "linkedin" | "instagram" | "facebook";
export type ContentObjective = "brand_awareness" | "engagement" | "education" | "product_promotion";
export type ContentTone = "professional" | "inspiring" | "friendly" | "persuasive";
export type DraftStatus = "draft" | "approved";

export interface ContentGenerationRequest {
  topic: string;
  platform: Platform;
  objective: ContentObjective;
  tone: ContentTone;
  keywords?: string;
}

export interface GeneratedContent {
  topic: string;
  caption: string;
  hashtags: string[];
  platform: Platform;
  objective: ContentObjective;
  tone: ContentTone;
  character_count: number;
  is_demo_generated: boolean;
}

export interface SaveDraftRequest {
  topic: string;
  caption: string;
  hashtags: string[];
  platform: Platform;
  objective: ContentObjective;
  tone: ContentTone;
  is_demo_generated?: boolean;
}

export interface SavedDraft extends GeneratedContent {
  id: string;
  brand_id: string;
  status: DraftStatus;
  created_at: string;
  updated_at: string;
}

export interface DraftListResponse {
  items: SavedDraft[];
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

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isString);
}

function isPlatform(value: unknown): value is Platform {
  return value === "x" || value === "linkedin" || value === "instagram" || value === "facebook";
}

function isObjective(value: unknown): value is ContentObjective {
  return value === "brand_awareness" || value === "engagement" || value === "education" || value === "product_promotion";
}

function isTone(value: unknown): value is ContentTone {
  return value === "professional" || value === "inspiring" || value === "friendly" || value === "persuasive";
}

function isDraftStatus(value: unknown): value is DraftStatus {
  return value === "draft" || value === "approved";
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

export function isGeneratedContent(value: unknown): value is GeneratedContent {
  return (
    isRecord(value) &&
    isString(value.topic) &&
    isString(value.caption) &&
    isStringArray(value.hashtags) &&
    isPlatform(value.platform) &&
    isObjective(value.objective) &&
    isTone(value.tone) &&
    typeof value.character_count === "number" &&
    Number.isInteger(value.character_count) &&
    value.character_count === Array.from(value.caption).length &&
    isBoolean(value.is_demo_generated)
  );
}

export function isSavedDraftResponse(value: unknown): value is SavedDraft {
  return (
    isRecord(value) &&
    isGeneratedContent(value) &&
    isString(value.id) &&
    isString(value.brand_id) &&
    isDraftStatus(value.status) &&
    isString(value.created_at) &&
    isString(value.updated_at)
  );
}

export function isDraftListResponse(value: unknown): value is DraftListResponse {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(isSavedDraftResponse) &&
    typeof value.total === "number" &&
    Number.isInteger(value.total) &&
    value.total >= 0 &&
    isBoolean(value.is_demo)
  );
}

export interface ApiRequestOptions {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  signal?: AbortSignal;
}

function errorDetail(payload: unknown): string | null {
  if (!isRecord(payload) || !("detail" in payload)) return null;
  if (isString(payload.detail)) return payload.detail;
  if (Array.isArray(payload.detail)) {
    const messages = payload.detail
      .filter(isRecord)
      .map((entry) => entry.msg)
      .filter(isString);
    if (messages.length) return messages.join("; ");
  }
  return null;
}

export async function requestApiData<T>(
  path: string,
  validate: (value: unknown) => value is T,
  options: ApiRequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });

  if (!response.ok) {
    let detail: string | null = null;
    try {
      detail = errorDetail(await response.json());
    } catch {
      // Return a status-based message if the server response is not JSON.
    }
    throw new Error(detail ?? `The API returned ${response.status} ${response.statusText}.`);
  }

  const payload: unknown = await response.json();
  if (!validate(payload)) {
    throw new Error("The API returned data in an unexpected format.");
  }

  return payload;
}

export function fetchApiData<T>(
  path: string,
  validate: (value: unknown) => value is T,
  signal: AbortSignal,
): Promise<T> {
  return requestApiData(path, validate, { signal });
}
