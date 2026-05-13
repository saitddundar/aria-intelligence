"""
Collaborative filtering boosting for RAG candidates.

Kullanıcının beğeni geçmişi ve co-occurrence sinyallerini kullanarak
RAG pipeline'ından gelen adayları yeniden sıralar ve zenginleştirir.
"""

import logging

from config.settings import settings

logger = logging.getLogger(__name__)


def boost_with_collab(
    candidates: list[dict],
    collab_track_ids: list[str],
    liked_track_ids: list[str],
    store,
    boost_factor: float | None = None,
    max_collab_inject: int | None = None,
) -> list[dict]:
    """
    RAG adaylarını collaborative filtering sinyalleriyle boost eder.

    1. Kullanıcının zaten beğendiği şarkıları çıkarır (yeni keşif için).
    2. Co-occurrence ile eşleşen adaylara score boost uygular.
    3. Aday listesinde olmayan collab şarkılarını Qdrant'tan çekip inject eder.
    4. Score'a göre yeniden sıralar.

    Args:
        candidates: RAG pipeline'ından gelen aday şarkılar.
        collab_track_ids: Co-occurrence sorgusundan dönen Spotify ID'ler.
        liked_track_ids: Kullanıcının beğendiği şarkıların Spotify ID'leri.
        store: VectorStore instance (Qdrant'tan şarkı çekmek için).
        boost_factor: Collab eşleşme score boost miktarı (default: settings).
        max_collab_inject: Enjekte edilecek max collab şarkı sayısı (default: settings).

    Returns:
        Boost edilmiş ve yeniden sıralanmış aday listesi.
    """
    if not collab_track_ids and not liked_track_ids:
        return candidates

    if boost_factor is None:
        boost_factor = settings.collaborative.boost_factor
    if max_collab_inject is None:
        max_collab_inject = settings.collaborative.max_collab_inject

    liked_set = set(liked_track_ids or [])
    collab_set = set(collab_track_ids or [])
    candidate_ids = {c.get("spotify_id") for c in candidates}

    # 1. Kullanıcının zaten beğendiği şarkıları çıkar
    if liked_set:
        original_count = len(candidates)
        candidates = [c for c in candidates if c.get("spotify_id") not in liked_set]
        removed = original_count - len(candidates)
        if removed > 0:
            logger.info(f"Removed {removed} already-liked tracks from candidates")

    # 2. Collab eşleşen adaylara score boost
    boosted = 0
    for c in candidates:
        if c.get("spotify_id") in collab_set:
            c["score"] = min(1.0, c.get("score", 0.5) + boost_factor)
            boosted += 1

    if boosted > 0:
        logger.info(f"Boosted {boosted} candidates matching collab signals (+{boost_factor})")

    # 3. Aday listesinde olmayan collab şarkılarını inject et
    missing_collab = [
        tid for tid in collab_track_ids
        if tid not in candidate_ids and tid not in liked_set
    ]
    if missing_collab and max_collab_inject > 0:
        injected = store.get_by_ids(missing_collab[:max_collab_inject])
        for track in injected:
            track["score"] = 0.5  # nötr score
            candidates.append(track)
        if injected:
            logger.info(f"Injected {len(injected)} collaborative tracks into candidates")

    # 4. Score'a göre yeniden sırala
    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)

    return candidates
