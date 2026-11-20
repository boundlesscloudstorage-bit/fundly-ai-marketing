"use client";

import { useState, type FormEvent } from "react";
import {
  createCampaign,
  type Campaign,
  type CampaignChannel,
  type CampaignCreateRequest,
  type CampaignObjective,
} from "@/lib/api";

const channels: CampaignChannel[] = ["Instagram", "LinkedIn", "X", "Facebook", "Email"];
const objectives: { value: CampaignObjective; label: string }[] = [
  { value: "awareness", label: "Awareness" },
  { value: "education", label: "Education" },
  { value: "consideration", label: "Consideration" },
  { value: "engagement", label: "Engagement" },
];

function dateOffset(days: number): string {
  const value = new Date();
  value.setDate(value.getDate() + days);
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function CampaignComposer({ onCreated }: { onCreated: (campaign: Campaign) => void }) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [created, setCreated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [channel, setChannel] = useState<CampaignChannel>("Instagram");
  const [objective, setObjective] = useState<CampaignObjective>("awareness");
  const [targetDate, setTargetDate] = useState(() => dateOffset(7));

  function close() {
    if (saving) return;
    setOpen(false);
    setCreated(false);
    setError(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    const request: CampaignCreateRequest = { name, channel, objective, target_date: targetDate };
    try {
      const campaign = await createCampaign(request);
      onCreated(campaign);
      setCreated(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The campaign could not be created. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="campaign-composer">
      <button className="primary-button campaign-create-trigger" type="button" onClick={() => setOpen(true)}>
        <span aria-hidden="true">＋</span> New campaign
      </button>
      {open && (
        <div className="campaign-dialog-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}>
          <section
            className="campaign-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="campaign-dialog-title"
            onKeyDown={(event) => { if (event.key === "Escape") close(); }}
          >
            <div className="campaign-dialog-heading">
              <div>
                <div className="eyebrow">FUNDLY WORKSPACE</div>
                <h2 id="campaign-dialog-title">Create a campaign</h2>
              </div>
              <button className="campaign-dialog-close" type="button" onClick={close} disabled={saving} aria-label="Close campaign form">×</button>
            </div>
            {created ? (
              <div className="campaign-created" role="status">
                <span aria-hidden="true">✓</span>
                <div><strong>Campaign added to this demo workspace.</strong><p>Nothing was scheduled or published.</p></div>
                <button className="workflow-button" type="button" onClick={close}>Done</button>
              </div>
            ) : (
              <>
                <p className="campaign-dialog-intro">Set up a planning entry for your next idea. It stays in memory and resets when the API restarts.</p>
                <form className="campaign-form" onSubmit={submit}>
                  <label className="campaign-field">
                    Campaign name
                    <input value={name} onChange={(event) => setName(event.target.value)} minLength={3} maxLength={80} required autoFocus placeholder="e.g. Small steps, stronger savings" />
                  </label>
                  <div className="campaign-form-row">
                    <label className="campaign-field">
                      Channel
                      <select value={channel} onChange={(event) => setChannel(event.target.value as CampaignChannel)}>
                        {channels.map((item) => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </label>
                    <label className="campaign-field">
                      Objective
                      <select value={objective} onChange={(event) => setObjective(event.target.value as CampaignObjective)}>
                        {objectives.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                      </select>
                    </label>
                  </div>
                  <label className="campaign-field">
                    Target date
                    <input type="date" value={targetDate} min={dateOffset(0)} onChange={(event) => setTargetDate(event.target.value)} required />
                  </label>
                  {error && <div className="campaign-form-error" role="alert">{error}</div>}
                  <div className="campaign-form-actions">
                    <button className="secondary-action" type="button" onClick={close} disabled={saving}>Cancel</button>
                    <button className="workflow-button" type="submit" disabled={saving || name.trim().length < 3 || !targetDate}>
                      {saving ? "Creating…" : "Create demo campaign"}
                    </button>
                  </div>
                </form>
                <p className="campaign-dialog-note">Demo data only · No ads, posts, or messages are sent.</p>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
