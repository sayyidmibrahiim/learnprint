"""Plain-text course journey card grounded in canonical plan and optional FSM.

No grading, side effects or progress persistence. Compatible with Python 3.9.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

FALLBACK_LABELS = {
    "not_assessed": ("belum dinilai", "not assessed"),
    "in_progress": ("ada latihan/bukti, belum tuntas", "some evidence, not complete"),
    "immediate_demonstrated": ("tes mandiri + transfer tercatat", "application + transfer recorded"),
    "maintained": ("review tertunda terpenuhi", "delayed review satisfied"),
}

STAGES = {
    "PREPARATION": ("PERSIAPAN", "PREPARATION"),
    "SCREENING": ("SCREENING AWAL", "INITIAL SCREENING"),
    "LESSON": ("BELAJAR", "LEARNING"),
    "GUIDED": ("BELAJAR: LATIHAN TERBIMBING", "LEARNING: GUIDED PRACTICE"),
    "INDEPENDENT": ("TES MANDIRI", "INDEPENDENT TEST"),
    "TRANSFER": ("TES TRANSFER", "TRANSFER TEST"),
    "REVIEW": ("REVIEW TERTUNDA", "DELAYED REVIEW"),
    "PAUSE": ("JEDA/KLARIFIKASI", "PAUSE/CLARIFICATION"),
    "FEEDBACK": ("UMPAN BALIK", "FEEDBACK"),
    "TEACH_BACK": ("JELASKAN KEMBALI", "TEACH BACK"),
    "COMPLETE": ("SESI SELESAI", "SESSION COMPLETE"),
}
FSM_STAGES = {
    "ORIENT": "PREPARATION",
    "EXPLAIN": "LESSON",
    "GUIDED": "GUIDED",
    "ATTEMPT": "INDEPENDENT",
    "FEEDBACK": "FEEDBACK",
    "TEACH_BACK": "TEACH_BACK",
    "TRANSFER": "TRANSFER",
    "DELAYED_RETRIEVAL": "REVIEW",
    "COMPLETE": "COMPLETE",
}


def render_stage_card(
    plan: Dict[str, Any],
    stage: Optional[str] = None,
    stored_phase: Optional[str] = None,
    screening_used: Optional[int] = None,
    unit_id: Optional[str] = None,
    language: str = "id",
) -> str:
    """Render an honest navigation card; never infer a mastery percentage.

    stage and screening_used are host-reported, not evaluator-confirmed.
    stored_phase is validated by the caller against a matching FSM session.
    """
    if language not in ("id", "en"):
        raise ValueError("supported card languages: id, en")
    if stage is not None and stored_phase is not None:
        raise ValueError("stage and persisted session phase are mutually exclusive")
    if stage is not None and stage not in STAGES:
        raise ValueError("unknown host-reported stage")
    if stored_phase is not None and stored_phase not in FSM_STAGES:
        raise ValueError("unknown persisted FSM phase")
    if screening_used is not None and (
        not isinstance(screening_used, int) or isinstance(screening_used, bool)
        or not 0 <= screening_used <= 3
    ):
        raise ValueError("screening prompts used must be 0..3")
    units = plan.get("units")
    if not isinstance(units, list):
        raise ValueError("canonical plan has invalid units")
    ids = [u["unit_id"] for u in units]
    if unit_id is not None and unit_id not in ids:
        raise ValueError("requested unit absent from canonical plan")
    idx = 0 if language == "id" else 1
    mode = FSM_STAGES[stored_phase] if stored_phase else stage
    label = (STAGES[mode][idx] if mode else
             ("belum tercatat secara pasti" if idx == 0 else "not confirmed"))
    provenance = (
        "FSM tersimpan dan diverifikasi" if stored_phase and idx == 0 else
        "validated persisted FSM" if stored_phase else
        "dilaporkan agent; belum diverifikasi di ledger" if stage and idx == 0 else
        "host-reported, not verified by ledger" if stage else
        "tidak tersedia" if idx == 0 else "unavailable"
    )
    lines = [
        f"{'Kursus' if idx == 0 else 'Course'}: {plan.get('title') or '(untitled)'}",
        f"{'Tahap' if idx == 0 else 'Stage'}: {label} ({provenance})",
    ]
    if screening_used is not None:
        lines.append(
            ("Screening: {}/3 pertanyaan dipakai (maksimum, bukan target)").format(screening_used)
            if idx == 0 else
            "Screening: {}/3 prompts used (maximum, not quota)".format(screening_used)
        )
    else:
        lines.append("Screening: belum ada hitungan terverifikasi" if idx == 0
                     else "Screening: no verified prompt count")
    lines.append("Roadmap (posisi, BUKAN % mahir):" if idx == 0
                 else "Roadmap (unit position, NOT mastery %):")
    if not units:
        lines.append("  (silabus terstruktur belum tersedia)" if idx == 0
                     else "  (no structured syllabus)")
    for n, unit in enumerate(units, 1):
        status = unit.get("evidence_status", "not_assessed")
        status_text = FALLBACK_LABELS.get(
            status, ("status belum diverifikasi", "status not verified"))[idx]
        title = unit.get("title", "(untitled)")
        lines.append(f"  [{n}/{len(units)}] {title} : {status_text}")
    if unit_id is not None:
        pos = ids.index(unit_id) + 1
        bar = "".join("#" if i == pos - 1 else "-" for i in range(len(units)))
        lines.append(
            f"Posisi unit: [{bar}] {pos}/{len(units)} (dilaporkan agent, bukan nilai)"
            if idx == 0 else
            f"Unit position: [{bar}] {pos}/{len(units)} (host-reported, not a grade)"
        )
    else:
        lines.append("Unit aktif: belum dikonfirmasi" if idx == 0
                     else "Active unit: not confirmed")
    lines.append(
        "Kemampuan: lihat evaluator evidence; posisi unit bukan persentase kemampuan"
        if idx == 0 else
        "Proficiency: use evidence evaluator; unit position is not mastery"
    )
    return "\n".join(lines)
