"use client";

import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
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
  type ActivityItem,
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

function monthGrid(month: string) {
  const start = new Date(`${month}-01T12:00:00`);
  const offset = start.getDay();
  const count = new Date(start.getFullYear(), start.getMonth() + 1, 0).getDate();
  return Array.from({ length: Math.ceil((offset + count) / 7) * 7 }, (_, index) => {
    const day = index - offset + 1;
    return day > 0 && day <= count ? `${month}-${String(day).padStart(2, "0")}` : null;
  });
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

function CalendarPost({ item, onUpdated, onRemoved, startEditing = false }: { item: CalendarEntry; onUpdated: (entry: CalendarEntry) => void; onRemoved: (id: string) => void; startEditing?: boolean }) {
  const [editing, setEditing] = useState(false);
  const [scheduledFor, setScheduledFor] = useState(() => localDateTimeValue(item.scheduled_for));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { if (startEditing) setEditing(true); }, [startEditing]);
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
  const [activityFilter, setActivityFilter] = useState<"all" | ActivityItem["kind"]>("all");
  const [campaignStatusFilter, setCampaignStatusFilter] = useState("all");
  const [campaignChannelFilter, setCampaignChannelFilter] = useState("all");
  const [calendarMonthFilter, setCalendarMonthFilter] = useState("all");
  const [calendarView, setCalendarView] = useState<"list" | "grid">("list");
  const [calendarFocusId, setCalendarFocusId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showQuickNav, setShowQuickNav] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null);
  const [retryKey, setRetryKey] = useState(0);
  const retry = () => setRetryKey((value) => value + 1);

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setShowQuickNav(true);
      }
      if (event.key === "/" && document.activeElement?.tagName !== "INPUT" && document.activeElement?.tagName !== "TEXTAREA") {
        event.preventDefault();
        searchInputRef.current?.focus();
      }
      if (event.key === "Escape") setShowQuickNav(false);
    }
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  useEffect(() => {
    const saved = window.localStorage;
    setSearchQuery(saved.getItem("fundly-search") || "");
    setCampaignStatusFilter(saved.getItem("fundly-campaign-status") || "all");
    setCampaignChannelFilter(saved.getItem("fundly-campaign-channel") || "all");
    setCalendarMonthFilter(saved.getItem("fundly-calendar-month") || "all");
    setCalendarView(saved.getItem("fundly-calendar-view") === "grid" ? "grid" : "list");
    const savedActivity = saved.getItem("fundly-activity-filter");
    if (savedActivity === "campaign" || savedActivity === "draft" || savedActivity === "calendar") setActivityFilter(savedActivity);
  }, []);

  useEffect(() => {
    const saved = window.localStorage;
    saved.setItem("fundly-search", searchQuery);
    saved.setItem("fundly-campaign-status", campaignStatusFilter);
    saved.setItem("fundly-campaign-channel", campaignChannelFilter);
    saved.setItem("fundly-calendar-month", calendarMonthFilter);
    saved.setItem("fundly-calendar-view", calendarView);
    saved.setItem("fundly-activity-filter", activityFilter);
  }, [searchQuery, campaignStatusFilter, campaignChannelFilter, calendarMonthFilter, calendarView, activityFilter]);

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
  const visibleCampaigns = campaigns.status === "success"
    ? campaigns.data.items.filter((campaign) => (campaignStatusFilter === "all" || campaign.status === campaignStatusFilter) && (campaignChannelFilter === "all" || campaign.channel.startsWith(campaignChannelFilter)) && `${campaign.name} ${campaign.channel} ${campaign.status}`.toLowerCase().includes(searchQuery.toLowerCase()))
    : [];
  const scheduledContent = calendar.status === "success"
    ? calendar.data.items.filter((item) => item.status.toLowerCase() === "scheduled" && `${item.title} ${item.body} ${item.channel}`.toLowerCase().includes(searchQuery.toLowerCase()))
    : [];
  const calendarMonths = [...new Set(scheduledContent.map((item) => item.scheduled_for.slice(0, 7)))].sort();
  const visibleCalendar = calendarMonthFilter === "all"
    ? scheduledContent
    : scheduledContent.filter((item) => item.scheduled_for.startsWith(calendarMonthFilter));
  const selectedMonthIndex = calendarMonths.indexOf(calendarMonthFilter);
  const todayMonth = new Date().toISOString().slice(0, 7);
  const canGoPrevious = selectedMonthIndex > 0;
  const canGoNext = selectedMonthIndex >= 0 && selectedMonthIndex < calendarMonths.length - 1;
  const gridMonth = calendarMonthFilter === "all" ? calendarMonths[0] : calendarMonthFilter;
  const gridDays = gridMonth ? monthGrid(gridMonth) : [];
  const draftContent = content.status === "success"
    ? content.data.items.filter((item) => item.status.toLowerCase() === "draft" && `${item.title} ${item.body} ${item.channel}`.toLowerCase().includes(searchQuery.toLowerCase()))
    : [];
  const visibleActivity = activity.status === "success" && activityFilter !== "all"
    ? activity.data.items.filter((item) => item.kind === activityFilter && `${item.title} ${item.detail}`.toLowerCase().includes(searchQuery.toLowerCase()))
    : activity.status === "success" ? activity.data.items.filter((item) => `${item.title} ${item.detail}`.toLowerCase().includes(searchQuery.toLowerCase())) : [];
  const resourceErrors = [overview, campaigns, content, calendar, activity].filter((resource): resource is { status: "error"; message: string } => resource.status === "error");

  function exportWorkspace(format: "json" | "csv") {
    const payload = {
      exported_at: new Date().toISOString(),
      campaigns: campaigns.status === "success" ? campaigns.data.items : [],
      calendar: calendar.status === "success" ? calendar.data.items : [],
      content: content.status === "success" ? content.data.items : [],
      activity: activity.status === "success" ? activity.data.items : [],
    };
    const rows = payload.activity.map((item) => ({ type: item.kind, title: item.title, detail: item.detail, occurred_at: item.occurred_at }));
    const csv = ["type,title,detail,occurred_at", ...rows.map((row) => [row.type, row.title, row.detail, row.occurred_at].map((value) => `"${value.replaceAll('"', '""')}"`).join(","))].join("\n");
    const blob = new Blob([format === "json" ? JSON.stringify(payload, null, 2) : csv], { type: format === "json" ? "application/json" : "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `fundly-workspace-${new Date().toISOString().slice(0, 10)}.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="app-shell">
      <Sidebar campaignCount={campaignCount} brandName={brandName} />
      <main className="main-content" id="overview">
        <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> <strong>{overview.status === "success" ? overview.data.period : "Overview"}</strong></div><div className="topbar-right"><ThemeToggle /><span className="demo-pill"><i /> DEMO DATA</span><button type="button" className="icon-button" aria-label="Notifications" aria-expanded={showNotifications} onClick={() => setShowNotifications((value) => !value)}>♧<i /></button><span className="top-avatar">JD</span></div>{showNotifications && <div className="notifications-panel" role="dialog" aria-label="Notifications"><div className="notifications-heading"><strong>Notifications</strong><button type="button" onClick={() => setShowNotifications(false)} aria-label="Close notifications">×</button></div>{resourceErrors.map((resource, index) => <p className="notification-error" key={`error-${index}`}>API request needs attention: {resource.message}</p>)}{activity.status === "success" && activity.data.items.slice(0, 4).map((item) => <a href="#activity" className="notification-item" key={item.id} onClick={() => setShowNotifications(false)}><span className={`activity-dot ${item.kind}`} /><span><strong>{item.title}</strong><small>{item.detail}</small></span></a>)}{resourceErrors.length === 0 && (activity.status !== "success" || activity.data.items.length === 0) && <p className="notification-empty">No new notifications.</p>}</div>}</header>
        <div className="page-wrap">
          <section className="welcome-row"><div><div className="eyebrow">SATURDAY, OCTOBER 24, 2026 <span className="welcome-spark">✦</span></div><h1>Good morning, Jamie <span>☀️</span></h1><p>Here’s what’s happening with your marketing today.</p></div><CampaignComposer onCreated={addCampaign} /></section>

          <div className="demo-banner"><span className="banner-icon">✦</span><span><strong>Your workspace, ready to explore.</strong> Everything you see here is sample data. AI and social integrations aren’t connected.</span><a href="#studio">Explore the studio <span>→</span></a></div>

          <div className="workspace-search"><label htmlFor="workspace-search-input">Search workspace <kbd>Ctrl K</kbd></label><input ref={searchInputRef} id="workspace-search-input" type="search" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search campaigns, drafts, or calendar entries" /><span aria-hidden="true">⌕</span><div className="workspace-actions"><button type="button" className="quick-nav-trigger" onClick={() => setShowQuickNav(true)}>Quick jump</button><button type="button" onClick={() => exportWorkspace("json")}>Export JSON</button><button type="button" onClick={() => exportWorkspace("csv")}>Export CSV</button></div></div>

          {showQuickNav && <div className="quick-nav" role="dialog" aria-modal="true" aria-label="Quick navigation"><div className="quick-nav-card"><div className="quick-nav-heading"><strong>Jump to</strong><button type="button" onClick={() => setShowQuickNav(false)} aria-label="Close quick navigation">×</button></div>{[{ label: "Campaigns", href: "#campaigns" }, { label: "Calendar", href: "#calendar" }, { label: "Activity", href: "#activity" }, { label: "Content studio", href: "#studio" }].map((item) => <a href={item.href} key={item.href} onClick={() => setShowQuickNav(false)}>{item.label}<span>→</span></a>)}</div></div>}

          <section className="stats-grid" aria-label="Demo performance metrics">
            {overview.status === "loading" && <LoadingMetrics />}
            {overview.status === "error" && <RetryMessage message={overview.message} onRetry={retry} />}
            {overview.status === "success" && overview.data.metrics.length === 0 && <div className="resource-state">No overview metrics are available yet.</div>}
            {overview.status === "success" && overview.data.metrics.map((metric, index) => <MetricCard metric={metric} index={index} key={metric.label} />)}
          </section>

          <div className="content-grid">
            <section className="panel campaign-panel" id="campaigns"><SectionHeading eyebrow="IN MOTION" title="Campaigns" action="All campaigns" href="#campaigns"/><div className="campaign-filters"><label>Status<select value={campaignStatusFilter} onChange={(event) => setCampaignStatusFilter(event.target.value)}><option value="all">All statuses</option><option value="Planning">Planning</option><option value="In progress">In progress</option></select></label><label>Channel<select value={campaignChannelFilter} onChange={(event) => setCampaignChannelFilter(event.target.value)}><option value="all">All channels</option><option value="Instagram">Instagram</option><option value="LinkedIn">LinkedIn</option><option value="X">X</option><option value="Email">Email</option><option value="Facebook">Facebook</option></select></label></div><div className="campaign-list">
              {campaigns.status === "loading" && <div className="resource-state">Loading campaigns…</div>}
              {campaigns.status === "error" && <RetryMessage message={campaigns.message} onRetry={retry} />}
              {campaigns.status === "success" && campaigns.data.items.length === 0 && <div className="resource-state">No campaigns are available yet.</div>}
              {campaigns.status === "success" && campaigns.data.items.length > 0 && visibleCampaigns.length === 0 && <div className="resource-state">No campaigns match these filters.</div>}
              {campaigns.status === "success" && visibleCampaigns.map((campaign, index) => <CampaignRow campaign={campaign} index={index} onEdit={setEditingCampaign} key={campaign.id} />)}
            </div><div className="panel-footnote"><span>ⓘ</span> Campaign details are demonstration data.</div></section>

            <section className="panel calendar-panel" id="calendar"><SectionHeading eyebrow="UP NEXT" title="On the calendar" action="View calendar" href="#calendar"/><div className="calendar-toolbar"><div className="calendar-filter"><button type="button" onClick={() => setCalendarMonthFilter(calendarMonths[selectedMonthIndex - 1])} disabled={!canGoPrevious} aria-label="Previous month">‹</button><label>Month<select value={calendarMonthFilter} onChange={(event) => setCalendarMonthFilter(event.target.value)}><option value="all">All dates</option>{calendarMonths.map((month) => <option value={month} key={month}>{new Intl.DateTimeFormat("en", { month: "long", year: "numeric" }).format(new Date(`${month}-01T12:00:00`))}</option>)}</select></label><button type="button" onClick={() => setCalendarMonthFilter(calendarMonths[selectedMonthIndex + 1])} disabled={!canGoNext} aria-label="Next month">›</button><button type="button" onClick={() => setCalendarMonthFilter(todayMonth)} className="today-button">Today</button></div><div className="calendar-view-toggle" role="group" aria-label="Calendar view"><button type="button" className={calendarView === "list" ? "active" : ""} onClick={() => setCalendarView("list")}>List</button><button type="button" className={calendarView === "grid" ? "active" : ""} onClick={() => setCalendarView("grid")}>Month</button></div></div>{calendarView === "list" ? <div className="upcoming-list">
              {calendar.status === "loading" && <div className="resource-state">Loading local calendar…</div>}
              {content.status === "loading" && <div className="resource-state">Loading scheduled content…</div>}
              {calendar.status === "error" && <RetryMessage message={calendar.message} onRetry={retry} />}
              {calendar.status === "success" && visibleCalendar.length === 0 && <div className="resource-state">{scheduledContent.length === 0 ? "No scheduled posts are available yet." : "No posts are scheduled in this month."}</div>}
              {calendar.status === "success" && visibleCalendar.map((item) => <CalendarPost item={item} onUpdated={replaceCalendar} onRemoved={removeCalendar} startEditing={item.id === calendarFocusId} key={item.id} />)}
            </div> : <div className="calendar-grid"><div className="calendar-weekdays">{["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => <span key={day}>{day}</span>)}</div><div className="calendar-grid-days">{gridDays.map((day, index) => <div className="calendar-grid-day" key={`${day ?? "empty"}-${index}`}>{day && <><strong>{Number(day.slice(-2))}</strong>{scheduledContent.filter((item) => item.scheduled_for.startsWith(day)).map((item) => <button type="button" className="calendar-grid-entry" key={item.id} title={`Edit ${item.title}`} onClick={() => { setCalendarFocusId(item.id); setCalendarMonthFilter(day.slice(0, 7)); setCalendarView("list"); }}>{item.title}</button>)}</>}</div>)}</div></div>}<div className="panel-footnote"><span>◷</span> Local planning calendar; nothing is published.</div></section>
          </div>

          <section className="panel activity-panel" id="activity" aria-labelledby="activity-title">
            <SectionHeading eyebrow="RECENT ACTIVITY" title="Workspace timeline" href="#activity" />
            <div className="activity-filters" role="group" aria-label="Filter activity">
              {(["all", "campaign", "draft", "calendar"] as const).map((filter) => <button key={filter} type="button" className={activityFilter === filter ? "active" : ""} aria-pressed={activityFilter === filter} onClick={() => setActivityFilter(filter)}>{filter === "all" ? "All" : filter === "calendar" ? "Calendar" : `${filter[0].toUpperCase()}${filter.slice(1)}s`}</button>)}
            </div>
            {activity.status === "loading" && <div className="resource-state">Loading activity…</div>}
            {activity.status === "error" && <RetryMessage message={activity.message} onRetry={retry} />}
            {activity.status === "success" && visibleActivity.length === 0 && <div className="resource-state">{activity.data.items.length === 0 ? "No workspace activity yet." : "No activity matches this filter."}</div>}
            {activity.status === "success" && visibleActivity.length > 0 && <div className="activity-list">{visibleActivity.map((item) => <article className="activity-item" key={item.id}><span className={`activity-dot ${item.kind}`} /><div><strong>{item.title}</strong><p>{item.detail}</p></div><time dateTime={item.occurred_at}>{new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(item.occurred_at))}</time></article>)}</div>}
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
