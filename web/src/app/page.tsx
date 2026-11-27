"use client";

import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import {
  API_BASE_URL,
  fetchApiData,
  isActivityListResponse,
  isCalendarListResponse,
  isCampaignListResponse,
  isContentListResponse,
  isOverviewResponse,
  rescheduleCalendarEntry,
  unscheduleCalendarEntry,
  type ApiResource,
  type ActivityListResponse,
  type Campaign,
  type CampaignListResponse,
  type CalendarEntry,
  type CalendarListResponse,
  type ContentItem,
  type ContentListResponse,
  type Metric,
  type OverviewResponse,
} from "@/lib/api";
import ContentWorkflow from "@/components/content-workflow";
import CampaignComposer from "@/components/campaign-composer";
import CampaignEditor from "@/components/campaign-editor";

function Mark({ small = false }: { small?: boolean }) {
  return <span className={`brand-mark${small ? " brand-mark-small" : ""}`} aria-hidden="true"><span>f</span></span>;
}

function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = window.localStorage.getItem("fundly-theme");
    const isDark = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    setDark(isDark);
    document.documentElement.dataset.theme = isDark ? "dark" : "light";
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
    window.localStorage.setItem("fundly-theme", next ? "dark" : "light");
  }

  return <button className="theme-toggle" type="button" onClick={toggle} aria-label={`Switch to ${dark ? "light" : "dark"} mode`} aria-pressed={dark}><span aria-hidden="true">{dark ? "☀" : "☾"}</span><span className="theme-toggle-label">{dark ? "Light" : "Dark"}</span></button>;
}

function Sidebar({ campaignCount, brandName }: { campaignCount: number | null; brandName: string }) {
  return (
    <aside className="sidebar">
      <a className="brand" href="#overview" aria-label="Fundly home"><Mark /><span className="brand-word">fundly<span className="brand-ai">.ai</span></span></a>
      <div className="workspace-label">WORKSPACE</div>
      <nav className="nav-list" aria-label="Main navigation">
        <a className="nav-item active" href="#overview"><span className="nav-icon">⌂</span>Overview</a>
        <a className="nav-item" href="#campaigns"><span className="nav-icon">◫</span>Campaigns<span className="nav-count">{campaignCount ?? "–"}</span></a>
        <a className="nav-item" href="#calendar"><span className="nav-icon">▦</span>Content calendar</a>
        <a className="nav-item" href="#studio"><span className="nav-icon">✳</span>Content studio<span className="nav-dot" /></a>
      </nav>
      <div className="sidebar-bottom">
        <div className="workspace-label">YOUR BRAND</div>
        <div className="brand-switcher" aria-label={`Current brand: ${brandName}`}><Mark small /><span><strong>{brandName}</strong><small>Brand workspace</small></span><span className="chevron">⌄</span></div>
        <div className="demo-note"><span className="demo-spark">✦</span><div><strong>Your creative copilot</strong><p>Draft ideas and stay on brand.</p></div></div>
        <div className="profile"><span className="avatar">JD</span><span><strong>Jamie Davis</strong><small>Marketing team</small></span><span className="more">···</span></div>
      </div>
    </aside>
  );
}

function SectionHeading({ eyebrow, title, action, href }: { eyebrow?: string; title: string; action?: string; href: string }) {
  return <div className="section-heading"><div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h2>{title}</h2></div>{action && <a className="text-link" href={href}>{action}<span> ↗</span></a>}</div>;
}

