const API_BASE_URL = "https://entarata-ass-6lvt.vercel.app";

export async function explainCode(payload) {
  const response = await fetch(`https://entarata-ass-6lvt.vercel.app/api/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Unable to explain the snippet.");
  }

  return response.json();
}
