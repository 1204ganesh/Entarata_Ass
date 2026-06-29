const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export async function explainCode(payload) {
  const response = await fetch(`${API_BASE_URL}/api/explain`, {
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
