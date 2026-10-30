export function googleCalendarUrl({ title, start, end, details, location }: {
  title: string;
  start: string;
  end: string;
  details?: string;
  location?: string;
}): string {
  const params = new URLSearchParams({ action: "TEMPLATE", text: title, dates: `${start}/${end}` });
  if (details) params.set("details", details);
  if (location) params.set("location", location);
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export function demoIcs(): string {
  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//LINE Portable Core//EN",
    "BEGIN:VEVENT",
    "UID:line-portable-core-demo@example.invalid",
    "DTSTAMP:20260923T000000Z",
    "DTSTART:20260924T010000Z",
    "DTEND:20260924T020000Z",
    "SUMMARY:LINE Portable Core Demo",
    "DESCRIPTION:Demo calendar event",
    "END:VEVENT",
    "END:VCALENDAR",
    "",
  ].join("\r\n");
}