function RetryMessage({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <div className="resource-state resource-error" role="alert"><span>{message}</span><button type="button" onClick={onRetry}>Retry</button></div>;
}

function MetricCard({ metric, index }: { metric: Metric; index: number }) {
  const visuals = [
    { icon: "◉", tone: "lilac" },
    { icon: "▤", tone: "peach" },
    { icon: "↗", tone: "mint" },
    { icon: "◎", tone: "blue" },
  ];
  const visual = visuals[index % visuals.length];

  return (
    <article className="stat-card">
      <div className="stat-top"><span>{metric.label}</span><span className={`stat-icon ${visual.tone}`}>{visual.icon}</span></div>
      <div className="stat-value">{metric.value}</div>
      <div className="stat-change"><span>↗</span> {metric.change}</div>
      <span className="metric-caption">{metric.is_demo ? "DEMO METRIC" : "METRIC"}</span>
    </article>
  );
}

function LoadingMetrics() {
  return <>{[0, 1, 2, 3].map((item) => <div className="stat-card loading-card" key={item} aria-hidden="true"><span className="skeleton skeleton-label" /><span className="skeleton skeleton-value" /><span className="skeleton skeleton-detail" /></div>)}</>;
}

function campaignColor(index: number) {
  return ["purple", "orange", "green"][index % 3];
}

function CampaignRow({ campaign, index, onEdit }: { campaign: Campaign; index: number; onEdit: (campaign: Campaign) => void }) {
  const color = campaignColor(index);
  const targetDate = new Date(`${campaign.target_date}T12:00:00`);
  const dateLabel = Number.isNaN(targetDate.getTime())
    ? campaign.target_date
    : new Intl.DateTimeFormat("en", { month: "short", day: "2-digit" }).format(targetDate);

  return (
    <article className="campaign-row">
      <div className={`campaign-art ${color}`}><span>{color === "purple" ? "✳" : color === "orange" ? "↗" : "◌"}</span></div>
      <div className="campaign-info">
        <div className="campaign-name">{campaign.name}</div>
        <div className="campaign-meta">{campaign.channel}</div>
        <div className="progress-track"><span className={color} style={{ width: `${campaign.progress}%` }} /></div>
      </div>
      <div className="campaign-side"><span className={`status ${campaign.status.toLowerCase() === "planning" ? "planning" : ""}`}><i />{campaign.status}</span><span className="campaign-date">{dateLabel}</span><button className="campaign-edit-button" type="button" onClick={() => onEdit(campaign)}>Edit</button></div>
    </article>
  );
}

function contentColor(channel: string) {
  const normalized = channel.toLowerCase();
  if (normalized.includes("instagram")) return "pink";
  if (normalized.includes("linkedin")) return "blue";
  return "yellow";
}

function formatScheduledDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return { weekday: "—", day: "—", month: "—", time: "Time TBD" };

  return {
    weekday: new Intl.DateTimeFormat("en", { weekday: "short" }).format(date).toUpperCase(),
    day: new Intl.DateTimeFormat("en", { day: "2-digit" }).format(date),
    month: new Intl.DateTimeFormat("en", { month: "short" }).format(date).toUpperCase(),
    time: new Intl.DateTimeFormat("en", { hour: "numeric", minute: "2-digit" }).format(date),
  };
}

