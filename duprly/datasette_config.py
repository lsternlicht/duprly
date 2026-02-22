from __future__ import annotations


def build_datasette_metadata(db_name: str) -> dict:
    """Build Datasette metadata with curated canned analytics queries."""
    queries = {
        "player_rating_over_time": {
            "title": "Player Rating Over Time",
            "description": (
                "Trend view for a player over time. Defaults to DOUBLES and full available date range."
            ),
            "hide_sql": True,
            "params": ["dupr_id", "rating_type", "start_date", "end_date", "limit"],
            "sql": """
                SELECT
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    rating_type,
                    rating_date,
                    match_date,
                    rating,
                    changed_by_admin,
                    row_index
                FROM v_player_rating_points
                WHERE player_dupr_id = CAST(:dupr_id AS INTEGER)
                  AND rating_type = UPPER(COALESCE(NULLIF(:rating_type, ''), 'DOUBLES'))
                  AND rating_date BETWEEN COALESCE(NULLIF(:start_date, ''), '1970-01-01')
                                      AND COALESCE(NULLIF(:end_date, ''), date('now'))
                ORDER BY rating_date ASC, row_index ASC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 1000)
            """,
        },
        "player_rating_summary": {
            "title": "Player Rating Summary",
            "description": "First/latest/delta/count summary for a player in the selected scope.",
            "hide_sql": True,
            "params": ["dupr_id", "rating_type", "start_date", "end_date"],
            "sql": """
                WITH scoped AS (
                    SELECT *
                    FROM v_player_rating_points
                    WHERE player_dupr_id = CAST(:dupr_id AS INTEGER)
                      AND rating_type = UPPER(COALESCE(NULLIF(:rating_type, ''), 'DOUBLES'))
                      AND rating_date BETWEEN COALESCE(NULLIF(:start_date, ''), '1970-01-01')
                                          AND COALESCE(NULLIF(:end_date, ''), date('now'))
                ),
                ranked AS (
                    SELECT
                        scoped.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY player_dupr_id, rating_type
                            ORDER BY rating_date ASC, row_index ASC, rating_history_id ASC
                        ) AS rn_first,
                        ROW_NUMBER() OVER (
                            PARTITION BY player_dupr_id, rating_type
                            ORDER BY rating_date DESC, row_index DESC, rating_history_id DESC
                        ) AS rn_last
                    FROM scoped
                )
                SELECT
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    rating_type,
                    COUNT(*) AS points,
                    MAX(CASE WHEN rn_first = 1 THEN rating END) AS first_rating,
                    MAX(CASE WHEN rn_last = 1 THEN rating END) AS latest_rating,
                    (
                        MAX(CASE WHEN rn_last = 1 THEN rating END) -
                        MAX(CASE WHEN rn_first = 1 THEN rating END)
                    ) AS delta_rating,
                    MIN(rating_date) AS first_rating_date,
                    MAX(rating_date) AS latest_rating_date
                FROM ranked
                GROUP BY player_dupr_id, player_full_name, club_id, rating_type
            """,
        },
        "player_recent_form": {
            "title": "Player Recent Form",
            "description": "Recent match outcomes and win rate for a player (default last 90 days).",
            "hide_sql": True,
            "params": ["dupr_id", "days"],
            "sql": """
                WITH scoped AS (
                    SELECT *
                    FROM v_player_match_results
                    WHERE player_dupr_id = CAST(:dupr_id AS INTEGER)
                      AND match_date >= date(
                          'now',
                          printf('-%d day', COALESCE(CAST(NULLIF(:days, '') AS INTEGER), 90))
                      )
                )
                SELECT
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    COUNT(DISTINCT match_id) AS matches,
                    SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN is_winner THEN 0 ELSE 1 END) AS losses,
                    ROUND(
                        1.0 * SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) /
                        NULLIF(COUNT(DISTINCT match_id), 0),
                        4
                    ) AS win_rate,
                    MAX(match_date) AS last_match_date
                FROM scoped
                GROUP BY player_dupr_id, player_full_name, club_id
            """,
        },
        "player_partner_breakdown": {
            "title": "Player Partner Breakdown",
            "description": "How a player performs with each partner over a recent time window.",
            "hide_sql": True,
            "params": ["dupr_id", "days", "min_matches", "limit"],
            "sql": """
                WITH scoped AS (
                    SELECT *
                    FROM v_player_match_results
                    WHERE player_dupr_id = CAST(:dupr_id AS INTEGER)
                      AND match_date >= date(
                          'now',
                          printf('-%d day', COALESCE(CAST(NULLIF(:days, '') AS INTEGER), 90))
                      )
                ),
                pairs AS (
                    SELECT
                        s.player_dupr_id,
                        s.player_full_name,
                        s.club_id,
                        partner.dupr_id AS partner_dupr_id,
                        partner.full_name AS partner_full_name,
                        s.match_id,
                        s.match_date,
                        s.is_winner
                    FROM scoped s
                    JOIN match_team_player mtp_partner
                      ON mtp_partner.match_team_id = s.team_id
                     AND mtp_partner.player_id != s.player_id
                    JOIN player partner ON partner.id = mtp_partner.player_id
                )
                SELECT
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    partner_dupr_id,
                    partner_full_name,
                    COUNT(DISTINCT match_id) AS matches,
                    SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN is_winner THEN 0 ELSE 1 END) AS losses,
                    ROUND(
                        1.0 * SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) /
                        NULLIF(COUNT(DISTINCT match_id), 0),
                        4
                    ) AS win_rate,
                    MAX(match_date) AS last_match_date
                FROM pairs
                GROUP BY
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    partner_dupr_id,
                    partner_full_name
                HAVING COUNT(DISTINCT match_id) >= COALESCE(CAST(NULLIF(:min_matches, '') AS INTEGER), 1)
                ORDER BY matches DESC, win_rate DESC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 200)
            """,
        },
        "player_opponent_breakdown": {
            "title": "Player Opponent Breakdown",
            "description": "How a player performs against specific opponents over a recent time window.",
            "hide_sql": True,
            "params": ["dupr_id", "days", "min_matches", "limit"],
            "sql": """
                WITH scoped AS (
                    SELECT *
                    FROM v_player_match_results
                    WHERE player_dupr_id = CAST(:dupr_id AS INTEGER)
                      AND match_date >= date(
                          'now',
                          printf('-%d day', COALESCE(CAST(NULLIF(:days, '') AS INTEGER), 90))
                      )
                ),
                opponents AS (
                    SELECT
                        s.player_dupr_id,
                        s.player_full_name,
                        s.club_id,
                        opp.player_dupr_id AS opponent_dupr_id,
                        opp.player_full_name AS opponent_full_name,
                        s.match_id,
                        s.match_date,
                        s.is_winner
                    FROM scoped s
                    JOIN v_player_match_results opp
                      ON opp.match_db_id = s.match_db_id
                     AND opp.team_id != s.team_id
                )
                SELECT
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    opponent_dupr_id,
                    opponent_full_name,
                    COUNT(DISTINCT match_id) AS matches,
                    SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN is_winner THEN 0 ELSE 1 END) AS losses,
                    ROUND(
                        1.0 * SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) /
                        NULLIF(COUNT(DISTINCT match_id), 0),
                        4
                    ) AS win_rate,
                    MAX(match_date) AS last_match_date
                FROM opponents
                GROUP BY
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    opponent_dupr_id,
                    opponent_full_name
                HAVING COUNT(DISTINCT match_id) >= COALESCE(CAST(NULLIF(:min_matches, '') AS INTEGER), 1)
                ORDER BY matches DESC, win_rate DESC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 200)
            """,
        },
        "club_top_risers": {
            "title": "Club Top Risers",
            "description": "Players with the biggest rating increase over a recent window (default doubles, 90 days).",
            "hide_sql": True,
            "params": ["club_id", "days", "rating_type", "limit"],
            "sql": """
                WITH scoped AS (
                    SELECT *
                    FROM v_player_rating_points
                    WHERE rating_type = UPPER(COALESCE(NULLIF(:rating_type, ''), 'DOUBLES'))
                      AND rating_date >= date(
                          'now',
                          printf('-%d day', COALESCE(CAST(NULLIF(:days, '') AS INTEGER), 90))
                      )
                      AND (
                          NULLIF(:club_id, '') IS NULL OR
                          club_id = CAST(:club_id AS INTEGER)
                      )
                ),
                ranked AS (
                    SELECT
                        scoped.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY player_dupr_id, rating_type
                            ORDER BY rating_date ASC, row_index ASC, rating_history_id ASC
                        ) AS rn_first,
                        ROW_NUMBER() OVER (
                            PARTITION BY player_dupr_id, rating_type
                            ORDER BY rating_date DESC, row_index DESC, rating_history_id DESC
                        ) AS rn_last
                    FROM scoped
                ),
                summarized AS (
                    SELECT
                        player_dupr_id,
                        player_full_name,
                        club_id,
                        rating_type,
                        COUNT(*) AS points,
                        MAX(CASE WHEN rn_first = 1 THEN rating END) AS first_rating,
                        MAX(CASE WHEN rn_last = 1 THEN rating END) AS latest_rating,
                        (
                            MAX(CASE WHEN rn_last = 1 THEN rating END) -
                            MAX(CASE WHEN rn_first = 1 THEN rating END)
                        ) AS delta_rating,
                        MIN(rating_date) AS first_rating_date,
                        MAX(rating_date) AS latest_rating_date
                    FROM ranked
                    GROUP BY player_dupr_id, player_full_name, club_id, rating_type
                )
                SELECT *
                FROM summarized
                WHERE points >= 2
                ORDER BY delta_rating DESC, points DESC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 200)
            """,
        },
        "club_rating_snapshot": {
            "title": "Club Rating Snapshot",
            "description": "Club-level player counts and average singles/doubles ratings.",
            "hide_sql": True,
            "params": ["club_id", "limit"],
            "sql": """
                SELECT *
                FROM v_club_rating_snapshot
                WHERE (NULLIF(:club_id, '') IS NULL OR club_id = CAST(:club_id AS INTEGER))
                ORDER BY avg_doubles_rating DESC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 200)
            """,
        },
        "players_needing_more_data": {
            "title": "Players Needing More Data",
            "description": "Find players with sparse recent matches/rating points to target more activity.",
            "hide_sql": True,
            "params": ["days", "min_matches", "min_rating_points", "rating_type", "limit"],
            "sql": """
                WITH window AS (
                    SELECT COALESCE(CAST(NULLIF(:days, '') AS INTEGER), 90) AS days
                ),
                match_counts AS (
                    SELECT
                        pmr.player_dupr_id,
                        COUNT(DISTINCT pmr.match_id) AS matches_recent
                    FROM v_player_match_results pmr, window w
                    WHERE pmr.match_date >= date('now', printf('-%d day', w.days))
                    GROUP BY pmr.player_dupr_id
                ),
                rating_counts AS (
                    SELECT
                        vrp.player_dupr_id,
                        COUNT(*) AS rating_points_recent,
                        MAX(vrp.rating_date) AS last_rating_date
                    FROM v_player_rating_points vrp, window w
                    WHERE vrp.rating_type = UPPER(COALESCE(NULLIF(:rating_type, ''), 'DOUBLES'))
                      AND vrp.rating_date >= date('now', printf('-%d day', w.days))
                    GROUP BY vrp.player_dupr_id
                )
                SELECT
                    p.dupr_id AS player_dupr_id,
                    p.full_name AS player_full_name,
                    p.club_id,
                    COALESCE(mc.matches_recent, 0) AS matches_recent,
                    COALESCE(rc.rating_points_recent, 0) AS rating_points_recent,
                    rc.last_rating_date
                FROM player p
                LEFT JOIN match_counts mc ON mc.player_dupr_id = p.dupr_id
                LEFT JOIN rating_counts rc ON rc.player_dupr_id = p.dupr_id
                WHERE COALESCE(mc.matches_recent, 0) < COALESCE(CAST(NULLIF(:min_matches, '') AS INTEGER), 5)
                   OR COALESCE(rc.rating_points_recent, 0) < COALESCE(CAST(NULLIF(:min_rating_points, '') AS INTEGER), 5)
                ORDER BY matches_recent ASC, rating_points_recent ASC, p.full_name ASC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 200)
            """,
        },
    }

    return {
        "title": "DUPR Pickleball Analytics",
        "description": (
            "Question-driven local analytics for player trends, recent form, partner/opponent impact, and club movement."
        ),
        "plugins": {
            "datasette-vega": {
                "note": "Trend queries emit chart-friendly columns (rating_date, rating, rating_type)."
            }
        },
        "databases": {
            db_name: {
                "tables": {
                    "rating": {
                        "description": (
                            "Current player ratings with cached player identity columns for easier browsing."
                        )
                    },
                    "v_player_rating_points": {
                        "description": "Row-level rating history points joined to player identity."
                    },
                    "v_player_match_results": {
                        "description": "Row-level player match results for outcome and trend analysis."
                    },
                },
                "queries": queries,
            }
        },
    }
