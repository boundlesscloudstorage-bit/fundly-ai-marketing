"use client";

import { useEffect, useState, type FormEvent } from "react";
import { updateCampaign, type Campaign, type CampaignChannel, type CampaignObjective } from "@/lib/api";

const channels: CampaignChannel[] = ["Instagram", "LinkedIn", "X", "Facebook", "Email"];
const objectives: { value: CampaignObjective; label: string }[] = [
  { value: "awareness", label: "Awareness" },
  { value: "education", label: "Education" },
  { value: "consideration", label: "Consideration" },
  { value: "engagement", label: "Engagement" },
];

function objectiveFromCampaign(channel: string): CampaignObjective {
  const label = channel.split(" · ")[1]?.toLowerCase();
  return objectives.find((item) => item.label.toLowerCase() === label)?.value ?? "awareness";
}

function dateOffset(days: number): string {
  const value = new Date();
  value.setDate(value.getDate() + days);
  return value.toISOString().slice(0, 10);
}

export default function CampaignEditor({ campaign, onClose, onUpdated }: {
  campaign: Campaign;
  onClose: () => void;
  onUpdated: (campaign: Campaign) => void;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState(campaign.name);
  const [channel, setChannel] = useState<CampaignChannel>((campaign.channel.split(" · ")[0] as CampaignChannel) || "Instagram");
  const [objective, setObjective] = useState<CampaignObjective>(() => objectiveFromCampaign(campaign.channel));
  const [targetDate, setTargetDate] = useState(campaign.target_date);

  useEffect(() => {
    setName(campaign.name);
    setChannel((campaign.channel.split(" · ")[0] as CampaignChannel) || "Instagram");
    setObjective(objectiveFromCampaign(campaign.channel));
    setTargetDate(campaign.target_date);
    setError(null);
  }, [campaign]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateCampaign(campaign.id, { name, channel, objective, target_date: targetDate });
      onUpdated(updated);
      onClose();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The campaign could not be updated. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="campaign-dialog-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !saving) onClose(); }}>
      <section className="campaign-dialog" role="dialog" aria-modal="true" aria-labelledby="campaign-edit-title" onKeyDown={(event) => { if (event.key === "Escape" && !saving) onClose(); }}>
        <div className="campaign-dialog-heading">
          <div><div className="eyebrow">FUNDLY WORKSPACE</div><h2 id="campaign-edit-title">Edit campaign</h2></div>
          <button className="campaign-dialog-close" type="button" onClick={onClose} disabled={saving} aria-label="Close campaign editor">×</button>
        </div>
        <p className="campaign-dialog-intro">Update this planning entry. Nothing is scheduled or published.</p>
        <form className="campaign-form" onSubmit={submit}>
          <label className="campaign-field">Campaign name<input value={name} onChange={(event) => setName(event.target.value)} minLength={3} maxLength={80} required autoFocus /></label>
          <div className="campaign-form-row">
            <label className="campaign-field">Channel<select value={channel} onChange={(event) => setChannel(event.target.value as CampaignChannel)}>{channels.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
            <label className="campaign-field">Objective<select value={objective} onChange={(event) => setObjective(event.target.value as CampaignObjective)}>{objectives.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
          </div>
          <label className="campaign-field">Target date<input type="date" value={targetDate} min={dateOffset(0)} onChange={(event) => setTargetDate(event.target.value)} required /></label>
          {error && <div className="campaign-form-error" role="alert">{error}</div>}
          <div className="campaign-form-actions"><button className="secondary-action" type="button" onClick={onClose} disabled={saving}>Cancel</button><button className="workflow-button" type="submit" disabled={saving || name.trim().length < 3 || !targetDate}>{saving ? "Saving…" : "Save changes"}</button></div>
        </form>
      </section>
    </div>
  );
}
