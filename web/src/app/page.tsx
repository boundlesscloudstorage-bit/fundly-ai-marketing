import { campaigns, drafts, stats, upcoming } from "@/data/mock";

function Mark({ small = false }: { small?: boolean }) {
  return <span className={`brand-mark${small ? " brand-mark-small" : ""}`} aria-hidden="true"><span>f</span></span>;
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <a className="brand" href="#overview" aria-label="Fundly home"><Mark /><span className="brand-word">fundly<span className="brand-ai">.ai</span></span></a>
      <div className="workspace-label">WORKSPACE</div>
      <nav className="nav-list" aria-label="Main navigation">
        <a className="nav-item active" href="#overview"><span className="nav-icon">⌂</span>Overview</a>
        <a className="nav-item" href="#campaigns"><span className="nav-icon">◫</span>Campaigns<span className="nav-count">4</span></a>
        <a className="nav-item" href="#calendar"><span className="nav-icon">▦</span>Content calendar</a>
        <a className="nav-item" href="#studio"><span className="nav-icon">✳</span>Content studio<span className="nav-dot" /></a>
      </nav>
      <div className="sidebar-bottom">
        <div className="workspace-label">YOUR BRAND</div>
        <div className="brand-switcher" aria-label="Current brand: Fundly"><Mark small /><span><strong>Fundly</strong><small>Brand workspace</small></span><span className="chevron">⌄</span></div>
        <div className="demo-note"><span className="demo-spark">✦</span><div><strong>Your creative copilot</strong><p>Draft ideas and stay on brand.</p></div></div>
        <div className="profile"><span className="avatar">JD</span><span><strong>Jamie Davis</strong><small>Marketing team</small></span><span className="more">···</span></div>
      </div>
    </aside>
  );
}

function SectionHeading({ eyebrow, title, action, href }: { eyebrow?: string; title: string; action?: string; href: string }) {
  return <div className="section-heading"><div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h2>{title}</h2></div>{action && <a className="text-link" href={href}>{action}<span> ↗</span></a>}</div>;
}

export default function Home() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content" id="overview">
        <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> <strong>Overview</strong></div><div className="topbar-right"><span className="demo-pill"><i /> DEMO DATA</span><span className="icon-button" aria-label="Notifications">♧<i /></span><span className="top-avatar">JD</span></div></header>
        <div className="page-wrap">
          <section className="welcome-row"><div><div className="eyebrow">SATURDAY, OCTOBER 24, 2026 <span className="welcome-spark">✦</span></div><h1>Good morning, Jamie <span>☀️</span></h1><p>Here’s what’s happening with your marketing today.</p></div><button className="primary-button" type="button" disabled title="Campaign creation is coming soon"><span>＋</span> New campaign <span className="soon-label">SOON</span></button></section>

          <div className="demo-banner"><span className="banner-icon">✦</span><span><strong>Your workspace, ready to explore.</strong> Everything you see here is sample data. AI and social integrations aren’t connected.</span><a href="#studio">Explore the studio <span>→</span></a></div>

          <section className="stats-grid" aria-label="Demo performance metrics">{stats.map((stat) => <article className="stat-card" key={stat.label}><div className="stat-top"><span>{stat.label}</span><span className={`stat-icon ${stat.tone}`}>{stat.icon}</span></div><div className="stat-value">{stat.value}</div><div className="stat-change"><span>↗</span> {stat.change}</div><span className="metric-caption">DEMO METRIC</span></article>)}</section>

          <div className="content-grid">
            <section className="panel campaign-panel" id="campaigns"><SectionHeading eyebrow="IN MOTION" title="Campaigns" action="All campaigns" href="#campaigns"/><div className="campaign-list">{campaigns.map((campaign) => <article className="campaign-row" key={campaign.name}><div className={`campaign-art ${campaign.color}`}><span>{campaign.color === "purple" ? "✳" : campaign.color === "orange" ? "↗" : "◌"}</span></div><div className="campaign-info"><div className="campaign-name">{campaign.name}</div><div className="campaign-meta">{campaign.channel}</div><div className="progress-track"><span className={campaign.color} style={{ width: `${campaign.progress}%` }} /></div></div><div className="campaign-side"><span className={`status ${campaign.status === "Planning" ? "planning" : ""}`}><i />{campaign.status}</span><span className="campaign-date">{campaign.date}</span></div></article>)}</div><div className="panel-footnote"><span>ⓘ</span> Campaigns shown are illustrative examples.</div></section>

            <section className="panel calendar-panel" id="calendar"><SectionHeading eyebrow="UP NEXT" title="On the calendar" action="View calendar" href="#calendar"/><div className="upcoming-list">{upcoming.map((post) => <article className="upcoming-row" key={post.day}><div className="date-tile"><span>{post.weekday}</span><strong>{post.day}</strong><small>{post.month}</small></div><div className="upcoming-info"><strong>{post.title}</strong><span><i className={`channel-dot ${post.color}`} />{post.channel}<span className="meta-sep">·</span>{post.time}</span></div><span className="row-arrow">›</span></article>)}</div><div className="panel-footnote"><span>◷</span> Scheduled times are sample placeholders.</div></section>
          </div>

          <section className="studio-section" id="studio"><div className="studio-intro"><div><div className="eyebrow"><span className="eyebrow-star">✦</span> YOUR CREATIVE CORNER</div><h2>Content studio</h2><p>A few on-brand ideas to get the creative wheels turning.</p></div><button className="outline-button" type="button" disabled title="AI generation is not connected">✦ &nbsp; Generate ideas <span className="soon-label">SOON</span></button></div><div className="draft-grid">{drafts.map((draft) => <article className="draft-card" key={draft.title}><div className="draft-head"><span className={`draft-icon ${draft.color}`}>{draft.color === "pink" ? "◎" : "in"}</span><span className="draft-type">{draft.type}</span><span className="draft-menu">···</span></div><h3>{draft.title}</h3><p>{draft.text}</p><div className="draft-footer"><span className="tone-tag"><i />{draft.tag}</span><button type="button" disabled title="Editing is coming soon">Open draft <span>↗</span></button></div></article>)}</div><div className="studio-disclaimer"><span>✦</span> Sample drafts for inspiration. No AI service is connected.</div></section>
          <footer className="page-footer"><span><Mark small /> Made for meaningful momentum.</span><span>Fundly AI Marketing Agent <i>·</i> Local demo</span></footer>
        </div>
      </main>
    </div>
  );
}
