function ensureDateTime(date, time) {
  const rawDate = String(date || "").trim();
  const rawTime = String(time || "").trim();

  if (!rawDate || !rawTime) {
    throw new Error("Date and start time are required.");
  }

  const dateTime = new Date(`${rawDate}T${rawTime}:00`);
  if (Number.isNaN(dateTime.getTime())) {
    throw new Error("Invalid date or time.");
  }

  return dateTime;
}

function sanitizeDuration(value) {
  const duration = Number.parseInt(String(value || ""), 10);
  if (!Number.isInteger(duration) || duration <= 0) {
    throw new Error("Duration must be a positive whole number.");
  }
  return duration;
}

function formatUtc(date) {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  const seconds = String(date.getUTCSeconds()).padStart(2, "0");
  return `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
}

function escapeIcsText(value) {
  return String(value || "")
    .replace(/\\/g, "\\\\")
    .replace(/\n/g, "\\n")
    .replace(/,/g, "\\,")
    .replace(/;/g, "\\;");
}

function toGoogleDateTime(date) {
  return formatUtc(date);
}

function safeSlug(value) {
  return String(value || "activity")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 50) || "activity";
}

export function buildCalendarEventPayload(activity, scheduleInput) {
  const start = ensureDateTime(scheduleInput?.date, scheduleInput?.startTime);
  const durationMinutes = sanitizeDuration(scheduleInput?.durationMinutes);
  const end = new Date(start.getTime() + durationMinutes * 60 * 1000);

  const title = String(activity?.title || "Random Activity").trim();
  const description = String(activity?.description || "").trim();
  const category = String(activity?.category || "").trim();
  const details = [
    description,
    category ? `Category: ${category}` : "",
  ]
    .filter(Boolean)
    .join("\n\n");

  return {
    title,
    description: details,
    start,
    end,
    filename: `${safeSlug(title)}.ics`,
  };
}

export function downloadIcs(eventPayload) {
  const uid = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}@random-activity-flow`;
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Random Activity Flow//EN",
    "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    `UID:${uid}`,
    `DTSTAMP:${formatUtc(new Date())}`,
    `DTSTART:${formatUtc(eventPayload.start)}`,
    `DTEND:${formatUtc(eventPayload.end)}`,
    `SUMMARY:${escapeIcsText(eventPayload.title)}`,
    `DESCRIPTION:${escapeIcsText(eventPayload.description)}`,
    "END:VEVENT",
    "END:VCALENDAR",
  ];

  const blob = new Blob([`${lines.join("\r\n")}\r\n`], {
    type: "text/calendar;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = eventPayload.filename || "activity.ics";
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function buildGoogleCalendarUrl(eventPayload) {
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: eventPayload.title,
    details: eventPayload.description,
    dates: `${toGoogleDateTime(eventPayload.start)}/${toGoogleDateTime(eventPayload.end)}`,
  });

  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}
