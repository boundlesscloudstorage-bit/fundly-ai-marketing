"use client";

import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import {
  API_BASE_URL,
  fetchApiData,
  isCampaignListResponse,
  isContentListResponse,
  isOverviewResponse,
  type ApiResource,
  type Campaign,
  type CampaignListResponse,
  type ContentItem,
  type ContentListResponse,
  type Metric,
  type OverviewResponse,
} from "@/lib/api";

function Mark({ small = false }: { small?: boolean }) {
  return <span className={`brand-mark${small ? " brand-mark-small" : ""}`} aria-hidden="true"><span>f</span></span>;
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

function CampaignRow({ campaign, index }: { campaign: Campaign; index: number }) {
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
      <div className="campaign-side"><span className={`status ${campaign.status.toLowerCase() === "planning" ? "planning" : ""}`}><i />{campaign.status}</span><span className="campaign-date">{dateLabel}</span></div>
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

function CalendarPost({ item }: { item: ContentItem }) {
  const date = formatScheduledDate(item.scheduled_for);
  return (
    <article className="upcoming-row">
      <div className="date-tile"><span>{date.weekday}</span><strong>{date.day}</strong><small>{date.month}</small></div>
      <div className="upcoming-info"><strong>{item.title}</strong><span><i className={`channel-dot ${contentColor(item.channel)}`} />{item.channel}<span className="meta-sep">·</span>{date.time}</span></div>
      <span className="row-arrow" aria-hidden="true">›</span>
    </article>
  );
}

function ContentDraft({ item }: { item: ContentItem }) {
  const color = contentColor(item.channel);
  return (
    <article className="draft-card">
      <div className="draft-head"><span className={`draft-icon ${color}`}>{color === "pink" ? "◎" : color === "blue" ? "in" : "✉"}</span><span className="draft-type">{item.is_ai_generated_example ? "SAMPLE AI DRAFT" : "DRAFT"} · {item.channel.toUpperCase()}</span><span className="draft-menu">···</span></div>
      <h3>{item.title}</h3><p>{item.body}</p>
      <div className="draft-footer"><span className="tone-tag"><i />{item.is_ai_generated_example ? "AI example" : "Demo content"}</span><button type="button" disabled title="Editing is coming soon">Open draft <span>↗</span></button></div>
    </article>
  );
}

export default function Home() {
  const [overview, setOverview] = useState<ApiResource<OverviewResponse>>({ status: "loading" });
  const [campaigns, setCampaigns] = useState<ApiResource<CampaignListResponse>>({ status: "loading" });
  const [content, setContent] = useState<ApiResource<ContentListResponse>>({ status: "loading" });
  const [retryKey, setRetryKey] = useState(0);
  const retry = () => setRetryKey((value) => value + 1);

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

    return () => controller.abort();
  }, [retryKey]);

  const brandName = overview.status === "success" ? overview.data.brand_name : "Fundly";
  const campaignCount = campaigns.status === "success" ? campaigns.data.total : null;
  const scheduledContent = content.status === "success"
    ? content.data.items.filter((item) => item.status.toLowerCase() === "scheduled")
    : [];
  const draftContent = content.status === "success"
    ? content.data.items.filter((item) => item.status.toLowerCase() === "draft")
    : [];

  return (
    <div className="app-shell">
      <Sidebar campaignCount={campaignCount} brandName={brandName} />
      <main className="main-content" id="overview">
        <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> <strong>{overview.status === "success" ? overview.data.period : "Overview"}</strong></div><div className="topbar-right"><span className="demo-pill"><i /> DEMO DATA</span><span className="icon-button" aria-label="Notifications">♧<i /></span><span className="top-avatar">JD</span></div></header>
        <div className="page-wrap">
          <section className="welcome-row"><div><div className="eyebrow">SATURDAY, OCTOBER 24, 2026 <span className="welcome-spark">✦</span></div><h1>Good morning, Jamie <span>☀️</span></h1><p>Here’s what’s happening with your marketing today.</p></div><button className="primary-button" type="button" disabled title="Campaign creation is coming soon"><span>＋</span> New campaign <span className="soon-label">SOON</span></button></section>

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
              {campaigns.status === "success" && campaigns.data.items.map((campaign, index) => <CampaignRow campaign={campaign} index={index} key={campaign.id} />)}
            </div><div className="panel-footnote"><span>ⓘ</span> Campaign details are demonstration data.</div></section>

            <section className="panel calendar-panel" id="calendar"><SectionHeading eyebrow="UP NEXT" title="On the calendar" action="View calendar" href="#calendar"/><div className="upcoming-list">
              {content.status === "loading" && <div className="resource-state">Loading scheduled content…</div>}
              {content.status === "error" && <RetryMessage message={content.message} onRetry={retry} />}
              {content.status === "success" && scheduledContent.length === 0 && <div className="resource-state">No scheduled posts are available yet.</div>}
              {content.status === "success" && scheduledContent.map((item) => <CalendarPost item={item} key={item.id} />)}
            </div><div className="panel-footnote"><span>◷</span> Schedule examples from the demo API.</div></section>
          </div>

          <section className="studio-section" id="studio"><div className="studio-intro"><div><div className="eyebrow"><span className="eyebrow-star">✦</span> YOUR CREATIVE CORNER</div><h2>Content studio</h2><p>Sample drafts from your connected demo API.</p></div><button className="outline-button" type="button" disabled title="AI generation is not connected">✦ &nbsp; Generate ideas <span className="soon-label">SOON</span></button></div><div className="draft-grid">
            {content.status === "loading" && <div className="resource-state">Loading content drafts…</div>}
            {content.status === "error" && <RetryMessage message={content.message} onRetry={retry} />}
            {content.status === "success" && draftContent.length === 0 && <div className="resource-state">No drafts are available yet.</div>}
            {content.status === "success" && draftContent.map((item) => <ContentDraft item={item} key={item.id} />)}
          </div><div className="studio-disclaimer"><span>✦</span> Sample drafts for inspiration. No AI service is connected.</div></section>
          <footer className="page-footer"><span><Mark small /> Made for meaningful momentum.</span><span>Fundly AI Marketing Agent <i>·</i> Local demo</span></footer>
        </div>
      </main>
    </div>
  );
}
