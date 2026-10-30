export interface FlexValidationResult {
  valid: boolean;
  errors: string[];
}

function isHttpsUri(value: unknown): value is string {
  return typeof value === "string" && value.startsWith("https://") && value.length <= 2000;
}

function visit(value: unknown, path: string, errors: string[]): void {
  if (!value || typeof value !== "object") return;
  if (Array.isArray(value)) {
    value.forEach((item, index) => visit(item, `${path}[${index}]`, errors));
    return;
  }
  const record = value as Record<string, unknown>;
  if (record.type === "text" && (typeof record.text !== "string" || record.text.trim() === "")) {
    errors.push(`${path}.text must be non-empty`);
  }
  if (record.type === "uri" && !isHttpsUri(record.uri)) {
    errors.push(`${path}.uri must be an https URI no longer than 2000 characters`);
  }
  if (record.action && typeof record.action === "object") visit(record.action, `${path}.action`, errors);
  for (const [key, child] of Object.entries(record)) visit(child, `${path}.${key}`, errors);
}

export function validateFlexMessages(messages: unknown[]): FlexValidationResult {
  const errors: string[] = [];
  messages.forEach((message, index) => {
    if (!message || typeof message !== "object") {
      errors.push(`messages[${index}] must be an object`);
      return;
    }
    const record = message as Record<string, unknown>;
    if (record.type === "flex" && (typeof record.altText !== "string" || record.altText.trim() === "")) {
      errors.push(`messages[${index}].altText must be non-empty`);
    }
    visit(message, `messages[${index}]`, errors);
  });
  return { valid: errors.length === 0, errors };
}
