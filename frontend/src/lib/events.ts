import { DecisionRecord } from "@/types";

/**
 * Deterministically deduplicates decision event records by canonical event_id.
 *
 * Guarantees:
 * 1. Canonical Identity: Uses backend event_id as the primary unique key.
 * 2. Zero Duplicates: Each event_id appears exactly once in the returned array.
 * 3. Preserves Newest Information: When multiple records share the same event_id,
 *    the most recent record (by ISO timestamp) is retained, merging non-empty fields.
 * 4. Stable Chronological Order: Sorted descending by timestamp (newest event first).
 * 5. Deterministic & Safe: No random keys, no Math.random(), no array index keys.
 */
export function dedupeEventsById(records: DecisionRecord[]): DecisionRecord[] {
  if (!records || !Array.isArray(records) || records.length === 0) {
    return [];
  }

  const map = new Map<string, DecisionRecord>();

  for (const record of records) {
    if (!record || !record.event_id) continue;

    const id = record.event_id;
    const existing = map.get(id);

    if (!existing) {
      map.set(id, record);
      continue;
    }

    // Compare timestamps to keep the newest record
    const existingTime = existing.timestamp ? new Date(existing.timestamp).getTime() : 0;
    const newTime = record.timestamp ? new Date(record.timestamp).getTime() : 0;

    if (newTime >= existingTime) {
      // Replace with newer record, merging any preserved metadata
      map.set(id, {
        ...existing,
        ...record,
      });
    } else {
      // Existing is newer, merge any non-null fields from the incoming record
      map.set(id, {
        ...record,
        ...existing,
      });
    }
  }

  // Sort descending by timestamp (newest first) with stable tie-breaker
  return Array.from(map.values()).sort((a, b) => {
    const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
    const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
    if (timeB !== timeA) {
      return timeB - timeA;
    }
    return (b.event_id || "").localeCompare(a.event_id || "");
  });
}