function localDateTimeValue(value: string) {
  const date = new Date(value);
  const pad = (part: number) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function timezoneIso(value: string) {
  const date = new Date(value);
  const offset = -date.getTimezoneOffset();
  const sign = offset >= 0 ? "+" : "-";
  const absolute = Math.abs(offset);
  return `${value}:00${sign}${String(Math.floor(absolute / 60)).padStart(2, "0")}:${String(absolute % 60).padStart(2, "0")}`;
}

function CalendarPost({ item, onUpdated, onRemoved }: { item: CalendarEntry; onUpdated: (entry: CalendarEntry) => void; onRemoved: (id: string) => void }) {
  const [editing, setEditing] = useState(false);
  const [scheduledFor, setScheduledFor] = useState(() => localDateTimeValue(item.scheduled_for));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const date = formatScheduledDate(item.scheduled_for);
  async function reschedule() {
    setBusy(true); setError("");
    try { onUpdated(await rescheduleCalendarEntry(item.id, timezoneIso(scheduledFor))); setEditing(false); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not reschedule this entry."); }
    finally { setBusy(false); }
  }
  async function unschedule() {
    if (!window.confirm("Remove this entry from the local calendar?")) return;
    setBusy(true); setError("");
    try { await unscheduleCalendarEntry(item.id); onRemoved(item.id); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not unschedule this entry."); }
    finally { setBusy(false); }
  }
  return (
    <article className="upcoming-row">
      <div className="date-tile"><span>{date.weekday}</span><strong>{date.day}</strong><small>{date.month}</small></div>
      <div className="upcoming-info"><strong>{item.title}</strong><span><i className={`channel-dot ${contentColor(item.channel)}`} />{item.channel}<span className="meta-sep">·</span>{date.time}</span></div>
      <div className="calendar-actions"><button type="button" disabled={busy} onClick={() => setEditing((value) => !value)}>{editing ? "Close" : "Edit"}</button><button type="button" disabled={busy} onClick={unschedule}>Unschedule</button></div>
      {editing && <div className="calendar-reschedule"><input type="datetime-local" value={scheduledFor} onChange={(event) => setScheduledFor(event.target.value)} /><button type="button" disabled={busy || !scheduledFor} onClick={reschedule}>{busy ? "Saving…" : "Save"}</button></div>}
      {error && <span className="calendar-error" role="alert">{error}</span>}
    </article>
  );
}

function ContentDraft({ item }: { item: ContentItem }) {
  const color = contentColor(item.channel);
  return (
    <article className="draft-card">
      <div className="draft-head"><span className={`draft-icon ${color}`}>{color === "pink" ? "◎" : color === "blue" ? "in" : "✉"}</span><span className="draft-type">{item.is_ai_generated_example ? "SAMPLE AI DRAFT" : "DRAFT"} · {item.channel.toUpperCase()}</span><span className="draft-menu">···</span></div>
      <h3>{item.title}</h3><p>{item.body}</p>
      <div className="draft-footer"><span className="tone-tag"><i />{item.is_ai_generated_example ? "AI example" : "Demo content"}</span><span className="draft-type">SAMPLE ONLY</span></div>
    </article>
  );
}

export default function Home() {
  const [overview, setOverview] = useState<ApiResource<OverviewResponse>>({ status: "loading" });
  const [campaigns, setCampaigns] = useState<ApiResource<CampaignListResponse>>({ status: "loading" });
  const [content, setContent] = useState<ApiResource<ContentListResponse>>({ status: "loading" });
  const [calendar, setCalendar] = useState<ApiResource<CalendarListResponse>>({ status: "loading" });
  const [activity, setActivity] = useState<ApiResource<ActivityListResponse>>({ status: "loading" });
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null);
  const [retryKey, setRetryKey] = useState(0);
  const retry = () => setRetryKey((value) => value + 1);

  function addCampaign(campaign: Campaign) {
    setCampaigns((current) => {
      const existing = current.status === "success" ? current.data.items : [];
      const items = [campaign, ...existing.filter((item) => item.id !== campaign.id)];
      return {
        status: "success",
        data: {
          items,
          total: current.status === "success" ? current.data.total + 1 : 1,
          is_demo: true,
        },
      };
    });
  }

  function replaceCampaign(updated: Campaign) {
    setCampaigns((current) => current.status === "success"
      ? { ...current, data: { ...current.data, items: current.data.items.map((item) => item.id === updated.id ? updated : item) } }
      : current);
  }

  function replaceCalendar(updated: CalendarEntry) {
    setCalendar((current) => current.status === "success"
      ? { ...current, data: { ...current.data, items: current.data.items.map((item) => item.id === updated.id ? updated : item) } }
      : current);
  }

  function removeCalendar(id: string) {
    setCalendar((current) => current.status === "success"
      ? { ...current, data: { ...current.data, items: current.data.items.filter((item) => item.id !== id), total: current.data.total - 1 } }
      : current);
  }

  useEffect(() => {
    const controller = new AbortController();

    function load<T>(
      path: string,
      validate: (value: unknown) => value is T,
      setResource: Dispatch<SetStateAction<ApiResource<T>>>,
    ) {
      setResource({ status: "loading" });
      fetchApiData(path, validate, controller.signal)
        .then((data) => setResource({ status: "success", data }))
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          const detail = error instanceof Error ? error.message : "An unexpected error occurred.";
          setResource({ status: "error", message: `${detail} Check that the API is running at ${API_BASE_URL}.` });
        });
    }

    load("/api/dashboard/overview", isOverviewResponse, setOverview);
    load("/api/campaigns", isCampaignListResponse, setCampaigns);
    load("/api/content", isContentListResponse, setContent);
    load("/api/calendar", isCalendarListResponse, setCalendar);
    load("/api/dashboard/activity", isActivityListResponse, setActivity);

    return () => controller.abort();
  }, [retryKey]);

  const brandName = overview.status === "success" ? overview.data.brand_name : "Fundly";
  const campaignCount = campaigns.status === "success" ? campaigns.data.total : null;
  const scheduledContent = calendar.status === "success"
    ? calendar.data.items.filter((item) => item.status.toLowerCase() === "scheduled")
    : [];
  const draftContent = content.status === "success"
    ? content.data.items.filter((item) => item.status.toLowerCase() === "draft")
    : [];

  return (
    <div className="app-shell">
      <Sidebar campaignCount={campaignCount} brandName={brandName} />
      <main className="main-content" id="overview">
        <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> <strong>{overview.status === "success" ? overview.data.period : "Overview"}</strong></div><div className="topbar-right"><ThemeToggle /><span className="demo-pill"><i /> DEMO DATA</span><span className="icon-button" aria-label="Notifications">♧<i /></span><span className="top-avatar">JD</span></div></header>
        <div className="page-wrap">
          <section className="welcome-row"><div><div className="eyebrow">SATURDAY, OCTOBER 24, 2026 <span className="welcome-spark">✦</span></div><h1>Good morning, Jamie <span>☀️</span></h1><p>Here’s what’s happening with your marketing today.</p></div><CampaignComposer onCreated={addCampaign} /></section>

          <div className="demo-banner"><span className="banner-icon">✦</span><span><strong>Your workspace, ready to explore.</strong> Everything you see here is sample data. AI and social integrations aren’t connected.</span><a href="#studio">Explore the studio <span>→</span></a></div>

          <section className="stats-grid" aria-label="Demo performance metrics">
            {overview.status === "loading" && <LoadingMetrics />}
            {overview.status === "error" && <RetryMessage message={overview.message} onRetry={retry} />}
            {overview.status === "success" && overview.data.metrics.length === 0 && <div className="resource-state">No overview metrics are available yet.</div>}
            {overview.status === "success" && overview.data.metrics.map((metric, index) => <MetricCard metric={metric} index={index} key={metric.label} />)}
          </section>

          <div className="content-grid">
            <section className="panel campaign-panel" id="campaigns"><SectionHeading eyebrow="IN MOTION" title="Campaigns" action="All campaigns" href="#campaigns"/><div className="campaign-list">
              {campaigns.status === "loading" && <div className="resource-state">Loading campaigns…</div>}
              {campaigns.status === "error" && <RetryMessage message={campaigns.message} onRetry={retry} />}
              {campaigns.status === "success" && campaigns.data.items.length === 0 && <div className="resource-state">No campaigns are available yet.</div>}
              {campaigns.status === "success" && campaigns.data.items.map((campaign, index) => <CampaignRow campaign={campaign} index={index} onEdit={setEditingCampaign} key={campaign.id} />)}
            </div><div className="panel-footnote"><span>ⓘ</span> Campaign details are demonstration data.</div></section>

            <section className="panel calendar-panel" id="calendar"><SectionHeading eyebrow="UP NEXT" title="On the calendar" action="View calendar" href="#calendar"/><div className="upcoming-list">
              {calendar.status === "loading" && <div className="resource-state">Loading local calendar…</div>}
              {content.status === "loading" && <div className="resource-state">Loading scheduled content…</div>}
              {calendar.status === "error" && <RetryMessage message={calendar.message} onRetry={retry} />}
              {calendar.status === "success" && scheduledContent.length === 0 && <div className="resource-state">No scheduled posts are available yet.</div>}
              {calendar.status === "success" && scheduledContent.map((item) => <CalendarPost item={item} onUpdated={replaceCalendar} onRemoved={removeCalendar} key={item.id} />)}
            </div><div className="panel-footnote"><span>◷</span> Local planning calendar; nothing is published.</div></section>
          </div>

          <section className="panel activity-panel" id="activity" aria-labelledby="activity-title">
            <SectionHeading eyebrow="RECENT ACTIVITY" title="Workspace timeline" href="#activity" />
            {activity.status === "loading" && <div className="resource-state">Loading activity…</div>}
            {activity.status === "error" && <RetryMessage message={activity.message} onRetry={retry} />}
            {activity.status === "success" && activity.data.items.length === 0 && <div className="resource-state">No workspace activity yet.</div>}
            {activity.status === "success" && activity.data.items.length > 0 && <div className="activity-list">{activity.data.items.map((item) => <article className="activity-item" key={item.id}><span className={`activity-dot ${item.kind}`} /><div><strong>{item.title}</strong><p>{item.detail}</p></div><time dateTime={item.occurred_at}>{new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(item.occurred_at))}</time></article>)}</div>}
            <div className="panel-footnote"><span>◷</span> Activity is local workspace data; no publishing occurs.</div>
          </section>

          <section className="studio-section" id="studio">
            <div className="studio-intro"><div><div className="eyebrow"><span className="eyebrow-star">✦</span> YOUR CREATIVE CORNER</div><h2>Content studio</h2><p>Create a demo draft, refine it, and keep it in your workspace.</p></div></div>
            <ContentWorkflow />
            <section className="sample-api-drafts" aria-labelledby="sample-drafts-title">
              <div className="saved-drafts-heading"><div><div className="eyebrow">CONTENT FEED</div><h3 id="sample-drafts-title">Sample content examples</h3></div></div>
              <div className="draft-grid">
                {content.status === "loading" && <div className="resource-state">Loading content examples…</div>}
                {content.status === "error" && <RetryMessage message={content.message} onRetry={retry} />}
                {content.status === "success" && draftContent.length === 0 && <div className="resource-state">No sample drafts are available from the content feed.</div>}
                {content.status === "success" && draftContent.map((item) => <ContentDraft item={item} key={item.id} />)}
              </div>
              <div className="studio-disclaimer"><span>✦</span> Content feed examples are separate from saved drafts.</div>
            </section>
          </section>
          {editingCampaign && <CampaignEditor campaign={editingCampaign} onClose={() => setEditingCampaign(null)} onUpdated={replaceCampaign} />}
          <footer className="page-footer"><span><Mark small /> Made for meaningful momentum.</span><span>Fundly AI Marketing Agent <i>·</i> Local demo</span></footer>
        </div>
      </main>
    </div>
  );
}
