"use client";

import { useEffect, useState, type FormEvent } from "react";
import {
  API_BASE_URL,
  fetchApiData,
  isDraftListResponse,
  isGeneratedContent,
  isSavedDraftResponse,
  requestApiData,
  scheduleDraft as scheduleDraftRequest,
  type ApiResource,
  type ContentGenerationRequest,
  type ContentObjective,
  type ContentTone,
  type DraftListResponse,
  type DraftStatus,
  type GeneratedContent,
  type SavedDraft,
} from "@/lib/api";

const platforms = [
  ["x", "X"],
  ["linkedin", "LinkedIn"],
  ["instagram", "Instagram"],
  ["facebook", "Facebook"],
] as const;

const objectives: [ContentObjective, string][] = [
  ["brand_awareness", "Brand awareness"],
  ["engagement", "Engagement"],
  ["education", "Education"],
  ["product_promotion", "Product promotion"],
];

const tones: [ContentTone, string][] = [
  ["professional", "Professional"],
  ["inspiring", "Inspiring"],
  ["friendly", "Friendly"],
  ["persuasive", "Persuasive"],
];

function displayLabel(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function parseHashtags(value: string) {
  return [...new Set(value.split(/[\s,]+/).map((tag) => tag.trim()).filter(Boolean))];
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

function localDateTimeOffset(days: number) {
  const value = new Date(Date.now() + days * 24 * 60 * 60 * 1000);
  value.setSeconds(0, 0);
  value.setHours(9, 0, 0, 0);
  const pad = (part: number) => String(part).padStart(2, "0");
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}`;
}

function toTimezoneIso(value: string) {
  const local = new Date(value);
  const offset = -local.getTimezoneOffset();
  const sign = offset >= 0 ? "+" : "-";
  const absolute = Math.abs(offset);
  return `${value}:00${sign}${String(Math.floor(absolute / 60)).padStart(2, "0")}:${String(absolute % 60).padStart(2, "0")}`;
}

function DraftCard({
  draft,
  onSave,
  onApprove,
  onSchedule,
}: {
  draft: SavedDraft;
  onSave: (draftId: string, caption: string, hashtags: string[]) => Promise<SavedDraft>;
  onApprove: (draftId: string) => Promise<void>;
  onSchedule: (draftId: string, scheduledFor: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [caption, setCaption] = useState(draft.caption);
  const [hashtags, setHashtags] = useState(draft.hashtags.join(" "));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [scheduling, setScheduling] = useState(false);
  const [scheduledFor, setScheduledFor] = useState(() => localDateTimeOffset(1));

  useEffect(() => {
    setCaption(draft.caption);
    setHashtags(draft.hashtags.join(" "));
    setEditing(false);
    setError("");
  }, [draft]);

  async function saveChanges() {
    setBusy(true);
    setError("");
    try {
      await onSave(draft.id, caption, parseHashtags(hashtags));
      setEditing(false);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function approve() {
    setBusy(true);
    setError("");
    try {
      await onApprove(draft.id);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function schedule() {
    setBusy(true);
    setError("");
    try {
      await onSchedule(draft.id, toTimezoneIso(scheduledFor));
      setScheduling(false);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="saved-draft-card">
      <div className="saved-draft-top">
        <div>
          <div className="saved-draft-topic">{draft.topic}</div>
          <div className="saved-draft-meta">{displayLabel(draft.platform)} <span>·</span> {displayLabel(draft.tone)}</div>
        </div>
        <span className={`draft-status ${draft.status}`}>{draft.status}</span>
      </div>
      {editing ? (
        <div className="saved-draft-edit">
          <label>Caption<textarea value={caption} maxLength={2800} onChange={(event) => setCaption(event.target.value)} /></label>
          <label>Hashtags<input value={hashtags} onChange={(event) => setHashtags(event.target.value)} aria-describedby={`hashtags-help-${draft.id}`} /></label>
          <span className="field-help" id={`hashtags-help-${draft.id}`}>Separate tags with spaces or commas.</span>
        </div>
      ) : (
        <>
          <p className="saved-draft-caption">{draft.caption}</p>
          <div className="saved-draft-hashtags">{draft.hashtags.join(" ")}</div>
          <div className="saved-draft-count">{draft.character_count} characters · Updated {new Date(draft.updated_at).toLocaleString()}</div>
        </>
      )}
      {error && <div className="workflow-error" role="alert">{error}</div>}
      <div className="saved-draft-actions">
        {editing ? (
          <>
            <button className="secondary-action" type="button" disabled={busy} onClick={() => { setEditing(false); setCaption(draft.caption); setHashtags(draft.hashtags.join(" ")); }}>Cancel</button>
            <button className="workflow-button compact" type="button" disabled={busy || !caption.trim()} onClick={saveChanges}>{busy ? "Saving…" : "Save changes"}</button>
          </>
        ) : (
          <>
            <button className="secondary-action" type="button" disabled={busy} onClick={() => setEditing(true)}>Edit</button>
            {draft.status === "draft" && <button className="workflow-button compact" type="button" disabled={busy} onClick={approve}>{busy ? "Updating…" : "Mark approved"}</button>}
            {draft.status === "approved" && <button className="workflow-button compact" type="button" disabled={busy} onClick={() => setScheduling((value) => !value)}>{scheduling ? "Hide picker" : "Schedule locally"}</button>}
          </>
        )}
      </div>
      {scheduling && draft.status === "approved" && <div className="schedule-picker">
        <label className="workflow-field">Date and time<input type="datetime-local" value={scheduledFor} min={localDateTimeOffset(0)} onChange={(event) => setScheduledFor(event.target.value)} /></label>
        <button className="workflow-button compact" type="button" disabled={busy || !scheduledFor} onClick={schedule}>{busy ? "Scheduling…" : "Confirm local schedule"}</button>
        <span className="field-help">This adds a local planning entry only. Nothing is published.</span>
      </div>}
    </article>
  );
}

export default function ContentWorkflow() {
  const [drafts, setDrafts] = useState<ApiResource<DraftListResponse>>({ status: "loading" });
  const [refreshKey, setRefreshKey] = useState(0);
  const [form, setForm] = useState<ContentGenerationRequest>({
    topic: "",
    platform: "instagram",
    objective: "brand_awareness",
    tone: "friendly",
    keywords: "",
  });
  const [generated, setGenerated] = useState<GeneratedContent | null>(null);
  const [caption, setCaption] = useState("");
  const [hashtags, setHashtags] = useState("");
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const captionCharacterCount = Array.from(caption).length;

  useEffect(() => {
    const controller = new AbortController();
    setDrafts({ status: "loading" });
    fetchApiData("/api/drafts", isDraftListResponse, controller.signal)
      .then((data) => setDrafts({ status: "success", data }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setDrafts({ status: "error", message: `${errorMessage(error)} Check the API at ${API_BASE_URL}.` });
      });
    return () => controller.abort();
  }, [refreshKey]);

  function refreshDrafts() {
    setRefreshKey((current) => current + 1);
  }

  async function generate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setGenerating(true);
    setFormError("");
    setSuccessMessage("");
    setGenerated(null);

    try {
      const request: ContentGenerationRequest = {
        ...form,
        topic: form.topic.trim(),
        keywords: form.keywords?.trim() || undefined,
      };
      const result = await requestApiData("/api/content/generate", isGeneratedContent, { method: "POST", body: request });
      setGenerated(result);
      setCaption(result.caption);
      setHashtags(result.hashtags.join(" "));
    } catch (error) {
      setFormError(errorMessage(error));
    } finally {
      setGenerating(false);
    }
  }

  async function saveGenerated() {
    if (!generated) return;
    setSaving(true);
    setFormError("");
    setSuccessMessage("");
    try {
      await requestApiData("/api/drafts", isSavedDraftResponse, {
        method: "POST",
        body: {
          topic: generated.topic,
          caption: caption.trim(),
          hashtags: parseHashtags(hashtags),
          platform: generated.platform,
          objective: generated.objective,
          tone: generated.tone,
          is_demo_generated: generated.is_demo_generated,
        },
      });
      setSuccessMessage("Draft saved to the configured database.");
      refreshDrafts();
    } catch (error) {
      setFormError(errorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  function applyDraftUpdate(updatedDraft: SavedDraft) {
    setDrafts((current) => current.status === "success"
      ? {
          status: "success",
          data: {
            ...current.data,
            items: current.data.items.map((draft) => draft.id === updatedDraft.id ? updatedDraft : draft),
          },
        }
      : current);
  }

  async function updateDraft(draftId: string, updatedCaption: string, updatedHashtags: string[]): Promise<SavedDraft> {
    const updatedDraft = await requestApiData(`/api/drafts/${encodeURIComponent(draftId)}`, isSavedDraftResponse, {
      method: "PATCH",
      body: { caption: updatedCaption.trim(), hashtags: updatedHashtags },
    });
    applyDraftUpdate(updatedDraft);
    return updatedDraft;
  }

  async function approveDraft(draftId: string) {
    const updatedDraft = await requestApiData(`/api/drafts/${encodeURIComponent(draftId)}`, isSavedDraftResponse, {
      method: "PATCH",
      body: { status: "approved" satisfies DraftStatus },
    });
    applyDraftUpdate(updatedDraft);
  }

  async function scheduleDraft(draftId: string, scheduledFor: string) {
    await scheduleDraftRequest({ draft_id: draftId, scheduled_for: scheduledFor });
    setSuccessMessage("Draft scheduled in the local planning calendar. Nothing was published.");
  }

  return (
    <div className="content-workflow">
      <div className="workflow-demo-note"><span>AI CONTENT STUDIO</span> Drafts are generated through the backend’s configured Gemini provider. Review every draft before saving or approving. Saved drafts use the configured database; approval does not publish content.</div>

      <div className="workflow-panel">
        <div className="workflow-panel-heading"><div><div className="eyebrow">CREATE A DRAFT</div><h3>What would you like to share?</h3><p>Shape a brand-safe starting point, then edit it before saving.</p></div><span className="workflow-spark">✦</span></div>
        <form className="generator-form" onSubmit={generate}>
          <label className="workflow-field topic-field">Topic or campaign subject<input value={form.topic} minLength={3} maxLength={160} required placeholder="e.g. building a monthly budget" onChange={(event) => setForm({ ...form, topic: event.target.value })} /></label>
          <div className="workflow-select-grid">
            <label className="workflow-field">Platform<select value={form.platform} onChange={(event) => setForm({ ...form, platform: event.target.value as ContentGenerationRequest["platform"] })}>{platforms.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            <label className="workflow-field">Objective<select value={form.objective} onChange={(event) => setForm({ ...form, objective: event.target.value as ContentObjective })}>{objectives.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            <label className="workflow-field">Tone<select value={form.tone} onChange={(event) => setForm({ ...form, tone: event.target.value as ContentTone })}>{tones.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
          </div>
          <label className="workflow-field">Optional keywords or campaign notes<textarea value={form.keywords} maxLength={240} rows={2} placeholder="Add a few helpful words or constraints" onChange={(event) => setForm({ ...form, keywords: event.target.value })} /></label>
          {formError && <div className="workflow-error" role="alert">{formError}</div>}
          {successMessage && <div className="workflow-success" role="status">{successMessage}</div>}
          <button className="workflow-button" type="submit" disabled={generating || form.topic.trim().length < 3}>{generating ? "Generating content…" : formError && !generated ? "Try generation again" : "✦  Generate content"}</button>
        </form>

        {generated && <section className="generated-result" aria-label="Generated marketing content">
          <div className="generated-result-head"><div><span className="result-badge">{generated.is_demo_generated ? "DEMO EXAMPLE" : "AI-GENERATED DRAFT"}</span><h4>Your starting point</h4></div><span className="result-platform">{displayLabel(generated.platform)} <i>·</i> {displayLabel(generated.objective)} <i>·</i> {displayLabel(generated.tone)}</span></div>
          <label className="workflow-field">Caption<textarea value={caption} maxLength={2800} rows={5} onChange={(event) => setCaption(event.target.value)} /></label>
          <label className="workflow-field">Suggested hashtags<input value={hashtags} maxLength={360} onChange={(event) => setHashtags(event.target.value)} aria-describedby="generator-hashtag-help" /></label>
          <div className="field-help" id="generator-hashtag-help">Edit or remove tags; separate them with spaces or commas.</div>
          <div className={`character-count ${generated.platform === "x" && captionCharacterCount > 280 ? "over-limit" : ""}`} aria-live="polite">{captionCharacterCount} characters{generated.platform === "x" ? " · X limit 280" : ""}</div>
          <div className="generated-result-actions"><button className="workflow-button" type="button" disabled={saving || !caption.trim() || (generated.platform === "x" && captionCharacterCount > 280)} onClick={saveGenerated}>{saving ? "Saving…" : "Save draft"}</button><span>Review and edit the text before saving.</span></div>
        </section>}
      </div>

      <section className="saved-drafts-section" aria-labelledby="saved-drafts-title">
        <div className="saved-drafts-heading"><div><div className="eyebrow">YOUR WORKSPACE</div><h3 id="saved-drafts-title">Saved drafts</h3></div>{drafts.status === "success" && <span className="draft-total">{drafts.data.total} {drafts.data.total === 1 ? "draft" : "drafts"}</span>}</div>
        {drafts.status === "loading" && <div className="resource-state">Loading saved drafts…</div>}
        {drafts.status === "error" && <div className="resource-state resource-error" role="alert"><span>{drafts.message}</span><button type="button" onClick={refreshDrafts}>Retry</button></div>}
        {drafts.status === "success" && drafts.data.items.length === 0 && <div className="workflow-empty"><span>✦</span><strong>No saved drafts yet</strong><p>Generate a draft, review it, and save it here.</p></div>}
        {drafts.status === "success" && drafts.data.items.length > 0 && <div className="saved-drafts-grid">{drafts.data.items.map((draft) => <DraftCard key={draft.id} draft={draft} onSave={updateDraft} onApprove={approveDraft} onSchedule={scheduleDraft} />)}</div>}
      </section>
    </div>
  );
}
